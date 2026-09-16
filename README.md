# Sustainable AI Gateway

Das Projekt beinhaltet ein lokales Flask-MVP zur Vorabanalyse von Prompts. Ollama liefert eine strukturierte lokale Analyse und einen optimierten Prompt. Dabei ergänzen lokale Module folgende Informationen für den Anwender im Dashboard:

- Compliance-Status
- Token
- Kosten
- Carbon-Footprint (Energie/CO₂/Wasser/Ressourcenverbrauch) und eine
- Antwortdauer-Schätzung

Zusätzlich wird eine Modellempfehlung für das Ziel-LLM gegeben (lokal oder extern). Diese basiert auf der eingestuften Aufgabenkomplexität sowie der nachfolgend beschriebenen Compliance-Prüfung.

Die Compliance-Prüfung erkennt personenbezogene oder vertrauliche Daten. Dazu sind zwei Stufen implementiert:

- eine deterministische Regelprüfung
- eine semantische Prüfung mit Hilfe eines lokalen Guardian-Modells

Der Energie-, CO₂-, Wasser- und Ressourcenverbrauch werden über [EcoLogits](docs/ECOLOGITS_INTEGRATION.md) berechnet, wenn in der Datenbank verfügbar bzw. in der Provider-Konfiguration hinterlegt ist. Für den Versand an ein lokales Ollama-LLM greift ersatzweise ein Fallback über die `psutil`-Lib, für alle anderen Fälle eine feste Formel (siehe [`CARBON_FOOTPRINT_REDESIGN.md`](docs/CARBON_FOOTPRINT_REDESIGN.md)).

Eine ausführliche Erklärung mit Architektur-, Ablauf-, Compliance-, Datenbank- und Sicherheitsdiagrammen befindet sich in der [technischen Dokumentation](docs/TECHNISCHE_DOKUMENTATION.md). In Ergänzung dazu befinden sich in der [Architektur.md](Architektur.md) weitere Details zur System- und SW-Architektur inkl. State- und Sequenzdiagramme.

## Architektur

- `app/routes`: HTML- und JSON-API-Blueprints
- `app/services`: Analyse, Compliance, Schätzungen (inkl. EcoLogits-Anbindung), Verschlüsselung und SSRF-Schutz
- `app/providers`: Ollama und OpenAI-kompatible APIs hinter einer gemeinsamen Abstraktion
- `app/templates`, `app/static`: Jinja, Vanilla JavaScript und responsives CSS
- `app/models.py`: Provider und optionale, promptfreie Nutzungslogs
- `tests`: Unit- und Routentests mit gemockten externen Aufrufen

Die Prompt-Analyse und der Versand sind technisch getrennt, d.h. die `/api/analyze` ruft keinen externen Provider auf. Der Versand verlangt dabei immer eine bewusste Bestätigung im Dashboard durch den Anwender und wird bei einer "rot" eingestuften Compliance-Prüfung serverseitig blockiert. Folgenachrichten im Chat durchlaufen ebenfalls alle Prüfungen und müssen bewusst bestätigt werden.

## Installation

Voraussetzungen: Python 3.12 und optional Ollama (Hinweis: Das Gateway startet auch ohne Ollama, dann aber ohne lokale Prompt-Analyse/-Optimierung und ohne semantische Compliance-Prüfung (Stufe 2)).

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

`OLLAMA_MODEL`, `OLLAMA_BASE_URL` und `OLLAMA_TIMEOUT_SECONDS` steuern die Integration. `OLLAMA_ANALYSIS_TIMEOUT_SECONDS=0` lässt die lokale Dashboard-Analyse ohne Zeitlimit laufen; ein positiver Wert setzt stattdessen ein Limit in Sekunden. `OLLAMA_ANALYSIS_KEEP_ALIVE` (Standard `30m`) hält das Analyse-Modell nach einem Aufruf im Speicher, damit Folgeanalysen in der gleichen Instanz laufen. Der Analyse-Aufruf sendet ein eigenes `num_ctx` (32768) und keine weiteren Optionen und ist damit unabhängig vom globalen Context-Default der Ollama-App; jede Analyse schreibt eine INFO-Logzeile mit eigener Dauer sowie `total_duration`/`load_duration` aus der Ollama-Antwort ins Terminal (`load` nahe 0 = warme Instanz). Ohne Ollama startet das Gateway weiterhin. `/api/ollama/status` meldet Status und Modelle. `LOCAL_CPU_TDP_WATT` (optional, leer = deaktiviert) aktiviert eine grobe CPU-Auslastungsformel für Energie/CO₂ bei lokalen Ollama-Sends, wenn EcoLogits dafür keinen Wert liefert.

