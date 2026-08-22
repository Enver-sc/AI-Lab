# AGENTS.md — Coding-Regeln für Sustainable AI Gateway (AI Dashboard)

Diese Datei folgt der offenen [agents.md](https://agents.md)-Konvention und wird von
KI-Coding-Assistenten gelesen (Claude Code, Codex CLI, Cursor u. a.). Wer ein anderes
Tool nutzt, muss nichts umstellen — einfach diese Datei im Projekt-Root lassen.
Claude Code liest sie über den Import in `CLAUDE.md`.

## Projektüberblick

Flask-MVP zur Vorabanalyse von Prompts (Token-, Kosten-, CO₂-, Dauer-Schätzung,
Compliance-Check, Modellempfehlung). Details zu Architektur, Ablauf und Sicherheit:
`README.md`, `Architektur.md`, `docs/TECHNISCHE_DOKUMENTATION.md`.

## Struktur

- `app/routes`: HTML- und JSON-API-Blueprints — dünn halten, keine Geschäftslogik
- `app/services`: Analyse, Compliance, Schätzungen, Verschlüsselung, SSRF-Schutz
- `app/providers`: Ollama und OpenAI-kompatible APIs hinter gemeinsamer Abstraktion
  (`app/providers/base.py`) — neue Provider hier einhängen, nicht in Routen verzweigen
- `app/models.py`: SQLAlchemy-Modelle, promptfreie Nutzungslogs
- `app/templates`, `app/static`: Jinja, Vanilla JS, CSS
- `tests`: pytest, externe Aufrufe werden gemockt

Neue Logik dort einbauen, wo sie laut dieser Trennung hingehört, statt Kürzeln in
Routen.

## Code-Stil

- **Neuer und geänderter Code**: normale, mehrzeilige Formatierung (PEP 8 / wie mit
  Black formatiert). Keine Verkettung mehrerer Anweisungen per Semikolon, keine
  einzeiligen `try/except`-Blöcke.
- **Bestehender Code** ist bewusst kompakt geschrieben (Semikolons, Einzeiler). Den
  nicht aus stilistischen Gründen umformatieren — nur der tatsächlich geänderte
  Bereich wird in neuem Stil geschrieben. Kein Drive-by-Reformatting ganzer Dateien.
- Bezeichner (Funktionen, Variablen, Klassen) auf Englisch, wie im bestehenden Code.
- Nutzersichtbarer Text (Fehlermeldungen, UI-Strings, Templates) auf Deutsch, wie
  bisher.

## Typisierung

Neue Funktionssignaturen (Parameter und Rückgabewert) bekommen Type Hints.
Bestehende, untypisierte Funktionen werden nicht extra deswegen angefasst — nur wenn
sie ohnehin geändert werden, Hints ergänzen.

## Kommentare & Docstrings

- Sprache: Deutsch.
- Nur schreiben, wenn das *Warum* nicht offensichtlich ist (versteckte Annahme,
  Workaround, Sicherheits-Constraint). Kein Kommentar, der nur wiederholt, was der
  Code ohnehin zeigt.
- Keine mehrzeiligen Docstring-Blöcke. Ein kurzer Einzeiler reicht, falls überhaupt
  nötig.

## Sicherheit (in diesem Projekt besonders wichtig)

- Neue externe Zielorte (Provider-URLs, Webhooks etc.) laufen durch
  `validate_provider_url` bzw. dasselbe SSRF-Muster (DNS-Auflösung prüfen, private/
  Loopback/Link-local/reservierte Ziele blocken, keine Redirects).
- API-Keys nie im Klartext speichern oder loggen — Fernet-Verschlüsselung wie in
  `encryption_service.py`, maskiert ausgeben (`mask_secret`).
- Prompts standardmäßig nicht speichern; falls `ENABLE_PROMPT_LOGGING` aktiv ist, nur
  SHA-256-Hash plus Metadaten, nie den Rohtext.
- `.env` niemals committen; neue Secrets/Config-Werte in `.env.example` mit Platzhalter
  ergänzen.
- Verändernde API-Aufrufe brauchen CSRF-Schutz (`X-CSRF-Token`), wie bei bestehenden
  Endpunkten.

## Barrierefreiheit (WCAG / EN 301 549 — gezielter Light-Check, kein Vollaudit)

Kein formales Konformitäts-Audit, aber bei UI-Änderungen auf folgende, in
`tests/test_accessibility.py` automatisiert geprüfte Punkte achten:

- **Keine Blitz-/Flacker-Effekte** (WCAG 2.3.1): neue Animationen/Übergänge
  dürfen nicht wiederholt/blinkend sein (max. 3 Wiederholungen pro Sekunde,
  im Zweifel eine einmalige, sanfte Transition statt einer Schleife).
- **Neue Farb-Tokens in `:root` (`style.css`)** müssen einen Kontrast von
  mindestens 4,5:1 gegen die Flächen behalten, auf denen sie als Text
  eingesetzt werden (`test_text_color_combinations_meet_wcag_aa_contrast`
  prüft das automatisch für alle bestehenden Text-auf-Hintergrund-Paare).
- **Farbe nie als einziger Bedeutungsträger** (WCAG 1.4.1): neue
  farbcodierte Zustände (Ampeln, Ring-/Segmentfarben o. Ä.) brauchen
  zusätzlich Text, Icon oder Position als Unterscheidungsmerkmal.
- **`prefers-reduced-motion: reduce` respektieren** — neue Transitions/
  Animationen in dieses bestehende Media-Query-Muster in `style.css`
  aufnehmen, nicht eigenständig danebensetzen.
- **Fokus-Sichtbarkeit nicht unterdrücken** — kein `outline:none`/`outline:0`
  ohne einen mindestens gleichwertigen eigenen `:focus`-Stil (aktuell wird
  bewusst der native Browser-Fokusring genutzt).

## Tests

- pytest, externe Aufrufe (Ollama, Provider-APIs) werden gemockt, keine echten
  Netzwerkaufrufe in Tests.
- Neue Features und Bugfixes bekommen einen Test in `tests/`.
- Ausführen: `pytest` (Fixtures in `tests/conftest.py`, u. a. `app`, `client`, `csrf`).

## Fehlerbehandlung

- In Routen: `ValueError` für Nutzerfehler, über den bestehenden `error()`-Helper in
  eine JSON-Fehlerantwort übersetzen (siehe `app/routes/api.py`).
- Providerspezifische Fehler über eigene Exception-Klassen (`ProviderError`,
  `OllamaError`), nicht über generische `Exception`.

## Was KI-Assistenten unterlassen sollen

- Keine ungefragten Refactorings oder Formatierungs-Durchläufe über bestehenden Code.
- Keine neuen Abhängigkeiten/Linter/Formatter einführen, ohne dass das Team das
  entschieden hat.
- Keine Secrets, `.env`-Inhalte oder API-Keys in Commits, Logs oder Kommentare
  schreiben.
- Bei Änderungen an API-Endpunkten oder Architektur: `README.md` bzw.
  `Architektur.md` entsprechend nachziehen.

## Pflege dieser Datei

Diese Datei wird bei Bedarf im Team abgestimmt und aktualisiert, nicht einseitig von
einem KI-Assistenten umgeschrieben.
