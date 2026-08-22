# EcoLogits-Integration — Sustainable AI Dashboard

> Status: umgesetzt (§1–§11 `[ERLEDIGT]`). §12 sammelt bewusst offene, methodische
> Einschränkungen, die eine eigene Abstimmung brauchen, keinen Schnellschuss.
> Dieses Dokument beschreibt die tatsächlich implementierte Lösung inkl. der
> Erkenntnisse aus der Umsetzung und aus dem Anwender-Review.

## Kontext

Das Dashboard schätzt den CO₂-Fußabdruck pro Prompt aktuell über eine einfache,
von Hand geschriebene lineare Näherung in `app/services/sustainability_service.py`
(`energy = tokens/1000 × modellabhängige Konstante`, `co2 = energy × carbon_intensity`)
— keine Herleitung aus einer veröffentlichten Methodik. Überall im Projekt
(README, technische Dokumentation) ist das entsprechend als *"konfigurierbare
MVP-Schätzwerte; keine wissenschaftliche Messung"* gekennzeichnet. Ziel dieser
Integration ist es, diese Schätzung mit **EcoLogits** zu untermauern — einer
Python-Bibliothek, die Umweltwirkungen von LLM-Anfragen nach einer
dokumentierten, forschungsbasierten Methodik schätzt (Energie, CO₂e/GWP, Wasser,
Ressourcenverbrauch — siehe Glossar am Ende) — und die Parameter, die deren
Genauigkeit bestimmen (Modellparameteranzahl, Rechenzentrums-PUE/WUE,
Strommix-Zone sowie — falls tatsächlich bekannt — die reale Anbieteridentität),
an den richtigen Stellen konfigurierbar zu machen statt sie hart zu kodieren.

**Der Nutzen für den Anwender**: Der Nutzer gibt im Dashboard einen Prompt ein,
dieser wird analysiert, und das Dashboard zeigt den geschätzten CO₂-Fußabdruck
für diesen Prompt. Die Analyse schlägt bereits heute einen *optimierten*
(kürzeren/präziseren) Prompt als Alternative vor. Der Fußabdruck dieses
optimierten Prompts wird bisher nirgends berechnet oder angezeigt — nur der des
Originals. Damit der Nutzer tatsächlich für CO₂ sensibilisiert wird, soll das
Dashboard den Fußabdruck **beider** Varianten nebeneinander zeigen, sodass der
Vorteil einer Optimierung sichtbar wird statt nur behauptet zu werden. Das prägt
den Entwurf in §4 und §6.

## SDK-Anbindung vs. rohe `requests` — sollten wir die Transportschicht wechseln?

EcoLogits bietet zwei Wege, an Wirkungsdaten zu kommen: (a) das automatische
Patchen eines offiziellen Anbieter-SDK-Clients (`openai`, `anthropic`, `cohere`,
`google-genai`, `huggingface_hub`, `mistralai` — sechs Pakete, optional auch über
`litellm` erreichbar), sodass Wirkungswerte automatisch an `response.impacts`
hängen, oder (b) der direkte Aufruf der manuellen Berechnungs-API, bei dem wir
Modell-, Token- und Latenzdaten selbst übergeben. Dieses Projekt nutzt für Anfragen
an Provider durchgängig rohe `requests`-Aufrufe (`ollama_service.py`,
`providers/openai_compatible.py`), daher ist die Frage berechtigt, ob ein Wechsel
zu offiziellen SDKs den genaueren, automatischen Pfad freischalten würde. Das ist
keine Selbstverständlichkeit — hier die tatsächliche Abwägung, geprüft anhand von
EcoLogits' Quellcode und Dokumentation (nicht angenommen):

- **EcoLogits' Anbieterkatalog (verwendet sowohl beim SDK-Patchen als auch beim
  manuellen `llm_impacts()`-Lookup) ist eine geschlossene Liste genau dieser sechs
  kommerziellen Anbieter**, indiziert über deren eigene veröffentlichte
  Modellnamen. Es gibt **keine Einträge für lokal über Ollama betriebene,
  offene Modelle** — auch die `litellm`-Integration bestätigt das: ihr eigenes
  Tutorial verlangt einen Anbieter-API-Key und zeigt ausschließlich Cloud-Modelle,
  kein Ollama- oder Self-Hosted-Beispiel existiert. Das bedeutet: **ein
  Transportwechsel (rohe Requests → offizielles SDK oder → litellm) würde keine
  Ollama-Unterstützung hinzufügen** — Ollama-Modelle benötigen unabhängig vom
  HTTP-Transport den manuellen, parameteranzahl-basierten Pfad
  (`compute_llm_impacts()`). Das ist laut `Architektur.md` (lokal-first-Ansatz)
  der überwiegende Anwendungsfall hier und damit das entscheidende Argument.
- Für die *generischen* Providertypen `openai_compatible`/`eu_openai_compatible`/
  `custom`: Diese erlauben absichtlich, dass ein Code-Pfad **beliebige**
  OpenAI-API-kompatible Backends anspricht (echtes OpenAI, Azure OpenAI, ein
  Reseller, eine selbst gehostete vLLM-/LM-Studio-Instanz usw.) über eine
  konfigurierbare `base_url`. Ein Wechsel zum offiziellen `openai`-SDK würde diese
  Mehrdeutigkeit nicht auflösen — auch das SDK nimmt lediglich eine `base_url`
  entgegen, und EcoLogits' Patch für den Anbieter `"openai"` geht weiterhin
  blind von echter OpenAI-Hardware/-Modellen aus. Ein Transportwechsel bringt
  hier also **keinerlei Genauigkeitsgewinn** — das Problem der Anbieteridentität
  wird durch das explizite Opt-in-Feld `ecologits_provider` gelöst (§2), nicht
  durch die Wahl des HTTP-Clients.
- Der einzige echte Vorteil des SDK-Patchens wäre *Komfort* (Wirkungswerte hängen
  automatisch an jede Antwort, statt dass wir `model_name`/`output_token_count`/
  `request_latency` selbst übergeben) — auf Kosten von sechs zusätzlichen,
  schwergewichtigen Anbieter-SDK-Abhängigkeiten und dem Verlust der aktuellen,
  einheitlichen `OpenAICompatibleProvider`-Abstraktion zugunsten je eines
  Code-Pfads pro Anbieter.

