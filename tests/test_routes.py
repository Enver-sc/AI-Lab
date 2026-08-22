from unittest.mock import patch
from cryptography.fernet import Fernet
from app.extensions import db
from app.models import ProviderConfiguration, UsageLog
from app.services.encryption_service import EncryptionService

ANALYSIS_STUB = {"prompt_category":"x","complexity_score":1,"sensitivity_score":1,"compliance_score":100,"contains_personal_data":False,"contains_confidential_data":False,"copyright_risk":"low","recommended_model_class":"local_small","optimization_suggestions":[],"optimized_prompt":"x","short_reasoning":"x"}

def test_home_works_without_ollama(client):
    assert client.get("/").status_code==200

def test_info_page_shows_version(app, client):
    response = client.get("/info")
    assert response.status_code == 200
    assert app.config["APP_VERSION"].encode() in response.data

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
    assert sustainability["co2_grams"] >= 0 and sustainability["energy_wh"] >= 0

def test_expected_output_tokens_scales_with_prompt_length(client, csrf):
    short_prompt = "Was ist Entropie?"
    long_prompt = "Erklaere ausfuehrlich und mit vielen Beispielen: " + "Entropie " * 50
    with patch("app.routes.api.analyze_with_ollama", return_value=(ANALYSIS_STUB, None)):
        short_data = client.post("/api/analyze", json={"prompt": short_prompt}, headers={"X-CSRF-Token": csrf}).get_json()
        long_data = client.post("/api/analyze", json={"prompt": long_prompt}, headers={"X-CSRF-Token": csrf}).get_json()
    assert long_data["expected_output_tokens"] > short_data["expected_output_tokens"]
    assert long_data["sustainability"]["co2_grams"] > short_data["sustainability"]["co2_grams"]

def test_estimate_footprint_scales_with_text_length(client, csrf):
    short_text = "Was ist Entropie?"
    long_text = "Erklaere ausfuehrlich und mit vielen Beispielen: " + "Entropie " * 50
    short_data = client.post("/api/estimate-footprint", json={"text": short_text, "model_class": "local_small"}, headers={"X-CSRF-Token": csrf}).get_json()
    long_data = client.post("/api/estimate-footprint", json={"text": long_text, "model_class": "local_small"}, headers={"X-CSRF-Token": csrf}).get_json()
    assert long_data["expected_output_tokens"] > short_data["expected_output_tokens"]
    assert long_data["sustainability"]["co2_grams"] > short_data["sustainability"]["co2_grams"]

def test_estimate_footprint_rejects_unknown_model_class(client, csrf):
    response = client.post("/api/estimate-footprint", json={"text": "Hallo", "model_class": "does-not-exist"}, headers={"X-CSRF-Token": csrf})
    assert response.status_code == 400

def test_estimate_footprint_requires_no_ollama_call(client, csrf):
    with patch("app.routes.api.analyze_with_ollama") as ollama_call:
        response = client.post("/api/estimate-footprint", json={"text": "Hallo", "model_class": "cloud_small"}, headers={"X-CSRF-Token": csrf})
        ollama_call.assert_not_called()
    assert response.status_code == 200

def test_estimate_footprint_for_active_provider_returns_sustainability(app, client, csrf):
    with app.app_context():
        db.session.add(ProviderConfiguration(name="Anthropic", provider_type="anthropic", base_url="https://api.anthropic.com", model_name="claude-haiku-4-5-20251001", ecologits_provider="anthropic", enabled=True))
        db.session.commit()
    response = client.post("/api/estimate-footprint", json={"text": "Was ist Entropie?", "provider_id": 1, "model_name": "claude-haiku-4-5-20251001"}, headers={"X-CSRF-Token": csrf})
    data = response.get_json()
    assert response.status_code == 200
    assert data["sustainability"]["mode"] == "llm_impacts"

