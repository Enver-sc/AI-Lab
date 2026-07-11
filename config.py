import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

def as_bool(value):
    return str(value).lower() in {"1", "true", "yes", "on"}

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "development-only-change-me")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'instance' / 'gateway.db'}")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma4")
    OLLAMA_TIMEOUT_SECONDS = float(os.getenv("OLLAMA_TIMEOUT_SECONDS", "60"))
    OLLAMA_ANALYSIS_TIMEOUT_SECONDS = float(os.getenv("OLLAMA_ANALYSIS_TIMEOUT_SECONDS", "0"))
    APP_ENCRYPTION_KEY = os.getenv("APP_ENCRYPTION_KEY", "")
    ENABLE_PROMPT_LOGGING = as_bool(os.getenv("ENABLE_PROMPT_LOGGING", "false"))
    MAX_PROMPT_LENGTH = int(os.getenv("MAX_PROMPT_LENGTH", "30000"))
    DEFAULT_EXPECTED_OUTPUT_TOKENS = int(os.getenv("DEFAULT_EXPECTED_OUTPUT_TOKENS", "500"))
    CARBON_INTENSITY_G_PER_KWH = float(os.getenv("CARBON_INTENSITY_G_PER_KWH", "350"))
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = as_bool(os.getenv("SESSION_COOKIE_SECURE", "false"))
    MAX_CONTENT_LENGTH = 1_000_000