**Empfehlung: rohe `requests` beibehalten, Anbindung über EcoLogits' manuelle
Berechnungs-API** (`llm_impacts()`, wenn ein Provider die reale Anbieteridentität
explizit bestätigt; sonst `compute_llm_impacts()`). Das kostet gegenüber
SDK-Patchen keinerlei Genauigkeit für den tatsächlichen Provider-Mix dieses
Projekts und vermeidet einen Transportschicht-Umbau, der für ein
CO₂-Dashboard-Feature nicht im Scope liegt. Diese Entscheidung ist bewusst
festgehalten, falls es aus einem anderen — von EcoLogits unabhängigen — Grund
später sinnvoll wird, auf Anbieter-SDKs zu standardisieren.

## Ansatz

EcoLogits wird als **zusätzliche Schicht über** der bestehenden Formel
eingeführt, nie als harter Ersatz — dasselbe defensive Fallback-Muster, das
bereits bei Ollama-Fehlern verwendet wird (`analyze_with_ollama` → sicherer
`DEFAULT`-Wert bei Fehler). Ein neues Modul `ecologits_service.py` löst die
Konfiguration über drei Ebenen auf (Provider-Datensatz → statischer
Katalogeintrag → globaler Konfigurations-Default), wählt den passenden
EcoLogits-Aufruf und liefert bei jedem Fehler stets sicher `(None, warning)`
zurück statt eine Exception zu werfen — `/api/analyze` und `/api/send` können
dadurch nie an dieser Stelle fehlschlagen.

---

## 1. Abhängigkeit `[ERLEDIGT]`

`requirements.txt`: `ecologits==0.11.1` ergänzen (nur das Basispaket — keine
Extras wie `[openai]` nötig, da kein SDK gepatcht wird). Einmaliger
Funktionstest bei der Umsetzung: `pip install -r requirements.txt && python -c
"import ecologits"` im Projekt-venv (aktuell Python 3.14 — EcoLogits verlangt
`>=3.10,<4`, sollte also auflösen, ist aber neu genug, um es zu prüfen statt
anzunehmen).

---

## 2. Konfigurierbare Parameter und ihr Ort `[ERLEDIGT]`

**Rangfolge für jeden EcoLogits-Parameter: `ProviderConfiguration`-Feld (falls
gesetzt) → Katalogeintrag in `MODELS` (falls gesetzt) → globaler Default in
`config.py`.** `ecologits_provider` (das explizite "das ist wirklich Anbieter X"
Opt-in) hat keine Fallback-Ebene — es ist `None`, solange es nicht bewusst
gesetzt wird.

**Global (`config.py` + `.env.example`, neben dem bestehenden
`CARBON_INTENSITY_G_PER_KWH`):**
- `ECOLOGITS_ENABLED` (bool, Default `true`) — globaler Schalter; bei `false`
  liefert der Service sofort `(None, None)`, ohne `ecologits` überhaupt zu
  importieren.
