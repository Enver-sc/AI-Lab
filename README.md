# Sustainable AI Gateway

Eine ausführliche Erklärung mit Architektur-, Ablauf-, Compliance-, Datenbank- und Sicherheitsdiagrammen befindet sich in der [technischen Dokumentation](docs/TECHNISCHE_DOKUMENTATION.md).

Lokales Flask-MVP zur Vorabanalyse von Prompts. Ollama liefert möglichst eine strukturierte lokale Analyse; lokale Regeln ergänzen Compliance-Funde, Token-, Kosten-, Energie-, CO₂- und Dauer-Schätzungen sowie eine nachvollziehbare Modellempfehlung. Energie/CO₂/Wasser/Ressourcenverbrauch werden, wo konfiguriert, über [EcoLogits](docs/ECOLOGITS_INTEGRATION.md) berechnet; ohne passende Konfiguration greift eine einfache Fallback-Formel. Zusätzlich zum Anbieterpreis ("Kosten", bei lokalen Modellen immer 0 €) wird eine unabhängige, geschätzte Stromkosten-Kennzahl aus dem geschätzten Energieverbrauch angezeigt (`ELECTRICITY_PRICE_EUR_PER_KWH`).

## Architektur

- `app/routes`: HTML- und JSON-API-Blueprints
- `app/services`: Analyse, Compliance, Schätzungen (inkl. EcoLogits-Anbindung), Verschlüsselung und SSRF-Schutz
- `app/providers`: Ollama und OpenAI-kompatible APIs hinter einer gemeinsamen Abstraktion
- `app/templates`, `app/static`: Jinja, Vanilla JavaScript und responsives CSS
- `app/models.py`: Provider und optionale, promptfreie Nutzungslogs
- `tests`: Unit- und Routentests mit gemockten externen Aufrufen

Analyse und Versand sind technisch getrennt. `/api/analyze` ruft keinen externen Provider auf. Versand verlangt eine bewusste Bestätigung im UI und wird bei roter Compliance ohne Begründung serverseitig blockiert.

## Installation

Voraussetzungen: Python 3.12 und optional Ollama.

```bash
python -m venv .venv
```

Linux/macOS: `source .venv/bin/activate`  
Windows: `.venv\Scripts\activate`

```bash
pip install -r requirements.txt
copy .env.example .env
```

Unter Linux/macOS: `cp .env.example .env`.

Fernet-Key erzeugen und als `APP_ENCRYPTION_KEY` ausschließlich in `.env` eintragen:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Ohne Key startet die Anwendung, speichert aber keine API-Schlüssel. Auch `SECRET_KEY` muss ersetzt werden.

## Ollama

```bash
ollama pull gemma4
ollama serve
```

`OLLAMA_MODEL`, `OLLAMA_BASE_URL` und `OLLAMA_TIMEOUT_SECONDS` steuern die Integration. `OLLAMA_ANALYSIS_TIMEOUT_SECONDS=0` lässt die lokale Dashboard-Analyse ohne Zeitlimit laufen; ein positiver Wert setzt stattdessen ein Limit in Sekunden. Ohne Ollama startet das Gateway weiterhin. `/api/ollama/status` meldet Status und Modelle.

## Start, Datenbank und Tests

SQLite und Tabellen werden beim ersten Start automatisch im `instance`-Verzeichnis angelegt.

```bash
flask --app app run --debug
pytest
```

Dashboard: <http://127.0.0.1:5000>, Provider: `/settings/providers`.

## Provider und Sicherheit

Unterstützt werden Ollama und generische OpenAI-kompatible APIs (`/models`, `/chat/completions`). Private, Loopback-, Link-local- und reservierte externe Ziele werden nach DNS-Auflösung blockiert; Redirects sind deaktiviert. Localhost ist nur für `ollama` erlaubt. Schlüssel liegen Fernet-verschlüsselt in SQLite und erscheinen in API/HTML nur maskiert. EU-Hosting ist vom Betreiber vertraglich zu verifizieren.

Prompts werden standardmäßig nicht gespeichert. `ENABLE_PROMPT_LOGGING=true` speichert nur SHA-256-Hash, Token-/Modell-/Schätzmetadaten und Status. CSRF-Schutz, Größenlimits, sichere Cookie-Vorgaben, CSP und Eingabevalidierung sind aktiv. Verändernde API-Aufrufe benötigen den Sessionwert als `X-CSRF-Token`.

## API

HTML: `GET /`, `/settings/providers`, `/privacy`. JSON: `POST /api/analyze`, `/api/optimize`, `/api/send`; Provider-CRUD samt Test/Modellen; Ollama-Status/Modelle und `/api/usage/summary`. `/api/analyze` liefert bei abweichendem Optimierungsvorschlag zusätzlich `optimized` (dieselben Kennzahlen für den optimierten Prompt); `/api/send` liefert die real gemessene `sustainability`.

## Einschränkungen

CO₂-, Energie-, Kosten- und Dauerwerte sind konfigurierbare Beispielschätzungen, keine wissenschaftliche Messung, Abrechnung oder Garantie. Die Compliance-Prüfung ist keine Rechtsberatung. DNS-Rebinding kann ein MVP nicht vollständig ausschließen. Streaming, OAuth und providerspezifische Abweichungen sind nicht enthalten. Externe Integrationen werden in Tests gemockt. Der CO₂-Vergleich zwischen Original- und optimiertem Prompt beruht auf einer zusätzlichen Annahme (nicht Teil von EcoLogits): dass ein kürzerer Prompt zu einer proportional kürzeren Antwort führt — EcoLogits' Formel selbst hängt nur von der erwarteten Ausgabelänge ab, nicht vom Prompt.
