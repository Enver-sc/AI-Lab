# Sustainable AI Gateway

Eine ausführliche Erklärung mit Architektur-, Ablauf-, Compliance-, Datenbank- und Sicherheitsdiagrammen befindet sich in der [technischen Dokumentation](docs/TECHNISCHE_DOKUMENTATION.md).

Lokales Flask-MVP zur Vorabanalyse von Prompts. Ollama liefert möglichst eine strukturierte lokale Analyse; lokale Regeln ergänzen Compliance-Funde, Token-, Kosten-, Energie-, CO₂- und Dauer-Schätzungen sowie eine nachvollziehbare Modellempfehlung. Energie/CO₂/Wasser/Ressourcenverbrauch werden, wo konfiguriert, über [EcoLogits](docs/ECOLOGITS_INTEGRATION.md) berechnet; für den tatsächlichen Versand an einen lokalen Ollama-Provider ohne passende EcoLogits-Konfiguration greift ersatzweise eine eigene CPU-Auslastungsformel (`LOCAL_CPU_TDP_WATT`), sonst eine einfache Fallback-Formel. Die Weiterentwicklung dieser Schätzlogik (Live-Versand-Schätzung `/api/estimate-footprint`, bildhafte Darstellung, EcoLogits-Fallback-Stufen) ist in [`CARBON_FOOTPRINT_REDESIGN.md`](docs/CARBON_FOOTPRINT_REDESIGN.md) dokumentiert — eine zwischenzeitlich geprüfte CodeCarbon-Integration wurde dort zugunsten der eigenen Formel wieder verworfen.

## Architektur

- `app/routes`: HTML- und JSON-API-Blueprints
- `app/services`: Analyse, Compliance, Schätzungen (inkl. EcoLogits-Anbindung), Verschlüsselung und SSRF-Schutz
- `app/providers`: Ollama und OpenAI-kompatible APIs hinter einer gemeinsamen Abstraktion
- `app/templates`, `app/static`: Jinja, Vanilla JavaScript und responsives CSS
- `app/models.py`: Provider und optionale, promptfreie Nutzungslogs
- `tests`: Unit- und Routentests mit gemockten externen Aufrufen

Analyse und Versand sind technisch getrennt. `/api/analyze` ruft keinen externen Provider auf. Versand verlangt eine bewusste Bestätigung im UI und wird bei roter Compliance ohne Begründung serverseitig blockiert. Bei Chat-Anfragen prüft der Server jede Nachricht des mitgeschickten Verlaufs; das Gesamtergebnis richtet sich nach der schlechtesten Nachricht, und jede rote Nachricht braucht eine eigene, frische Begründung — auch Folgenachrichten im Chat durchlaufen im UI die bewusste Bestätigung.

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

`OLLAMA_MODEL`, `OLLAMA_BASE_URL` und `OLLAMA_TIMEOUT_SECONDS` steuern die Integration. `OLLAMA_ANALYSIS_TIMEOUT_SECONDS=0` lässt die lokale Dashboard-Analyse ohne Zeitlimit laufen; ein positiver Wert setzt stattdessen ein Limit in Sekunden. Ohne Ollama startet das Gateway weiterhin. `/api/ollama/status` meldet Status und Modelle. `LOCAL_CPU_TDP_WATT` (optional, leer = deaktiviert) aktiviert eine grobe CPU-Auslastungsformel für Energie/CO₂ bei lokalen Ollama-Sends, wenn EcoLogits dafür keinen Wert liefert.

## Start, Datenbank und Tests

SQLite und Tabellen werden beim ersten Start automatisch im `instance`-Verzeichnis angelegt. Die Datei `instance/gateway.db` ist deshalb nicht versioniert, sondern entsteht beim ersten Start lokal.

```bash
flask --app app run --debug
pytest
flask calibrate-ratio
```

Dashboard: <http://127.0.0.1:5000>, Provider: `/settings/providers`. `flask calibrate-ratio` schlägt einen kalibrierten `EXPECTED_OUTPUT_RATIO`-Wert aus echten `UsageLog`-Daten vor (Mindeststichprobe 20 erfolgreiche Sends, `ENABLE_PROMPT_LOGGING=true` nötig); ändert nichts automatisch, die Übernahme in `.env` bleibt manuell.

## Provider und Sicherheit

Unterstützt werden Ollama, die native Anthropic Messages API und generische OpenAI-kompatible APIs (`/models`, `/chat/completions`). Claude Haiku 4.5 (`claude-haiku-4-5-20251001`, 1 USD Input/5 USD Output je Mio. Token) ist für einfache Anfragen hinterlegt; Claude Sonnet 4.6 (`claude-sonnet-4-6`, 3 USD/15 USD) für komplexe Aufgaben. Cache- und Batchpreise werden nicht verwendet. Private, Loopback-, Link-local- und reservierte externe Ziele werden nach DNS-Auflösung blockiert; Redirects sind deaktiviert. Localhost ist nur für `ollama` erlaubt. Schlüssel liegen Fernet-verschlüsselt in SQLite und erscheinen in API/HTML nur maskiert. EU-Hosting ist vom Betreiber vertraglich zu verifizieren.