- `ECOLOGITS_ELECTRICITY_MIX_ZONE` (str, Default `"DEU"` — das Projekt ist
  durchgängig EU-/Deutschland-fokussiert; fällt nur bei einem fehlgeschlagenen
  Zonen-Lookup weiter auf EcoLogits' eigenen Weltdurchschnitt `"WOR"` zurück).
- `ECOLOGITS_DEFAULT_DATACENTER_PUE` (float, Default `1.2`) /
  `ECOLOGITS_DEFAULT_DATACENTER_WUE` (float, Default `1.8`) — generische
  Rechenzentrums-Annahmen, wenn weder Provider noch Katalogeintrag sie
  überschreiben.

**Pro statischem Demo-Modell (`app/services/model_catalog.py`, jedes der 5
`MODELS`-Dicts erweitern):**
- `ecologits_provider` (Default `None` für alle — der Katalog ist illustrative
  Demo-Daten, kein anbieterbestätigtes Deployment, daher immer der manuelle
  Parameteranzahl-Pfad, nie die Anbieter-Lookup-Sicherheit vortäuschen).
- `eco_active_params_b`, `eco_total_params_b` (Milliarden Parameter) — grobe,
  ausdrücklich als illustrativ dokumentierte Werte, passend zur bestehenden
  Größenordnung von `input_energy`/`output_energy` je Modellklasse (z. B.
  local_small ≈ 3 Mrd., local_large ≈ 13 Mrd., cloud_small ≈ 8 Mrd.,
  cloud_large ≈ 70 Mrd., eu_hosted ≈ 20 Mrd.).
- `eco_datacenter_pue`, `eco_datacenter_wue`, `eco_electricity_mix_zone`
  (alle `None` per Default → fallen auf die globale Konfiguration zurück).

**Pro echtem Provider (`app/models.py`, `ProviderConfiguration`, neue
nullable Spalten):**
- `ecologits_provider` (`String(40)`, nullable) — einer von
  `openai|anthropic|cohere|google_genai|huggingface_hub|mistralai`; nur gesetzt,
  wenn die Administration bestätigt, dass der Endpunkt wirklich das echte
  Modell dieses Anbieters ist.
- `eco_active_params_b`, `eco_total_params_b` (`Float`, nullable, Milliarden) —
  bewusst dieselben Feldnamen wie im Katalog (nicht `eco_model_*`), damit
  `ecologits_service.py` beide Objektarten mit derselben `_resolve()`-Hilfsfunktion
  abfragen kann.
- `eco_datacenter_pue`, `eco_datacenter_wue` (`Float`, nullable).
- `eco_electricity_mix_zone` (`String(3)`, nullable, ISO 3166-1 alpha-3).

Keine neuen `UsageLog`-Spalten — das bestehende Feld `estimated_co2_grams`
(aktuell in `send()` fest auf `0` gesetzt) wird künftig tatsächlich befüllt.
Energie/Wasser/ADPe werden im Dashboard live aus der API-Antwort angezeigt,
aber nicht persistiert — das hält die Schemaänderung minimal.

**Idempotente SQLite-Migration**: In diesem Projekt gibt es kein Flask-Migrate —
`db.create_all()` erzeugt nur fehlende *Tabellen*, keine neuen *Spalten* in der
bestehenden `instance/gateway.db`. Neue Funktion `ensure_schema_upgrades(app)`
in `app/extensions.py`, direkt nach `db.create_all()` in `create_app()`
aufgerufen. Nur für den `sqlite`-Dialekt: `PRAGMA table_info(provider_configuration)`
lesen, `ALTER TABLE provider_configuration ADD COLUMN <name> <typ>` für jede der
6 neuen Spalten, die noch fehlt. Bei jedem Start unbedenklich ausführbar
(No-op, sobald einmal angewendet).

---

## 3. Neues Modul: `app/services/ecologits_service.py` `[ERLEDIGT]`

Folgt der bestehenden Konvention "nie über die Routen-Grenze hinweg werfen,
stattdessen sicheren Default + Warnhinweis zurückgeben" aus
`analysis_service.parse_analysis`.

```python
def compute_impacts(output_tokens, request_latency_seconds, provider=None, catalog_model=None, app_config=None):
    """Liefert (impacts_dict | None, warning | None). Wirft nie."""
```

- `provider`: eine `ProviderConfiguration`-Instanz oder `None`.
- `catalog_model`: ein `MODELS`-Dict oder `None`.
- Auflösungsreihenfolge je Feld wie in §2 definiert; lassen sich im manuellen
  Pfad die Parameteranzahlen auf keiner Ebene auflösen, liefert die Funktion
  `(None, None)` (nichts zu berechnen, kein meldenswerter Fehler).
- `ECOLOGITS_ENABLED=false` (oder kein `app_config` übergeben) → `(None, None)`,
  kein Import wird versucht.
- `ecologits_provider` aufgelöst und in der bekannten Menge (`openai`, `anthropic`,
  `cohere`, `google_genai`, `huggingface_hub`, `mistralai`) → `ecologits.tracers
  .utils.llm_impacts(...)`; sonst → `ecologits.impacts.llm.compute_llm_impacts(...)`
  mit den aufgelösten Parametern sowie den Strommixfaktoren aus
  `ecologits.electricity_mix_repository.electricity_mixes.find_electricity_mix
  (zone=...)` (fällt bei unbekannter Zone zusätzlich auf `"WOR"` zurück, das laut
  Datensatz immer existiert — dieser zweite Fallback macht den `mix is None`-Zweig
  in der Praxis zu einem reinen Sicherheitsnetz).
- **Update, siehe [`CARBON_FOOTPRINT_REDESIGN.md`](CARBON_FOOTPRINT_REDESIGN.md)
  (Designvorschlag A):** liefert der Anbieter-Lookup-Pfad kein Ergebnis (z. B.
  Modell nicht in der EcoLogits-Datenbank), fällt `compute_impacts()` seither
  automatisch zusätzlich auf den manuellen Parameter-Pfad zurück, falls dafür
  Werte hinterlegt sind — zweistufiger statt der hier ursprünglich beschriebenen
  einstufigen Entscheidung.
- Am installierten Paket (0.11.1) verifiziert: `llm_impacts()` liefert ein
  `ImpactsOutput` mit `.energy/.gwp/.adpe/.pe/.wcf` (je ein `BaseImpact` mit
  `.value: float | RangeValue` und `.unit`), `.has_errors`/`.errors` sowie
  `.has_warnings`/`.warnings`. `compute_llm_impacts()` liefert dagegen ein
  einfacheres `Impacts`-Objekt **ohne** `errors`/`warnings`-Attribute — die
  Unterscheidung ist im Code über zwei separate Hilfsfunktionen abgebildet
  (`_compute_via_provider_lookup` vs. `_compute_via_manual_parameters`).
  `RangeValue.mean` wird verwendet, um Werte, die EcoLogits als Intervall liefert
  (z. B. Parameteranzahl bei undokumentierten/MoE-Architekturen), auf eine einzelne
  Zahl zu reduzieren.
- Jede Exception beim EcoLogits-Aufruf (auch nicht vollständig dokumentierte, z. B.
  Pydantic-Validierungsfehler bei unplausiblen Parametern) oder ein befülltes
  `impacts.errors` (z. B. `model-not-registered`) → Logging über ein
  modul-eigenes `logging.getLogger(__name__)` (bewusst **kein** `current_app.logger`,
  damit das Modul ohne Flask-Anwendungskontext testbar bleibt), Rückgabe
  `(None, FALLBACK_WARNING)`.
- Erfolg mit `impacts.has_warnings` → Wirkungs-Dict plus ein deutscher
  Warnhinweis, der die Unsicherheiten zusammenfasst (z. B. "Schätzung mit
  Unsicherheiten: Modellarchitektur nicht veröffentlicht." — das trifft in der
  Praxis z. B. auf `gpt-3.5-turbo` zu, dessen Architektur OpenAI nie
  veröffentlicht hat).
- Bei Erfolg: `impacts_dict = {"energy_wh":..., "co2_grams":...,
  "water_ml":..., "adpe_ug_sb_eq":..., "mode":
  "llm_impacts"|"compute_llm_impacts"}` (GWP in kgCO2eq × 1000 → Gramm, passend
  zur bestehenden Einheit von `co2_grams`; Energie in kWh × 1000 → Wattstunde
  (`[ERGÄNZT]`, lesbarere Größenordnung); Wasser in L × 1000 →
  Milliliter (`[ERGÄNZT]`, siehe `CARBON_FOOTPRINT_REDESIGN.md`, sonst rundet
  der Wert bei kurzen Prompts fast immer auf 0); ADPe in kg Sb-eq × 1e9 →
  Mikrogramm, siehe §11 — das rohe kg-Sb-eq-Feld war nicht gerundet und lag
  typischerweise bei 1e-10..1e-11, was im Dashboard als rohe wissenschaftliche
  Notation gerendert wurde).

Keine Session-Injektion nötig (anders als bei den HTTP-basierten
Provider-Services) — EcoLogits ist eine reine lokale Berechnung, keine
Netzwerkanfrage. `tests/test_ecologits_service.py` ruft die echte, installierte
EcoLogits-Bibliothek daher direkt auf (kein Patchen nötig) und deckt beide Pfade,
die Rangfolge sowie Fehler-/Warnungsfälle ab.

---

## 4. Anbindung in `app/routes/api.py` `[ERLEDIGT]`

**`analysis_payload()`** (Vorab-Schätzung, `/api/analyze`, `/api/optimize`):
Nach der Berechnung von `duration = estimate_duration(...)`
`compute_impacts(output, duration["max_seconds"], provider=None,
catalog_model=model, app_config=current_app.config)` aufrufen. Ergebnis in das
bestehende `sustainable`-Dict mischen (`{**sustainable, **eco_result}`, falls
`eco_result` vorhanden), sodass die Antwort stets dieselben Schlüssel enthält,
die das Frontend erwartet, mit EcoLogits-Werten als Priorität. Die
zurückgegebene Warnung als neuen Schlüssel `sustainability_warning` ergänzen
(getrennt vom bestehenden `warning`-Feld der Ollama-Analyse, damit das
Dashboard beide unterschiedlich beschriften kann).

> **⚠️ ÜBERHOLT — entfernt.** Der komplette Abschnitt "Vergleich Original- vs.
> optimierter Prompt" (bis zum Ende von §4) beschreibt eine Funktion, die
> mittlerweile wieder entfernt wurde. Grund und Nachfolge-Design:
> [`CARBON_FOOTPRINT_REDESIGN.md`](CARBON_FOOTPRINT_REDESIGN.md) — der
> Vergleich war strukturell fast immer negativ für den optimierten Prompt
> (Ollamas Optimierung zielt auf Klarheit/Präzision, nicht Kürze). Als
> historische Aufzeichnung belassen, nicht mehr im Code aktiv.

**Vergleich Original- vs. optimierter Prompt** (neu, adressiert den
Nutzen aus dem Kontext-Abschnitt): Die Ollama-Analyse liefert bereits
`analysis["optimized_prompt"]` — einen umformulierten, meist kürzeren
Prompt-Vorschlag — der bisher nirgends gemessen wird. Nachdem die Werte für
den Original-Prompt berechnet sind: falls `analysis["optimized_prompt"]` nicht
leer ist und sich vom Original unterscheidet (Bedingung:
`optimized_prompt.strip() and optimized_prompt.strip() != prompt.strip()` —
überspringt den Sicherheits-Default-Fall mit leerem `optimized_prompt`), die
gleiche kleine Pipeline ein zweites Mal ausführen und als neuen Schlüssel
`"optimized"` anhängen:

**Wichtiger Befund aus der Umsetzung, der den ursprünglichen Entwurf verändert
hat:** Ein erster Testlauf zeigte, dass Original- und optimierter Prompt
identische CO₂-Werte lieferten, unabhängig von der Tokenanzahl. Ursache:
`compute_llm_impacts()` hat **keinen Parameter für die Eingabe-/Prompt-
Tokenanzahl** — die Formel hängt ausschließlich von `output_token_count` ab
(EcoLogits' Methodik modelliert nur die autoregressive Antwortgenerierung, nicht
die Prompt-Verarbeitung). Da die Anwendung für Original und Optimierung
denselben festen `DEFAULT_EXPECTED_OUTPUT_TOKENS`-Wert verwendet hätte, wäre der
Vergleich in der Praxis fast immer 0 % Ersparnis gewesen — unabhängig davon, wie
sehr der Prompt gekürzt wurde. Das hätte den in §Kontext beschriebenen Zweck
(Sensibilisierung durch sichtbaren Unterschied) verfehlt.

Lösung: eine explizit dokumentierte Heuristik, **kein Teil der EcoLogits-
Methodik**, die die erwartete Ausgabelänge proportional zur
Prompt-Tokenanzahl skaliert:

```python
def optimized_payload(optimized_prompt, analysis, compliance, tokens, output, mode, carbon_intensity):
    tokens_opt = estimate_tokens(optimized_prompt)
    # Heuristische Annahme, nicht Teil der EcoLogits-Methodik: EcoLogits' Formel haengt nur von
    # der Anzahl der Ausgabe-Token ab, nicht vom Prompt selbst -- ohne eine Annahme dazu waere
    # der CO2-Vergleich original/optimiert immer identisch. Wir nehmen an, dass ein proportional
    # kuerzerer Prompt tendenziell zu einer proportional kuerzeren Antwort fuehrt.
    output_opt = max(1, round(output * tokens_opt / tokens))
    model_opt, reason_opt = recommend(analysis, compliance, tokens_opt, mode)
    # complexity_score stammt aus der Ollama-Analyse des Original-Prompts; der optimierte
    # Prompt wird nicht erneut eigenstaendig bewertet, Dauer/Modellwahl sind also Naeherungen.
    duration_opt = estimate_duration(tokens_opt, output_opt, analysis["complexity_score"], model_opt)
    sustainability_opt, sustainability_opt_warning = sustainability_for(tokens_opt, output_opt, model_opt, duration_opt, carbon_intensity)
    return {
        "prompt_tokens": tokens_opt,
        "expected_output_tokens": output_opt,
        "recommendation": {**model_opt, "reason": reason_opt},
        "estimated_cost": estimate_cost(tokens_opt, output_opt, model_opt),
        "sustainability": sustainability_opt,
        "sustainability_warning": sustainability_opt_warning,
        "duration": duration_opt,
    }
```

`sustainability_for(tokens, output, model, duration, carbon_intensity)` ist eine
gemeinsame Hilfsfunktion (mischt Fallback-Formel und EcoLogits-Ergebnis), die
sowohl für den Original- als auch den optimierten Pfad verwendet wird — keine
doppelte Logik.

**Beobachtung aus echten Testläufen gegen einen lokal laufenden Ollama:** Die
Heuristik geht in beide Richtungen — und die erste UI-Fassung des
Vergleichs-Widgets machte das nicht klar genug. Ursprünglich hieß die dritte
Kachel "Ersparnis" mit einer Formel `(1 - optimiert/original) * 100`; bei einem
Prompt, dessen CO₂-Wert durch die Optimierung *anstieg* (42 → 100 Token, da
Ollama eine ausführlichere statt kürzere Umformulierung vorschlug: 0,0168 g →
0,0186 g), zeigte das Widget "−11 %" unter dem Label "Ersparnis" — mathematisch
korrekt (negative Ersparnis = Mehrverbrauch), aber für Anwender missverständlich.
Behoben durch Umbenennung zu "Finale CO₂e-Bilanz" mit vorzeichenbehafteter
Differenz `(optimiert - original) / original * 100` (`+11 %` in Rot bei mehr
CO₂e, `-12 %` in Grün bei weniger) — ein "Bilanz"-Label trägt beide Richtungen
natürlich, ohne dass "Ersparnis"/"Mehrverbrauch" dynamisch getauscht werden
müsste. Das ist kein Fehler in der Berechnung, sondern ehrliches Verhalten:
nicht jeder von Ollama vorgeschlagene "optimierte" Prompt ist tatsächlich
kürzer, und die Anzeige
spiegelt das wider, statt eine Verbesserung zu unterstellen.

Weitere Einschränkung (ein Einzeiler im Code, da nicht offensichtlich):
`analysis["complexity_score"]` stammt aus der Ollama-Analyse des *Original*-
Prompts — der optimierte Prompt wird nicht erneut eigenständig analysiert,
daher sind `duration_opt`/`model_opt` Näherungen auf Basis des ursprünglichen
Komplexitätswerts, keine neue Einschätzung. Der Schlüssel `"optimized"` wird bei
fehlgeschlagener Bedingung vollständig weggelassen (nicht einmal `null`), damit
das Frontend sein Fehlen als "keine eigenständige Optimierung verfügbar"
interpretieren kann.

**`send()`** (`/api/send`, reale Nutzung): Nach Berechnung von `latency` und
`output` `compute_impacts(output, latency/1000, provider=provider,
catalog_model=None, app_config=current_app.config)` aufrufen.
`UsageLog.estimated_co2_grams = eco_result["co2_grams"] if eco_result else 0`
setzen (kein erfundener Fallback-Wert für reale Versände — entweder liefert
EcoLogits eine echte Zahl, oder es bleibt bei `0`, dasselbe Ehrlichkeitsprinzip
wie heute, nur künftig teils ungleich null). Zusätzlich `sustainability`/
`sustainability_warning` in die JSON-Antwort aufnehmen, damit das Dashboard
reale Werte nach dem Versand zeigen kann, nicht nur die Vorab-Schätzung.

---

## 5. Einstellungen-UI `[ERLEDIGT]`
(`app/templates/providers.html`, `app/static/js/providers.js`,
`apply_provider()`/`serialize_provider()` in `api.py`)

Kleine Feldgruppe "Erweitert: EcoLogits" im Provider-Formular ergänzen
(passend zum bestehenden knappen Inline-Stil): ein Auswahlfeld für
`ecologits_provider` (leer = "Nicht gesetzt (manuelle Schätzung)", plus die
6 Anbieteroptionen) mit Hinweistext — *"Nur setzen, wenn der Endpunkt
nachweislich das echte Modell dieses Anbieters ist."* — sowie Zahlenfelder für
aktive/Gesamt-Parameter (Milliarden), PUE, WUE und ein dreistelliges
Zonenfeld. `apply_provider()` validiert `eco_provider` gegen die bekannte
Menge und parst die Zahlenfelder (leerer String → `None`);
`serialize_provider()` liefert dieselben Felder zurück, damit der
Bearbeiten-/Rücklese-Fluss in `providers.js` funktioniert. Alle Felder
optional, Default leer — vollständig abwärtskompatibel zu bestehenden
Provider-Datensätzen.

---

## 6. Dashboard `[ERLEDIGT]`
(`app/templates/dashboard.html`, `app/static/js/dashboard.js`)

Die `.metrics`-Kachelzeile (aktuell CO₂e/Kosten/Dauer/Compliance) um zwei
weitere Kacheln erweitern: Energie (damals kWh, seither auf Wh umgestellt —
siehe §3) und einen kombinierten
Wasser/ADPe-Hinweis — Anzeige von `–`, wenn EcoLogits keinen Wert liefern
konnte (die Fallback-Formel liefert nur Energie/CO₂, nie Wasser/ADPe).
`render()` in `dashboard.js` um die Befüllung aus `data.sustainability.*`
erweitern, sowie den bestehenden `toast()`-Aufruf um `data.sustainability_warning`
ergänzen (mit dem bestehenden `data.warning` zusammengeführt, kein zweiter
Toast). Den Erfolgspfad nach dem Versand erweitern, um die realen
`sustainability`-Werte anzuzeigen, die `/api/send` künftig liefert.

> **⚠️ ÜBERHOLT — entfernt.** Das folgende "Vergleichs-Widget Original vs.
> optimiert" wurde zusammen mit der zugehörigen Backend-Logik entfernt, siehe
> Hinweis in §4 und [`CARBON_FOOTPRINT_REDESIGN.md`](CARBON_FOOTPRINT_REDESIGN.md).
> Als historische Aufzeichnung belassen.

**Vergleichs-Widget Original vs. optimiert** (neu): Das bestehende
`#optimization`-Panel zeigt den optimierten Prompt-Text und Vorschläge, aber
keine Zahlen. Ein kleiner Vergleichsblock im selben Panel, nur sichtbar, wenn
`data.optimized` in der Antwort vorhanden ist:

```html
<div id="optimization-comparison" class="metrics" hidden>
  <article><span>Original</span><strong id="co2-original">–</strong></article>
  <article><span>Optimiert</span><strong id="co2-optimized">–</strong></article>
  <article><span title="Geschätzte CO₂-Bilanz für den optimierten Prompt im Vergleich zum originalen Prompt">Finale CO₂e-Bilanz</span><strong id="co2-saving">–</strong></article>
</div>
```

In `render()`: Block einblenden und befüllen, wenn `data.optimized`
existiert — `#co2-original` = `data.sustainability.co2_grams + " g"`,
`#co2-optimized` = `data.optimized.sustainability.co2_grams + " g"`,
`#co2-saving` = die vorzeichenbehaftete prozentuale Differenz
`(optimiert - original) / original * 100`, gerundet, mit führendem `+` bei
positivem Wert (mehr CO₂e, rot über die bestehende `.red`-Klasse) bzw. negativ
angezeigt bei weniger CO₂e (grün über `.green`) — Division durch Null abgefangen
(→ `–`, keine Farbklasse). Ein `title`-Tooltip an der Kachelbeschriftung
erklärt kurz, was die Zahl bedeutet. Bei fehlendem `data.optimized` bleibt der
Block versteckt (nicht entfernt), passend zum bestehenden Muster vorbefüllter
Leerzustands-Markup (z. B. startet `#model` mit "Noch keine Analyse"). Das ist
der konkrete Mechanismus, der den CO₂-Effekt einer akzeptierten Optimierung
für den Nutzer sichtbar macht (siehe Kontext-Abschnitt) — in beide Richtungen,
nicht nur als Verbesserung.

Ebenfalls ergänzt: `title`-Tooltips an den Kachelbeschriftungen "CO₂e" und
"Wasser / ADPe" im `.metrics`-Grid, die kurz erklären, wofür die Abkürzungen
stehen (siehe Glossar) — ohne zusätzliches CSS oder JS, nur natives
Browser-Tooltip über das `title`-Attribut.

---

## 7. Dokumentation `[ERLEDIGT]`

- `README.md`-Hinweiszeile: EcoLogits als Grundlage der Schätzung erwähnen
  (wo verfügbar), die bestehende Formel bleibt Fallback — deutschen Ton und
  den Rest des Satzes unverändert lassen.
- `docs/TECHNISCHE_DOKUMENTATION.md`, Abschnitt "Energie und CO₂": die beiden
  EcoLogits-Modi, die Rangfolge der Konfiguration sowie den Fortbestand der
  linearen Formel als dokumentierten Fallback ergänzen; die Tabellenzeile zu
  den Schätzwert-Services und den Satz zur Testabdeckung entsprechend
  aktualisieren.

---

## 8. Tests `[ERLEDIGT]`

- **Neu `tests/test_ecologits_service.py`** (9 Tests): ruft die echte,
  installierte EcoLogits-Bibliothek direkt auf statt sie zu patchen — reine
  lokale Berechnung, kein Netzwerkzugriff, daher kein Mocking nötig. Deckt ab:
  deaktivierte/fehlende Konfiguration → `(None, None)`; `ecologits_provider`
  gesetzt → `llm_impacts`-Pfad (mit echtem `gpt-3.5-turbo`); nicht gesetzt →
  `compute_llm_impacts`-Pfad; fehlende Parameter → `(None, None)`; unbekannter
  Modellname → `(None, FALLBACK_WARNING)`; unbekannte Zone → fällt automatisch
  auf `"WOR"` zurück und liefert trotzdem ein Ergebnis (siehe §3 — der reine
  Fehlerfall ist mangels erreichbarem `mix is None` nicht separat testbar);
  Rangfolge Provider > Katalog sowie Katalog > globale Konfiguration je über
  einen Vergleich zweier Energiewerte.
- **`tests/test_services.py`**: `test_co2` bleibt unverändert (testet weiterhin
  direkt die reale Fallback-Formel, die nicht gelöscht wird). Zusätzlich ein
  günstiger Regressionstest, dass `MODELS`-Einträge die neuen Eco-Schlüssel
  tragen.
- **`tests/test_routes.py`** (5 neue Tests): `/api/analyze` liefert weiterhin
  ein gültiges `sustainability`-Dict bei deaktiviertem EcoLogits (kein Absturz,
  kein fehlender Schlüssel); `/api/send` befüllt `UsageLog.estimated_co2_grams`
  aus einer echten (nicht gepatchten) EcoLogits-Berechnung für einen Ollama-
  Provider mit gesetzten `eco_active_params_b`/`eco_total_params_b`, und
  belässt es bei `0`, wenn EcoLogits deaktiviert ist.
  **⚠️ ÜBERHOLT:** die ursprünglich hier beschriebenen zwei Tests zum
  `optimized`-Vergleich (`test_analyze_returns_optimized_comparison_when_prompt_differs`,
  `test_analyze_omits_optimized_when_prompt_unchanged`) wurden durch einen
  einzigen Regressionstest ersetzt (`test_analyze_never_returns_optimized_comparison`
  in `tests/test_routes.py`), der bestätigt, dass der Schlüssel `optimized`
  nie mehr auftaucht, siehe [`CARBON_FOOTPRINT_REDESIGN.md`](CARBON_FOOTPRINT_REDESIGN.md).
- **`tests/conftest.py`**: die neuen `ECOLOGITS_*`-Schlüssel in `TestConfig`
  ergänzen, damit Zugriffe auf `current_app.config[...]` in Tests, die den
  Service nicht explizit patchen, keinen `KeyError` auslösen.

---

## 9. Verifikation `[ERLEDIGT]`

Tatsächlich durchgeführt (mit einer Abweichung vom ursprünglichen Plan: in der
Umgebung standen weder `chromium-cli`, `node` noch Python-`playwright` zur
Verfügung, echte Browser-Interaktion war daher nicht möglich, ohne selbst eine
neue Abhängigkeit zu installieren. Stattdessen wurde der Flask-Dev-Server
gestartet und per `curl` über echtes HTTP angesprochen — inkl. eines echten,
lokal laufenden Ollama, nicht gemockt):

1. `pip install -r requirements.txt` im venv; `import ecologits` bestätigt (Version 0.11.1, Python 3.14 venv, keine Konflikte).
2. `pytest` — 35 Tests grün (20 bestehende + 15 neue).
3. Flask-Dev-Server gegen die bestehende `instance/gateway.db` gestartet;
   kein Absturz beim Start; `curl` gegen `/` und `/settings/providers` bestätigt,
   dass alle neuen HTML-Elemente (`#energy`, `#water`, `#adpe`,
   `#optimization-comparison`, `#eco-provider` usw.) im gerenderten Markup
   vorhanden sind und beide JS-Dateien mit korrektem MIME-Type ausgeliefert werden.
4. Settings-UI-Rücklese-Verhalten wird durch `serialize_provider()`/`edit()`
   im Code sichergestellt; nicht separat per Browser-Klick verifiziert (siehe
   Einschränkung oben) — client-seitiges JavaScript selbst wurde nicht in
   einem echten Browser ausgeführt.
5. `POST /api/analyze` per `curl` gegen den echten Server (mit echtem, lokal
   laufendem Ollama) ausgeführt: Antwort enthält `sustainability` mit
   `energy_kwh` (damaliger Feldname, seither `energy_wh`), `co2_grams`,
   `water_liters` (damaliger Feldname, seither `water_ml`, siehe
   `CARBON_FOOTPRINT_REDESIGN.md`), `adpe_ug_sb_eq` — alle
   ungleich Null (`mode: "compute_llm_impacts"`).
6. Derselbe Testlauf lieferte einen von Ollama tatsächlich abweichenden
   `optimized_prompt` — die Antwort enthielt den `optimized`-Schlüssel mit
   eigenen `sustainability`-Werten. Dabei zeigte sich der in §4 beschriebene
   Befund: der optimierte Prompt war in diesem konkreten Fall länger (100 statt
   42 Token), die CO₂-Zahl entsprechend höher (0,0396 g statt 0,0169 g) — die
   Heuristik und das Vergleichs-Widget verhalten sich also nachweislich korrekt
   in beide Richtungen, nicht nur im (erwarteten) Kürzer-ist-besser-Fall.
7. `/api/send` und `UsageLog.estimated_co2_grams` wurden bewusst **nicht** gegen
   die echte, persistente `instance/gateway.db` verifiziert, um deren
   tatsächliche Daten nicht mit einem Test-Provider zu verunreinigen. Stattdessen
   deckt `tests/test_send_populates_estimated_co2_grams` (isolierte In-Memory-DB
   über die `app`-Fixture) denselben Pfad automatisiert ab: reale
   EcoLogits-Berechnung, `UsageLog.estimated_co2_grams > 0`,
   `GET /api/usage/summary` würde entsprechend eine Summe ungleich Null melden.
8. `ECOLOGITS_ENABLED=false` in der Testkonfiguration bestätigt sauberen
   Fallback (`test_analyze_falls_back_when_ecologits_disabled`,
   `test_send_co2_zero_when_ecologits_unavailable`) — keine Fehler, `sustainability`
   ist `None`/Fallback-Formel je nach Pfad, `estimated_co2_grams` bleibt `0`.

### Zentrale Dateien
- `app/services/ecologits_service.py` (neu)
- `app/routes/api.py`
- `app/models.py`
- `app/extensions.py`
- `app/services/model_catalog.py`
- `app/services/cost_service.py`
- `config.py` / `.env.example`
- `app/templates/providers.html` / `app/static/js/providers.js`
- `app/templates/dashboard.html` / `app/static/js/dashboard.js`
- `tests/test_ecologits_service.py` (neu), `tests/test_routes.py`,
  `tests/test_services.py`, `tests/conftest.py`

---

## 10. Folgeanpassung: Stromkosten für lokale Modelle

> **⚠️ ÜBERHOLT — entfernt.** Die "Stromkosten"-Kachel und die zugehörige
> `estimate_electricity_cost`-Berechnung wurden wieder entfernt. Der hier
> angekündigte spätere Ersatz über CodeCarbon wurde **ebenfalls nicht
> umgesetzt** — CodeCarbon liefert auf der tatsächlichen Zielhardware (Windows,
> AMD, keine GPU) selbst keine echte Messung, sondern nur einen TDP-Schätzwert,
> und wurde deshalb zugunsten einer eigenen, leichtgewichtigen `psutil`-Formel
> verworfen (siehe [`CARBON_FOOTPRINT_REDESIGN.md`](CARBON_FOOTPRINT_REDESIGN.md),
> Nachtrag 24). Eine "Stromkosten"-Kachel auf Basis dieser Formel ist Stand
> jetzt nur ein unentschiedener Backlog-Punkt, kein aktiver Plan. Als
> historische Aufzeichnung belassen, nicht mehr im Code aktiv.

Aus einem manuellen Testlauf ergab sich eine weitere Beobachtung: Die "Kosten"-Kachel
zeigt bei lokalen Ollama-Modellen immer `0 €`, da `model_catalog.py` deren
`input_cost`/`output_cost` bewusst auf `0` setzt (kein API-Preis). Das ist korrekt für
den *Anbieterpreis*, verschleiert aber, dass lokale Inferenz realen Strom verbraucht —
und dank EcoLogits steht der geschätzte Energieverbrauch (`energy_kwh`) bereits zur
Verfügung.

Entscheidung (zwei Optionen abgewogen, siehe Konversation): eine **eigenständige**
Kachel/Kennzahl statt die bestehende "Kosten"-Kachel zu überschreiben, damit
"Anbieterpreis" und "geschätzte Stromkosten" nicht unter einem Label vermischt werden.

- Neue Konfiguration `ELECTRICITY_PRICE_EUR_PER_KWH` (Default `0.35`, grober
  Richtwert für einen deutschen Haushaltsstrompreis; global, nicht pro Provider/Region
  — bewusst einfach gehalten, wie auch `CARBON_INTENSITY_G_PER_KWH`).
- `cost_service.estimate_electricity_cost(energy_kwh, price_eur_per_kwh)` — reine
  Funktion, ein Einzeiler.
- `sustainability_for()` in `app/routes/api.py` berechnet `electricity_cost_eur` aus
  `energy_kwh` (egal ob EcoLogits- oder Fallback-Pfad, beide liefern `energy_kwh`),
  damit sowohl Original- als auch optimierter Prompt die Kennzahl tragen. `send()`
  ergänzt sie nur, wenn EcoLogits tatsächlich ein Ergebnis liefert (kein erfundener
  Wert für reale Versände, gleiches Prinzip wie bei `estimated_co2_grams`).
  **Wichtig, siehe §11: seit der Nachbesserung wird der Wert nur noch bei lokalen
  Modellen gesetzt, sonst `null`** — die ursprüngliche Version dieses Abschnitts
  berechnete ihn fälschlich für alle Modelle.
- Dashboard: neue Kachel "Stromkosten" neben "Kosten", mit Tooltip, der den
  Unterschied zum Anbieterpreis erklärt.

---

## 11. Korrekturen aus Anwender-Review `[ERLEDIGT]`

Ein manueller Test mit einem echten Prompt ("Wie viele Bäume muss ich pflanzen...")
und eine gezielte Nachfrage zur Korrektheit deckten drei reale Probleme auf:

**a) ADPe-Rohwert ungerundet und in falscher Größenordnung fürs Dashboard.**
`adpe_kg_sb_eq` war das einzige Feld in `_to_impacts_dict()`, das nicht gerundet
wurde (Kopierfehler beim ursprünglichen Schreiben der Funktion — `energy_kwh`,
`co2_grams`, `water_liters` wurden alle gerundet, dieses Feld nicht). Bei
typischen Werten um 1e-10 bis 1e-11 kg rendert JavaScript das ungerundet als rohe
wissenschaftliche Notation (`3.85e-11 kg Sb-Äq.` statt einer lesbaren Zahl) — real
reproduziert und verifiziert, kein hypothetisches Risiko. Behoben durch
Einheitswechsel auf Mikrogramm (`× 1e9`, gerundet auf 4 Nachkommastellen) und
Umbenennung des Felds zu `adpe_ug_sb_eq` (Einheit im Feldnamen, wie bei den
anderen drei Kennzahlen). Regressionstest: `test_adpe_is_in_readable_microgram_range`.