def test_estimate_footprint_falls_back_to_formula_for_incomplete_provider_eco_config(app, client, csrf):
    # Regression: ein echter Ollama-Provider mit nur teilweise gepflegten EcoLogits-Parametern
    # (z. B. nur Gesamt-, keine Aktivparameter) liess die Kacheln zuvor auf "nicht verfuegbar"
    # zurueckfallen, obwohl /api/analyze kurz zuvor ueber den Katalogeintrag Werte gezeigt hatte.
    with app.app_context():
        db.session.add(ProviderConfiguration(name="Local", provider_type="ollama", base_url="http://localhost:11434", model_name="x", enabled=True, eco_total_params_b=2))
        db.session.commit()
    response = client.post("/api/estimate-footprint", json={"text": "Was ist ein Gnu?", "provider_id": 1, "model_class": "local_small"}, headers={"X-CSRF-Token": csrf})
    data = response.get_json()
    assert response.status_code == 200
    assert data["sustainability"] is not None
    assert data["sustainability"]["mode"] == "formula"
    assert data["sustainability"]["co2_grams"] > 0

def test_estimate_footprint_prefers_ecologits_over_formula_fallback(app, client, csrf):
    with app.app_context():
        db.session.add(ProviderConfiguration(name="Anthropic", provider_type="anthropic", base_url="https://api.anthropic.com", model_name="claude-haiku-4-5-20251001", ecologits_provider="anthropic", enabled=True))
        db.session.commit()
    response = client.post("/api/estimate-footprint", json={"text": "Was ist Entropie?", "provider_id": 1, "model_name": "claude-haiku-4-5-20251001", "model_class": "cloud_small"}, headers={"X-CSRF-Token": csrf})
    data = response.get_json()
    assert data["sustainability"]["mode"] == "llm_impacts"
    assert data["sustainability"]["water_ml"] is not None

def test_estimate_footprint_rejects_unknown_provider(client, csrf):
    response = client.post("/api/estimate-footprint", json={"text": "Hallo", "provider_id": 999}, headers={"X-CSRF-Token": csrf})
    assert response.status_code == 400

def test_simple_prompt_recommends_claude_haiku(client, csrf):
    analysis = {**ANALYSIS_STUB, "recommended_model_class": "cloud_small"}
    with patch("app.routes.api.analyze_with_ollama", return_value=(analysis, None)):
        response = client.post(
            "/api/analyze",
            json={"prompt": "Fasse diesen kurzen Satz zusammen."},
            headers={"X-CSRF-Token": csrf},
        )
    data = response.get_json()
    assert data["recommendation"]["model_id"] == "claude-haiku-4-5-20251001"
    assert data["recommendation"]["input_cost"] == 1
    assert data["recommendation"]["output_cost"] == 5


def test_complex_prompt_recommends_claude_sonnet(client, csrf):
    analysis = {
        **ANALYSIS_STUB,
        "complexity_score": 90,
        "recommended_model_class": "cloud_large",
    }
    with patch("app.routes.api.analyze_with_ollama", return_value=(analysis, None)):
        response = client.post(
            "/api/analyze",
            json={"prompt": "Analysiere eine komplexe Softwarearchitektur."},
            headers={"X-CSRF-Token": csrf},
        )
    data = response.get_json()
    assert data["recommendation"]["model_id"] == "claude-sonnet-4-6"
    assert data["recommendation"]["input_cost"] == 3
    assert data["recommendation"]["output_cost"] == 15