Den Anthropic API-Key einmal unter `/settings/providers` eintragen. Dazu einen Provider vom Typ `Anthropic Claude` mit Base-URL `https://api.anthropic.com` anlegen. Nach der lokalen Prompt-Analyse empfiehlt das Dashboard Haiku oder Sonnet; der Nutzer kann direkt vor dem Versand trotzdem eines der beiden Modelle auswählen. Nach der ersten API-Antwort kann der Chat im Dashboard fortgesetzt werden. Der Verlauf bleibt im Browser und wird für Folgefragen als Kontext übertragen; pro Runde zeigt das Dashboard die von Anthropic gemeldeten Input-/Output-Tokens, deren Kosten, Gesamtkosten und kumulierte Umweltwerte.

Prompts werden standardmäßig nicht gespeichert. `ENABLE_PROMPT_LOGGING=true` speichert nur SHA-256-Hash, Token-/Modell-/Schätzmetadaten und Status. CSRF-Schutz, Größenlimits, sichere Cookie-Vorgaben, CSP und Eingabevalidierung sind aktiv. Verändernde API-Aufrufe benötigen den Sessionwert als `X-CSRF-Token`.

## Compliance Stufe 2 (semantische Prüfung)

Stufe 1 prüft deterministisch mit Mustern und Prüfsummen (IBAN, Kreditkarte, Schlüssel u. a.). Stufe 2 ergänzt eine semantische Prüfung über ein lokales Guardian-Modell (Ollama): Sie erkennt Datenschutzrisiken im Sinne von DSGVO und KDG auch ohne prüfbare Muster — etwa „Person A aus Abteilung X ist heute krank" (identifizierbare Person plus Gesundheitsbezug). Funde heben die Ampel mindestens auf Gelb und erscheinen als eigene Stufe-2-Flags (`semantic_findings`) mit kurzer Begründung; Rot und das serverseitige Blockieren bleiben allein Sache der deterministischen Stufe 1. Stufe 2 läuft bei der Analyse (`/api/analyze`) und bei der Verlaufsprüfung (`/api/send`, `/api/compliance/check`). Von Stufe 1 erkannte sensible Werte werden — wie bei der Analyse — vor der Übergabe an das Guardian-Modell maskiert.

Konfiguration: `OLLAMA_GUARDIAN_MODEL` bestimmt das Modell (Standard `granite4.1-guardian:8b`, Bezug z. B. per `ollama pull granite4.1-guardian:8b`); ein leerer Wert deaktiviert Stufe 2. Ist das Modell nicht erreichbar oder liefert es keine verwertbare Antwort, läuft alles mit Stufe 1 weiter, und das Ergebnis enthält statt eines Fehlers einen sichtbaren Hinweis (`semantic_warning`). Das Feld `status` im Compliance-Ergebnis benennt die tatsächliche Prüftiefe: `vollständig` (beide Stufen gelaufen), `degradiert` (Stufe 2 ausgefallen) oder `stufe-2-deaktiviert` (bewusst abgeschaltet). Die Compliance-Kachel macht das sichtbar: im vollständigen Zustand über die Statuszeile „Stufe 1 + 2 geprüft“, im degradierten Zustand über das Amber-Label „nur Stufe 1“ — ein sauberer Durchlauf ohne Fund und eine still ausgefallene Stufe 2 sind damit unterscheidbar.

## API

HTML: `GET /`, `/settings/providers`, `/privacy`, `/info`. JSON: `POST /api/analyze`, `/api/estimate-footprint`, `/api/optimize`, `/api/send`, `/api/compliance/check` (Stufe-1-Vorabprüfung von Nachricht plus Chatverlauf, genutzt von der Mini-Ampel im Chat); Provider-CRUD samt Test/Modellen; Ollama-Status/Modelle und `/api/usage/summary`. `/api/send` liefert die real gemessene `sustainability`. Vor dem Aufruf des lokalen Analyse-/Optimierungsmodells maskieren `/api/analyze` und `/api/optimize` erkannte sensible Werte (z. B. IBAN, Kreditkartennummer) per `redact_sensitive`; Compliance-Prüfung und Trefferanzeige arbeiten weiter auf dem Original, und das `warning`-Feld weist auf die Maskierung hin. Platzhalter bleiben im optimierten Prompt sichtbar und werden nicht zurückgetauscht.

## Einschränkungen

CO₂-, Energie-, Kosten- und Dauerwerte sind konfigurierbare Beispielschätzungen, keine wissenschaftliche Messung, Abrechnung oder Garantie. Die Compliance-Prüfung ist keine Rechtsberatung. DNS-Rebinding kann ein MVP nicht vollständig ausschließen. Streaming, OAuth und providerspezifische Abweichungen sind nicht enthalten. Externe Integrationen werden in Tests gemockt.