**b) Stromkosten wurden für alle Modelle berechnet, nicht nur lokale.** Der
Anbieterpreis ("Kosten") bei Cloud-/EU-Modellen deckt bereits deren (meist
günstigere, industrielle) Stromkosten ab — eine zusätzliche, mit dem
Haushaltsstrompreis geschätzte "Stromkosten"-Zahl daneben hätte einen Betrag
suggeriert, den der Nutzer bei Cloud-Nutzung gar nicht selbst zahlt. Behoben:
`sustainability_for()` und `send()` setzen `electricity_cost_eur` jetzt nur noch,
wenn `model["hosting_region"] == "Lokal"` (Katalogpfad) bzw.
`provider.provider_type == "ollama"` (echter Provider, dasselbe Signal wie
bereits in `validate_provider_url`s `allow_localhost`-Prüfung verwendet) — sonst
`None`. Frontend zeigt in diesem Fall "– (nur lokal)" statt eines Betrags.
Tests: `test_electricity_cost_shown_for_local_recommendation`,
`test_electricity_cost_hidden_for_cloud_recommendation`.

**c) Eine reale Beispielrechnung wurde Zahl für Zahl nachvollzogen und bestätigt**
(19 vs. 41 Prompt-Token, Modellwahl, Ausgabe-Token-Heuristik, EcoLogits-Formel) —
siehe die Konversation für die vollständige Herleitung. Ergebnis: die Implementierung
rechnet korrekt; ein vom Nutzer gemeldeter scheinbarer Widerspruch (0,168 g vs.
0,0168 g) erwies sich als Zahlendreher beim Ablesen, nicht als Fehler im Code.

