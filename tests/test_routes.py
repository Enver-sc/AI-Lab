from unittest.mock import patch
from cryptography.fernet import Fernet
from app.extensions import db
from app.models import ProviderConfiguration, UsageLog
from app.services.encryption_service import EncryptionService

ANALYSIS_STUB = {"prompt_category":"x","complexity_score":1,"sensitivity_score":1,"compliance_score":100,"contains_personal_data":False,"contains_confidential_data":False,"copyright_risk":"low","recommended_model_class":"local_small","optimization_suggestions":[],"optimized_prompt":"x","short_reasoning":"x"}

def test_home_works_without_ollama(client):
    assert client.get("/").status_code==200

def test_javascript_has_executable_mime_type(client):
    response = client.get("/static/js/dashboard.js")
    assert response.status_code == 200
    assert response.mimetype == "application/javascript"
    assert response.headers["X-Content-Type-Options"] == "nosniff"

def test_analysis_never_calls_external_provider(client,csrf):
    analysis={"prompt_category":"x","complexity_score":1,"sensitivity_score":1,"compliance_score":100,"contains_personal_data":False,"contains_confidential_data":False,"copyright_risk":"low","recommended_model_class":"local_small","optimization_suggestions":[],"optimized_prompt":"x","short_reasoning":"x"}
    with patch("app.routes.api.OpenAICompatibleProvider.generate") as external, patch("app.routes.api.analyze_with_ollama",return_value=(analysis,None)):
        assert client.post("/api/analyze",json={"prompt":"Hallo"},headers={"X-CSRF-Token":csrf}).status_code==200
        external.assert_not_called()

def test_red_compliance_blocks_send(app,client,csrf):
    with app.app_context():
        db.session.add(ProviderConfiguration(name="Local",provider_type="ollama",base_url="http://localhost:11434",model_name="x",enabled=True))
        db.session.commit()
    prompt="password=verysecret sk-abcdefghijklmnop Bearer abcdefghijklmnopqrst -----BEGIN PRIVATE KEY-----"
    assert client.post("/api/send",json={"prompt":prompt,"provider_id":1},headers={"X-CSRF-Token":csrf}).status_code==403

def test_eu_button_only_with_eu_provider(app,client):
    assert b'id="send-eu" class="eu" disabled' in client.get("/").data
    with app.app_context():
        db.session.add(ProviderConfiguration(name="EU",provider_type="ollama",base_url="http://localhost",model_name="x",enabled=True,is_eu_hosted=True))
        db.session.commit()
    assert b'id="send-eu" class="eu" disabled' not in client.get("/").data

def test_api_key_not_exposed(app,client):
    key=Fernet.generate_key().decode()
    app.config["APP_ENCRYPTION_KEY"]=key
    with app.app_context():
        encrypted=EncryptionService(key).encrypt("sk-supersecret1234")
        db.session.add(ProviderConfiguration(name="X",provider_type="ollama",base_url="http://localhost",model_name="x",encrypted_api_key=encrypted))
        db.session.commit()
    body=client.get("/api/providers").get_data(as_text=True)
    assert "supersecret" not in body and "encrypted_api_key" not in body

def test_analyze_falls_back_when_ecologits_disabled(app,client,csrf):
    app.config["ECOLOGITS_ENABLED"] = False
    with patch("app.routes.api.analyze_with_ollama", return_value=(ANALYSIS_STUB, None)):
        response = client.post("/api/analyze", json={"prompt": "Hallo Welt"}, headers={"X-CSRF-Token": csrf})
    assert response.status_code == 200
    sustainability = response.get_json()["sustainability"]
    assert sustainability["co2_grams"] >= 0 and sustainability["energy_kwh"] >= 0

def test_electricity_cost_shown_for_local_recommendation(client, csrf):
    with patch("app.routes.api.analyze_with_ollama", return_value=(ANALYSIS_STUB, None)):
        response = client.post("/api/analyze", json={"prompt": "Hallo Welt"}, headers={"X-CSRF-Token": csrf})
    data = response.get_json()
    assert data["recommendation"]["hosting_region"] == "Lokal"
    assert data["sustainability"]["electricity_cost_eur"] is not None

def test_electricity_cost_hidden_for_cloud_recommendation(client, csrf):
    with patch("app.routes.api.analyze_with_ollama", return_value=(ANALYSIS_STUB, None)):
        response = client.post("/api/analyze", json={"prompt": "Hallo Welt", "mode": "cloud"}, headers={"X-CSRF-Token": csrf})
    data = response.get_json()
    assert data["recommendation"]["hosting_region"] != "Lokal"
    assert data["sustainability"]["electricity_cost_eur"] is None

def test_analyze_returns_optimized_comparison_when_prompt_differs(client, csrf):
    analysis = {**ANALYSIS_STUB, "optimized_prompt": "Kurz."}
    long_prompt = "Bitte erledige diese Aufgabe fuer mich und beschreibe dabei jeden einzelnen Schritt sehr ausfuehrlich. " * 4
    with patch("app.routes.api.analyze_with_ollama", return_value=(analysis, None)):
        response = client.post("/api/analyze", json={"prompt": long_prompt}, headers={"X-CSRF-Token": csrf})
    data = response.get_json()
    assert "optimized" in data
    assert data["optimized"]["prompt_tokens"] < data["input_tokens"]
    assert data["optimized"]["sustainability"]["co2_grams"] <= data["sustainability"]["co2_grams"]

def test_analyze_omits_optimized_when_prompt_unchanged(client, csrf):
    prompt = "Ein kurzer Prompt."
    analysis = {**ANALYSIS_STUB, "optimized_prompt": prompt}
    with patch("app.routes.api.analyze_with_ollama", return_value=(analysis, None)):
        response = client.post("/api/analyze", json={"prompt": prompt}, headers={"X-CSRF-Token": csrf})
    assert "optimized" not in response.get_json()

def test_send_populates_estimated_co2_grams(app, client, csrf):
    app.config["ENABLE_PROMPT_LOGGING"] = True
    with app.app_context():
        db.session.add(ProviderConfiguration(name="Local", provider_type="ollama", base_url="http://localhost:11434", model_name="x", enabled=True, eco_active_params_b=8, eco_total_params_b=8))
        db.session.commit()
    with patch("app.routes.api.OllamaProvider.generate", return_value="Eine Antwort."):
        response = client.post("/api/send", json={"prompt": "Hallo", "provider_id": 1}, headers={"X-CSRF-Token": csrf})
    assert response.status_code == 200
    data = response.get_json()
    assert data["sustainability"]["co2_grams"] > 0
    with app.app_context():
        log = UsageLog.query.first()
        assert log.estimated_co2_grams > 0

def test_send_co2_zero_when_ecologits_unavailable(app, client, csrf):
    app.config["ENABLE_PROMPT_LOGGING"] = True
    app.config["ECOLOGITS_ENABLED"] = False
    with app.app_context():
        db.session.add(ProviderConfiguration(name="Local", provider_type="ollama", base_url="http://localhost:11434", model_name="x", enabled=True))
        db.session.commit()
    with patch("app.routes.api.OllamaProvider.generate", return_value="Eine Antwort."):
        response = client.post("/api/send", json={"prompt": "Hallo", "provider_id": 1}, headers={"X-CSRF-Token": csrf})
    assert response.get_json()["sustainability"] is None
    with app.app_context():
        log = UsageLog.query.first()
        assert log.estimated_co2_grams == 0
