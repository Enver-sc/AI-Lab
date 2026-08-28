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
    # Wie OLLAMA_GUARDIAN_KEEP_ALIVE: Analyse-Aufrufe folgen in einer Sitzung dicht
    # aufeinander; 30 Minuten statt Ollama-Default 5m vermeiden Kaltstarts dazwischen.
    OLLAMA_ANALYSIS_KEEP_ALIVE = os.getenv("OLLAMA_ANALYSIS_KEEP_ALIVE", "30m")
    # Leerer Wert deaktiviert die semantische Stufe-2-Prüfung.
    OLLAMA_GUARDIAN_MODEL = os.getenv("OLLAMA_GUARDIAN_MODEL", "granite4.1-guardian:8b")
    # Eigenes, grosszuegiges Zeitlimit statt OLLAMA_TIMEOUT_SECONDS: ein kalt startendes
    # 8B-Guardian-Modell braucht beim ersten Aufruf spuerbar laenger zum Laden als ein
    # bereits im Speicher gehaltenes Modell; ohne Limit blockiert der Request sonst
    # minutenlang die App, mit zu knappem Limit wuerde jeder Kaltstart faelschlich in
    # den degradierten Zustand fallen.
    OLLAMA_GUARDIAN_TIMEOUT_SECONDS = float(os.getenv("OLLAMA_GUARDIAN_TIMEOUT_SECONDS", "120"))
    # Haelt das Guardian-Modell nach einem Aufruf laenger im Speicher (Ollama-Default
    # waere 5m) -- Stufe-2-Pruefungen kommen innerhalb einer Arbeitssitzung wiederholt
    # vor; 30 Minuten vermeiden wiederholte Kaltstarts, ohne das Modell dauerhaft zu binden.
    OLLAMA_GUARDIAN_KEEP_ALIVE = os.getenv("OLLAMA_GUARDIAN_KEEP_ALIVE", "30m")
    APP_ENCRYPTION_KEY = os.getenv("APP_ENCRYPTION_KEY", "")
    ENABLE_PROMPT_LOGGING = as_bool(os.getenv("ENABLE_PROMPT_LOGGING", "false"))
    MAX_PROMPT_LENGTH = int(os.getenv("MAX_PROMPT_LENGTH", "30000"))
    # Ersetzt den frueheren festen DEFAULT_EXPECTED_OUTPUT_TOKENS-Wert: die erwartete Ausgabelaenge
    # skaliert jetzt mit der Eingabelaenge, siehe CARBON_FOOTPRINT_REDESIGN.md. Platzhalterwert,
    # noch nicht aus echten Nutzungsdaten kalibriert.
    EXPECTED_OUTPUT_RATIO = float(os.getenv("EXPECTED_OUTPUT_RATIO", "6"))
    CARBON_INTENSITY_G_PER_KWH = float(os.getenv("CARBON_INTENSITY_G_PER_KWH", "350"))
    # Bewusst kein Default: ohne bekannte CPU-TDP bleibt die lokale Energie-/CO2-Schaetzung
    # fuer Ollama-Sends "nicht verfuegbar", statt einen erfundenen Wert anzuzeigen.
    LOCAL_CPU_TDP_WATT = float(os.getenv("LOCAL_CPU_TDP_WATT")) if os.getenv("LOCAL_CPU_TDP_WATT") else None
    ECOLOGITS_ENABLED = as_bool(os.getenv("ECOLOGITS_ENABLED", "true"))
    ECOLOGITS_ELECTRICITY_MIX_ZONE = os.getenv("ECOLOGITS_ELECTRICITY_MIX_ZONE", "DEU")
    ECOLOGITS_DEFAULT_DATACENTER_PUE = float(os.getenv("ECOLOGITS_DEFAULT_DATACENTER_PUE", "1.2"))
    ECOLOGITS_DEFAULT_DATACENTER_WUE = float(os.getenv("ECOLOGITS_DEFAULT_DATACENTER_WUE", "1.8"))
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = as_bool(os.getenv("SESSION_COOKIE_SECURE", "false"))
    MAX_CONTENT_LENGTH = 1_000_000