## 12. Bekannte methodische Grenzen (nicht behoben, bewusst dokumentiert) `[TODO]`

Bei der Fehlersuche zu (b) wurde der EcoLogits-Quellcode
(`ecologits/impacts/llm.py`) direkt gelesen, nicht nur die Dokumentation. Dabei
zeigten sich zwei substanzielle Annahmen, die die Genauigkeit für **lokale**
Modelle einschränken — beide bewusst nicht behoben, weil sie Kalibrierungs-
entscheidungen erfordern, die eine eigene Abstimmung verdienen, keinen
Schnellschuss:

- **Cloud-Rechenzentrums-Annahmen im manuellen Pfad.** `compute_llm_impacts()`
  legt standardmäßig `BATCH_SIZE=64`, `SERVER_GPUS=8`, `GPU_MEMORY=80GB` zugrunde
  — ein Modell für einen 8-GPU-Cloud-Server, der 64 Anfragen gleichzeitig
  bündelt. Ein einzelner Nutzer mit lokalem Ollama hat effektiv `batch_size=1`,
  keine Bündelung. Da die GPU-Energie pro Token von `batch_size` abhängt,
  dürften unsere lokalen CO₂-/Energiewerte dadurch systematisch zu niedrig
  ausfallen. `compute_llm_impacts()` erlaubt, diese Werte per Keyword-Argument
  zu überschreiben — `_compute_via_manual_parameters()` tut das aktuell nicht.
  Eine Behebung würde die tatsächlichen Zahlen für lokale Modelle spürbar
  verändern (vermutlich erhöhen) und sollte nicht ohne Abstimmung über
  plausible lokale Ersatzwerte umgesetzt werden.