def test_one_anthropic_provider_can_send_with_both_models(app, client, csrf):
    key = Fernet.generate_key().decode()
    app.config["APP_ENCRYPTION_KEY"] = key
    with app.app_context():
        encrypted = EncryptionService(key).encrypt("sk-ant-test")
        db.session.add(
            ProviderConfiguration(
                name="Anthropic",
                provider_type="anthropic",
                base_url="https://api.anthropic.com",
                encrypted_api_key=encrypted,
                model_name="claude-haiku-4-5-20251001",
                enabled=True,
            )
        )
        db.session.commit()

    with patch(
        "app.routes.api.AnthropicProvider.generate_messages",
        return_value=("Antwort", {"input_tokens": 120, "output_tokens": 40}),
    ) as generate:
        response = client.post(
            "/api/send",
            json={
                "prompt": "Komplexe Aufgabe",
                "provider_id": 1,
                "model_name": "claude-sonnet-4-6",
            },
            headers={"X-CSRF-Token": csrf},
        )

    assert response.status_code == 200
    generate.assert_called_once_with(
        [{"role": "user", "content": "Komplexe Aufgabe"}],
        "claude-sonnet-4-6",
    )
    assert response.get_json()["cost_currency"] == "USD"
    assert response.get_json()["model_used"] == "claude-sonnet-4-6"
    assert response.get_json()["input_tokens"] == 120
    assert response.get_json()["output_tokens"] == 40


def test_anthropic_follow_up_sends_complete_chat(app, client, csrf):
    key = Fernet.generate_key().decode()
    app.config["APP_ENCRYPTION_KEY"] = key
    with app.app_context():
        db.session.add(
            ProviderConfiguration(
                name="Anthropic",
                provider_type="anthropic",
                base_url="https://api.anthropic.com",
                encrypted_api_key=EncryptionService(key).encrypt("sk-ant-test"),
                model_name="claude-haiku-4-5-20251001",
                enabled=True,
            )
        )
        db.session.commit()
    messages = [
        {"role": "user", "content": "Hallo"},
        {"role": "assistant", "content": "Guten Tag"},
        {"role": "user", "content": "Wie geht es weiter?"},
    ]
    with patch(
        "app.routes.api.AnthropicProvider.generate_messages",
        return_value=("So geht es weiter.", {"input_tokens": 50, "output_tokens": 20}),
    ) as generate:
        response = client.post(
            "/api/send",
            json={
                "prompt": "Wie geht es weiter?",
                "messages": messages,
                "provider_id": 1,
                "model_name": "claude-haiku-4-5-20251001",
            },
            headers={"X-CSRF-Token": csrf},
        )
    assert response.status_code == 200
    generate.assert_called_once_with(messages, "claude-haiku-4-5-20251001")
    data = response.get_json()
    assert data["actual_cost"] == 0.00015
    assert data["input_cost"] == 0.00005
    assert data["output_cost"] == 0.0001


def test_chat_may_exceed_single_prompt_limit(app, client, csrf):
    key = Fernet.generate_key().decode()
    app.config["APP_ENCRYPTION_KEY"] = key
    with app.app_context():
        db.session.add(
            ProviderConfiguration(
                name="Anthropic",
                provider_type="anthropic",
                base_url="https://api.anthropic.com",
                encrypted_api_key=EncryptionService(key).encrypt("sk-ant-test"),
                model_name="claude-haiku-4-5-20251001",
                enabled=True,
            )
        )
        db.session.commit()
    messages = [
        {"role": "user", "content": "Erste Frage"},
        {"role": "assistant", "content": "A" * 1500},
        {"role": "user", "content": "Folgefrage"},
    ]
    with patch(
        "app.routes.api.AnthropicProvider.generate_messages",
        return_value=("Antwort", {"input_tokens": 400, "output_tokens": 10}),
    ):
        response = client.post(
            "/api/send",
            json={
                "prompt": "Folgefrage",
                "messages": messages,
                "provider_id": 1,
                "model_name": "claude-haiku-4-5-20251001",
            },
            headers={"X-CSRF-Token": csrf},
        )
    assert response.status_code == 200


def test_anthropic_rejects_unknown_model(app, client, csrf):
    with app.app_context():
        db.session.add(
            ProviderConfiguration(
                name="Anthropic",
                provider_type="anthropic",
                base_url="https://api.anthropic.com",
                model_name="claude-haiku-4-5-20251001",
                enabled=True,
            )
        )
        db.session.commit()

    response = client.post(
        "/api/send",
        json={"prompt": "Hallo", "provider_id": 1, "model_name": "anderes-modell"},
        headers={"X-CSRF-Token": csrf},
    )
    assert response.status_code == 400

