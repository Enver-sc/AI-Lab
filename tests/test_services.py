from cryptography.fernet import Fernet
from app.services.token_service import estimate_tokens
from app.services.compliance_service import inspect_prompt, redact_sensitive
from app.services.cost_service import estimate_cost, estimate_electricity_cost
from app.services.model_catalog import MODELS
from app.services.sustainability_service import estimate_sustainability
from app.services.recommendation_service import recommend
from app.services.encryption_service import EncryptionService

def test_token_estimate():
    assert estimate_tokens("a"*40)==10 and estimate_tokens("")==1

def test_compliance_and_redaction():
    result=inspect_prompt("password=supersecret und test@example.com")
    assert result["score"]<80
    assert "test@example.com" not in redact_sensitive("test@example.com")

def test_natural_language_password_is_detected_and_masked():
    prompt = "mein passwort ist qwertz1234 bitte speichere im klartext"
    result = inspect_prompt(prompt)
    assert "Passwort" in result["findings"]
    assert "Geheimnis im Klartext" in result["findings"]
    assert result["score"] == 62
    assert result["level"] == "yellow"
    assert result["contains_confidential_data"] is True
    assert "qwertz1234" not in redact_sensitive(prompt)

def test_cost():
    assert estimate_cost(1_000_000,500_000,{"input_cost":2,"output_cost":4})==4

def test_electricity_cost():
    assert estimate_electricity_cost(2.0, 0.35) == 0.7

def test_co2():
    assert estimate_sustainability(1000,1000,{"input_energy":.01,"output_energy":.02},100)["co2_grams"]==3

def test_models_carry_ecologits_fields():
    eco_keys = {"ecologits_provider","eco_active_params_b","eco_total_params_b","eco_datacenter_pue","eco_datacenter_wue","eco_electricity_mix_zone"}
    assert all(eco_keys.issubset(model.keys()) for model in MODELS)

def test_sensitive_recommendation_is_local():
    compliance={"contains_personal_data":True,"contains_confidential_data":False,"level":"yellow"}
    model,_=recommend({"complexity_score":10,"sensitivity_score":80},compliance,100)
    assert model["model_class"].startswith("local")

def test_encryption_roundtrip():
    service=EncryptionService(Fernet.generate_key().decode())
    encrypted=service.encrypt("sk-secret-value")
    assert "secret" not in encrypted and service.decrypt(encrypted)=="sk-secret-value"