- **`request_latency` im Vorab-Schätzpfad beeinflusst das Ergebnis über einen
  ungetesteten Umweg.** Verifiziert im Quellcode: intern gilt
  `generation_latency = min(request_latency, <physikalisch berechnete Latenz>)`,
  und `generation_latency` fließt sowohl in den Server-Energieanteil als auch in
  die Herstellungs-Anteil-Umlage ein. `analysis_payload()` übergibt dafür
  `duration["max_seconds"]` — unsere eigene, EcoLogits-unabhängige
  Dauer-Heuristik. Numerisch verifiziert: bei einem Beispiel lieferte
  `request_latency=None` (unbeschränkt) 1,707e-05 kgCO2eq, unsere Heuristik
  (20,1 s) 1,680e-05 (≈1,6 % weniger) — bei einer hypothetisch niedrigeren
  Heuristik-Schätzung (0,5 s) fast die Hälfte. Für `send()` (reale gemessene
  Latenz) ist das Verhalten korrekt und beabsichtigt; für den Vorab-Pfad ist es
  eine unbeabsichtigte Wechselwirkung zwischen zwei unabhängig entworfenen
  Schätzungen.
- Kleinere, nicht separat verifizierte Beobachtung: `ECOLOGITS_DEFAULT_DATACENTER_PUE`
  (Default `1,2`) wird unverändert auch auf lokale Modelle angewendet — PUE
  bildet eigentlich Rechenzentrums-Kühlung/-Verteilverluste ab, kein Konzept,
  das eins-zu-eins auf einen privaten PC passt.