def test_analyze_never_returns_optimized_comparison(client, csrf):
    # CARBON_FOOTPRINT_REDESIGN.md: der CO2-Vergleich original vs. optimierter Prompt wurde entfernt
    # (strukturell fast immer negativ, da Ollamas Optimierung auf Klarheit statt Kuerze zielt). Der
    # reine Formulierungsvorschlag bleibt aber erhalten.
    analysis = {**ANALYSIS_STUB, "optimized_prompt": "Kurz."}
    long_prompt = "Bitte erledige diese Aufgabe fuer mich und beschreibe dabei jeden einzelnen Schritt sehr ausfuehrlich. " * 4
    with patch("app.routes.api.analyze_with_ollama", return_value=(analysis, None)):
        response = client.post("/api/analyze", json={"prompt": long_prompt}, headers={"X-CSRF-Token": csrf})
    data = response.get_json()
    assert "optimized" not in data
    assert data["analysis"]["optimized_prompt"] == "Kurz."

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

def test_send_falls_back_to_local_cpu_estimate_without_manual_ecologits_params(app, client, csrf):
    # Ollama-Modell ohne eco_active_params_b/eco_total_params_b (Regelfall) -- EcoLogits liefert
    # kein Ergebnis, die lokale TDP-Formel-Schaetzung (siehe local_energy_service.py) greift.
    app.config["LOCAL_CPU_TDP_WATT"] = 15
    with app.app_context():
        db.session.add(ProviderConfiguration(name="Local", provider_type="ollama", base_url="http://localhost:11434", model_name="x", enabled=True))
        db.session.commit()
    with patch("app.routes.api.OllamaProvider.generate", return_value="Eine Antwort."), \
         patch("app.routes.api.measure_local_generation", return_value=("Eine Antwort.", {"energy_wh": 0.05, "co2_grams": 0.0175, "mode": "local_cpu_estimate"}, None)):
        response = client.post("/api/send", json={"prompt": "Hallo", "provider_id": 1}, headers={"X-CSRF-Token": csrf})
    data = response.get_json()
    assert data["sustainability"]["mode"] == "local_cpu_estimate"
    assert data["sustainability"]["co2_grams"] == 0.0175
    assert data["sustainability"].get("water_ml") is None

def test_send_reports_warning_when_local_tdp_not_configured(app, client, csrf):
    with app.app_context():
        db.session.add(ProviderConfiguration(name="Local", provider_type="ollama", base_url="http://localhost:11434", model_name="x", enabled=True))
        db.session.commit()
    with patch("app.routes.api.OllamaProvider.generate", return_value="Eine Antwort."):
        response = client.post("/api/send", json={"prompt": "Hallo", "provider_id": 1}, headers={"X-CSRF-Token": csrf})
    data = response.get_json()
    assert data["sustainability"] is None
    assert "LOCAL_CPU_TDP_WATT" in data["sustainability_warning"]

def test_send_prefers_ecologits_manual_params_over_local_estimate(app, client, csrf):
    # Sind fuer das Ollama-Modell manuelle EcoLogits-Parameter hinterlegt, hat der vollstaendigere
    # EcoLogits-Wert (inkl. Wasser/ADPe) Vorrang vor der TDP-Formel-Schaetzung.
    app.config["LOCAL_CPU_TDP_WATT"] = 15
    with app.app_context():
        db.session.add(ProviderConfiguration(name="Local", provider_type="ollama", base_url="http://localhost:11434", model_name="x", enabled=True, eco_active_params_b=8, eco_total_params_b=8))
        db.session.commit()
    with patch("app.routes.api.OllamaProvider.generate", return_value="Eine Antwort."):
        response = client.post("/api/send", json={"prompt": "Hallo", "provider_id": 1}, headers={"X-CSRF-Token": csrf})
    data = response.get_json()
    assert data["sustainability"]["mode"] == "compute_llm_impacts"
    assert data["sustainability"]["water_ml"] is not None