## Start, Datenbank und Tests

SQLite und Tabellen werden beim ersten Start automatisch im `instance`-Verzeichnis angelegt. Die Datei `instance/gateway.db` ist deshalb nicht versioniert, sondern wird beim ersten Start lokal erzeugt.

```bash
flask --app app run --debug
pytest
flask calibrate-ratio
```

Dashboard: <http://127.0.0.1:5000>, Provider: `/settings/providers`. `flask calibrate-ratio` schlägt einen kalibrierten `EXPECTED_OUTPUT_RATIO`-Wert aus echten `UsageLog`-Daten vor (Mindeststichprobe 20 erfolgreiche Sends, `ENABLE_PROMPT_LOGGING=true` nötig); ändert nichts automatisch, die Übernahme in `.env` bleibt manuell.

## Provider und Sicherheit

Unterstützt werden Ollama, die native Anthropic Messages API und generische OpenAI-kompatible APIs (`/models`, `/chat/completions`). Claude Haiku 4.5 (`claude-haiku-4-5-20251001`, 1 USD Input/5 USD Output je Mio. Token) ist für einfache Anfragen hinterlegt; Claude Sonnet 4.6 (`claude-sonnet-4-6`, 3 USD/15 USD) für komplexe Aufgaben. Cache- und Batchpreise werden nicht verwendet. Private, Loopback-, Link-local- und reservierte externe Ziele werden nach DNS-Auflösung blockiert; Redirects sind deaktiviert. Localhost ist nur für `ollama` erlaubt. Schlüssel liegen Fernet-verschlüsselt in SQLite und erscheinen in API/HTML nur maskiert. EU-Hosting ist vom Betreiber vertraglich zu verifizieren. Die Formularfelder in der Provider-Konfiguration sind über `?`-Hilfe-Icons erläutert (Feldbedeutung, Beispielwerte).

Den Anthropic API-Key einmal unter `/settings/providers` eintragen. Dazu einen Provider vom Typ `Anthropic Claude` mit Base-URL `https://api.anthropic.com` anlegen. Nach der lokalen Prompt-Analyse empfiehlt das Dashboard Haiku oder Sonnet; der Nutzer kann direkt vor dem Versand trotzdem eines der beiden Modelle auswählen. Nach der ersten API-Antwort kann der Chat im Dashboard fortgesetzt werden. Der Verlauf bleibt im Browser und wird für Folgefragen als Kontext übertragen; pro Runde zeigt das Dashboard die von Anthropic gemeldeten Input-/Output-Tokens, deren Kosten, Gesamtkosten und kumulierte Umweltwerte.

Prompts werden standardmäßig nicht gespeichert. `ENABLE_PROMPT_LOGGING=true` speichert nur SHA-256-Hash, Token-/Modell-/Schätzmetadaten und Status. CSRF-Schutz, Größenlimits, sichere Cookie-Vorgaben, CSP und Eingabevalidierung sind aktiv. Verändernde API-Aufrufe benötigen den Sessionwert als `X-CSRF-Token`.

## Compliance Stufen