---

## Glossar

| Begriff | Bedeutung |
|---|---|
| **CO₂e / GWP** | Global Warming Potential — Klimawirkung ausgedrückt als CO₂-Äquivalent in Gramm/kg (`kgCO2eq`). Das, was die bestehende "CO₂e"-Kachel zeigt. |
| **ADPe** | Abiotic Depletion Potential (elements) — Verbrauch knapper mineralischer/metallischer Ressourcen (z. B. Seltene Erden in Chips), in `kg Sb-eq` (Antimon-Äquivalent), eine gängige Ökobilanz-Einheit (LCA, Life-Cycle Assessment). |
| **PE** | Primary Energy — gesamte, der Natur entnommene Rohenergie (in MJ), inklusive Erzeugungs-/Umwandlungsverluste; umfassender als der bereits gezeigte `kWh`-Wert (Strom an der Steckdose). |
| **WCF / Wasser** | Water Consumption Footprint — vom Rechenzentrum verbrauchtes (nicht nur entnommenes) Wasser in Litern, getrieben durch `WUE`. |
| **PUE** | Power Usage Effectiveness — Overhead-Verhältnis des Rechenzentrums (Gesamtenergie der Anlage ÷ Energie der IT-Ausrüstung); `1,0` = kein Overhead, reale Rechenzentren liegen meist bei `1,1`–`1,6`. |
| **WUE** | Water Usage Effectiveness — Liter Wasser je kWh IT-Energie, analog zu PUE, aber für Wasser (stark abhängig von Kühltechnik und Klima). |
| **Nutzungsphase vs. Herstellungsphase** | EcoLogits trennt Wirkungen in *Nutzung* (Strom/Wasser während der Anfrage) und *Herstellung* (anteiliger Herstellungsaufwand der Hardware). Beide fließen in die angezeigten Summen ein. |
| **Strommix-Zone** | ISO-3166-1-alpha-3-Länder-/Regionscode (z. B. `DEU`, `FRA`, `USA`, oder `WOR` für den Weltdurchschnitt), über den nachgeschlagen wird, wie CO₂-/wasser-/ressourcenintensiv das lokale Stromnetz ist. |
| **Aktive vs. Gesamt-Parameteranzahl** | Bei Mixture-of-Experts-Modellen (MoE) ist "aktiv" die Teilmenge der Parameter, die pro Token tatsächlich berechnet wird; "gesamt" die volle Modellgröße. Bei dichten Modellen sind beide gleich. EcoLogits' Formeln nutzen beide Werte. |
| **`llm_impacts()` vs. `compute_llm_impacts()`** | Die beiden EcoLogits-Einstiegspunkte dieser Integration — siehe Abschnitt "SDK-Anbindung vs. rohe requests": Ersterer sucht ein bekanntes Anbietermodell über den Namen, Letzterer nimmt Parameteranzahlen und Rechenzentrumsfaktoren direkt entgegen. |
