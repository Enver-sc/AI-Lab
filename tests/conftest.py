import pytest
from app import create_app

class TestConfig:
    TESTING=True
    SECRET_KEY="test"
    SQLALCHEMY_DATABASE_URI="sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS=False
    OLLAMA_BASE_URL="http://localhost:11434"
    OLLAMA_MODEL="test"
    OLLAMA_TIMEOUT_SECONDS=.1
    OLLAMA_ANALYSIS_TIMEOUT_SECONDS=.1
    # Stufe 2 in Tests standardmäßig aus: keine echten Netzwerkaufrufe;
    # Guardian-Tests setzen ein Modell und mocken den Ollama-Aufruf.
    OLLAMA_GUARDIAN_MODEL=""
    APP_ENCRYPTION_KEY=""
    ENABLE_PROMPT_LOGGING=False
    MAX_PROMPT_LENGTH=1000
    EXPECTED_OUTPUT_RATIO=6
    CARBON_INTENSITY_G_PER_KWH=350
    LOCAL_CPU_TDP_WATT=None
    ECOLOGITS_ENABLED=True
    ECOLOGITS_ELECTRICITY_MIX_ZONE="DEU"
    ECOLOGITS_DEFAULT_DATACENTER_PUE=1.2
    ECOLOGITS_DEFAULT_DATACENTER_WUE=1.8
    SESSION_COOKIE_HTTPONLY=True
    SESSION_COOKIE_SAMESITE="Lax"
    SESSION_COOKIE_SECURE=False
    MAX_CONTENT_LENGTH=100000

@pytest.fixture
def app():
    return create_app(TestConfig)

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def csrf(client):
    client.get("/")
    with client.session_transaction() as session:
        return session["csrf_token"]