Stufe 1 prüft deterministisch mit Mustern und Prüfsummen (IBAN, Kreditkarte, Schlüssel u. a.). Stufe 2 ergänzt eine semantische Prüfung über ein lokales Guardian-Modell (Ollama): Sie erkennt Datenschutzrisiken im Sinne von DSGVO und KDG auch ohne prüfbare Muster — etwa „Person A aus der Abteilung Vertrieb ist heute krank gemeldet …" (identifizierbare Person plus Gesundheitsbezug). Funde heben die Ampel mindestens auf Gelb und erscheinen als eigene Stufe-2-Flags (`semantic_findings`) mit kurzer Begründung; Rot und das serverseitige Blockieren bleiben allein Sache der deterministischen Stufe 1. Stufe 2 läuft bei der Analyse (`/api/analyze`) und bei der Verlaufsprüfung (`/api/send`, `/api/compliance/check`). Von Stufe 1 erkannte sensible Werte werden — wie bei der Analyse — vor der Übergabe an das Guardian-Modell maskiert.

Konfiguration: `OLLAMA_GUARDIAN_MODEL` bestimmt das Modell (Standard `granite4.1-guardian:8b`, Bezug z. B. per `ollama pull granite4.1-guardian:8b`); ein leerer Wert deaktiviert die Stufe 2. `OLLAMA_GUARDIAN_TIMEOUT_SECONDS` (Standard 120) setzt einen eigenen Timeout statt des geteilten `OLLAMA_TIMEOUT_SECONDS`. Zu beachten ist, dass auf CPU-only-Hardware ein 8B-Guardian-Modell länger als das allgemeine Zeitlimit benötigen kann. `OLLAMA_GUARDIAN_KEEP_ALIVE` (Standard `30m`) hält die Modellinstanz zwischen den Prüfungen aktiv. Ist das Modell nicht erreichbar, überschreitet das Zeitlimit oder liefert es keine verwertbare Antwort, läuft alles mit Stufe 1 weiter, und das Ergebnis enthält statt eines Fehlers einen sichtbaren Hinweis (`semantic_warning`). Das Feld `status` im Compliance-Ergebnis benennt die tatsächliche Prüftiefe: `vollständig` (beide Stufen gelaufen), `degradiert` (Stufe 2 ausgefallen) oder `stufe-2-deaktiviert` (bewusst abgeschaltet). Die Compliance-Kachel macht das sichtbar: im vollständigen Zustand über die Statuszeile „Stufe 1 + 2 geprüft“, im degradierten Zustand über das Amber-Label „nur Stufe 1“ — ein sauberer Durchlauf ohne Fund und eine still ausgefallene Stufe 2 sind damit unterscheidbar.

## API

HTML: `GET /`, `/settings/providers`, `/privacy`, `/info`. JSON: `POST /api/analyze`, `/api/estimate-footprint`, `/api/optimize`, `/api/send`, `/api/compliance/check` (Stufe-1-Vorabprüfung von Nachricht plus Chatverlauf, genutzt von der Mini-Ampel im Chat); Provider-CRUD samt Test/Modellen; Ollama-Status/Modelle und `/api/usage/summary`. `/api/send` liefert die real gemessene `sustainability`. Vor dem Aufruf des lokalen Analyse-/Optimierungsmodells maskieren `/api/analyze` und `/api/optimize` erkannte sensible Werte (z. B. IBAN, Kreditkartennummer) per `redact_sensitive`; Compliance-Prüfung und Trefferanzeige arbeiten weiter auf dem Original, und das `warning`-Feld weist auf die Maskierung hin. Platzhalter bleiben im optimierten Prompt sichtbar und werden bewusst nicht durch echte Werte ersetzt.

## Einschränkungen

CO₂-, Energie-, Kosten- und Dauerwerte sind Schätzungen, keine Abrechnung oder Garantie: Wo EcoLogits mit anbieterbasierten Parametern rechnet, folgt sie dessen forschungsbasierter Methodik, sonst gelten illustrative Katalog-Annahmen bzw. eine einfache Fallback-Formel — in keinem Fall eine wissenschaftliche Messung. Die Compliance-Prüfung ist keine Rechtsberatung. DNS-Rebinding kann ein MVP nicht vollständig ausschließen. Streaming (komplette Modellantwort wird geholt), OAuth (statische API-Keys werden verwendet) und providerspezifische Abweichungen sind nicht enthalten. Externe Provider APIs werden in Tests gemockt. Der Carbon-Footprint fließt aktuell nicht in die Modellauswahl ein. Er wird erst für das bereits gewählte Modell berechnet.
