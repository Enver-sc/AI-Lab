# Neukonzeption Nachhaltigkeits-Schätzung — Sustainable AI Gateway

> Status (zuletzt aktualisiert nach Nachtrag 34): **inhaltlich abgeschlossen.**
> Alter Prompt-Vergleich entfernt, Live-Versand-Schätzung
> (`/api/estimate-footprint`, inkl. Formel-Fallback bei unvollständiger
> Provider-Konfiguration) sowie die bildhafte Darstellung (Icons, Aktivitäts-
> ringe, Tassen-Segmente, Tasse-Tee-Referenz) sind vollständig gebaut und live
> verifiziert. **CodeCarbon wurde nicht umgesetzt** — auf der Zielhardware
> (Windows, AMD, keine GPU) liefert es selbst keine echte Messung, sondern nur
> einen TDP-Schätzwert (siehe Nachtrag 24); ersetzt durch eine eigene,
> leichtgewichtige `psutil`-Formel für den lokalen Ollama-Sendefall, und eine
> lokale Analyse-Fußabdruck-Kachel wurde bewusst komplett verworfen (Nachtrag 31,
> "Information Overload"). Die `RATIO`-Kalibrierung ist als `flask
> calibrate-ratio`-CLI-Kommando umgesetzt (Nachtrag 32). Verbleibend offen sind
> nur noch drei nicht-EcoLogits-spezifische Punkte (Prompt-Flow-UX,
> Fehlermeldungen) — siehe Checkliste am Ende. Was zusätzlich läuft, steht in
> [`ECOLOGITS_INTEGRATION.md`](ECOLOGITS_INTEGRATION.md) (Status: umgesetzt,
> mit ÜBERHOLT-Hinweisen an den durch dieses Dokument ersetzten Stellen).

## Kontext

Die erste Integrationsrunde (siehe `ECOLOGITS_INTEGRATION.md`) hat EcoLogits für
Energie-/CO₂-/Wasser-/Ressourcenschätzung eingeführt und zusätzlich einen
Vorher/Nachher-Vergleich zwischen Original- und optimiertem Prompt gebaut, um
Nutzer für den CO₂-Fußabdruck zu sensibilisieren (§4/§6 dort). Ein Anwender-Review
hat einen strukturellen Konstruktionsfehler in genau diesem Vergleich aufgedeckt,
der eine Neukonzeption statt einer weiteren Korrektur rechtfertigt.

**Bezug zur bestehenden Team-Analyse**: `docs/carbon_tool_eval.md` (manuelle
Analyse CodeCarbon vs. EcoLogits) kommt unabhängig zum selben Schluss, auf dem
dieses Dokument aufbaut — CodeCarbon für reale Messung des lokalen
Analyseschritts ("System-Selbstbewertung"), EcoLogits für die Schätzung der
eigentlichen LLM-Anfrage ("Nutzer-Sensibilisierung"). Die dortige Tabelle in
Abschnitt 4 und das Fazit in Abschnitt 6 sind die Grundlage für die
Aufgabenteilung "Analyse-Fußabdruck" vs. "Versand-Schätzung" weiter unten.
**Update**: Die CodeCarbon-Empfehlung aus `carbon_tool_eval.md` wurde später,
nach konkreter Prüfung an der tatsächlichen Zielhardware, nicht umgesetzt —
siehe Nachtrag 24/31 und die Statuszeile oben. `carbon_tool_eval.md` selbst
bleibt unverändert als historische Analyse stehen.

## Finding: der Vorher/Nachher-Vergleich ist strukturell verzerrt

Der `SYSTEM_PROMPT` der Ollama-Analyse (`analysis_service.py`) optimiert Prompts
auf **Klarheit und Präzision**, nicht auf **Kürze**. In allen bisher beobachteten
Beispielen wurde der "optimierte" Prompt dadurch *länger*, nicht kürzer (19→41
Token, 42→100 Token) — das ist der beabsichtigte Zweck des Optimierers, kein
Zufall. Da unsere bisherige Heuristik die erwartete Ausgabelänge proportional zur
Eingabe-Tokenanzahl skaliert (`output_opt = output × tokens_opt / tokens`), führt
das nahezu immer zu einem *höheren* CO₂-Wert für den optimierten Prompt.

Die Konsequenz: die "Finale CO₂e-Bilanz"-Kachel zeigt strukturell fast immer ein
Minus — unabhängig davon, ob der Nutzer tatsächlich ineffizient formuliert hat.
Für das Ziel der Sensibilisierung ist das kontraproduktiv: die Botschaft würde
lauten "Optimierung = schlechter fürs Klima", was weder stimmt noch beabsichtigt
ist. Eine weitere kosmetische Korrektur (wie die Umbenennung zu "Bilanz" in der
Vorrunde) behebt nur die Anzeige, nicht die falsche Prämisse dahinter.

## Zielarchitektur: zwei getrennte, jeweils ehrliche Kennzahlen

Statt einen einzelnen (strukturell verzerrten) Vergleichswert zu zeigen, trennen
wir zwei tatsächlich unterschiedliche Dinge, die bisher unter einer Kennzahl
vermischt wurden:

1. **Analyse-Fußabdruck** — real gemessen, für den lokalen Ollama-Analyseschritt,
   der für jeden Prompt ohnehin passiert (Compliance-/Komplexitäts-Scoring,
   Optimierungsvorschlag). Das ist ein bereits eingetretenes, messbares Ereignis.
2. **Voraussichtlicher Versand-Fußabdruck** — EcoLogits-Schätzung, aber live an
   das tatsächliche Sendefeld gekoppelt statt als statischer Vergleich gegen
   Ollamas Vorschlag. Das ist ein noch nicht eingetretenes, notwendig geschätztes
   Ereignis.

### 1. Analyse-Fußabdruck via CodeCarbon `[ÜBERHOLT]`

> ⚠️ **ÜBERHOLT (siehe Nachtrag 24 und Nachtrag 31)**: Dieser gesamte
> Abschnitt beschreibt den ursprünglichen Plan, bleibt aber als historische
> Aufzeichnung stehen (nicht gelöscht). Tatsächlich umgesetzt wurde etwas
> anderes: CodeCarbon wurde verworfen, weil es auf der tatsächlichen
> Zielhardware (Windows, AMD, keine GPU) selbst keine echte Messung liefert,
> sondern nur denselben TDP-Schätzwert, den man auch selbst leichtgewichtig
> berechnen kann (Nachtrag 24) — ersetzt durch eine eigene `psutil`-CPU-
> Auslastungsformel (`app/services/local_energy_service.py`), aber nur für
> den tatsächlichen **Sendefall** (`/api/send`), nicht für den Analyseschritt.
> Eine eigene Kachel/Anzeige für den lokalen Analyse-Fußabdruck (in welcher
> Form auch immer, real gemessen oder per Formel) wurde zusätzlich explizit
> geprüft und verworfen (Nachtrag 31) — unabhängig vom Zielmodus sichtbar,
> misst das falsche Modell/den falschen Workload und hilft der eigentlichen
> Sende-Entscheidung nicht. Es gibt also **keinen** Analyse-Fußabdruck am
> Dashboard, weder via CodeCarbon noch via eigener Formel.

**Warum CodeCarbon statt EcoLogits für diesen Teil**: EcoLogits' `compute_llm_impacts()`
modelliert einen Cloud-Rechenzentrums-Server (Batching von 64 gleichzeitigen
Anfragen, 8-GPU-Server — siehe `ECOLOGITS_INTEGRATION.md` §12, bekannte
Einschränkung). Für einen einzelnen lokalen Ollama-Prozess passt das nicht.
CodeCarbon misst stattdessen den *tatsächlichen* Energieverbrauch der Maschine,
auf der es läuft (RAPL unter Linux, Intel Power Gadget unter Windows, TDP-basierter
Fallback wenn keins davon verfügbar ist) — kein Modell fremder Hardware, sondern
(so weit die Hardware es hergibt) eine echte Messung der eigenen.

**Sicherheits-Constraint, verifiziert am tatsächlichen Quellcode des installierten
Pakets (nicht nur an der Dokumentation)**:

- `EmissionsTracker` (die Standard-"Online"-Klasse) ruft bei jedem Start
  automatisch `requests.get(geo_js_url, timeout=0.5)` auf, um die öffentliche
  IP-basierte Geolokalisierung über einen externen Dienst (`geojs`) aufzulösen —
  das widerspricht direkt dem Projektgrundsatz "keine automatische externe
  Übertragung" (`AGENTS.md`).
- `OfflineEmissionsTracker` macht **keinen** Netzwerkaufruf für die
  Geolokalisierung — sie liest ausschließlich aus einer lokal mitgelieferten
  Datei (`global_energy_mix.json`), anhand eines explizit übergebenen
  `country_iso_code`.
- Emissions-Reporting an die zentrale CodeCarbon-API (`CodeCarbonAPIOutput`,
  `requests.post(...)`) ist unabhängig davon **standardmäßig deaktiviert**
  (`save_to_api` defaultet auf `False`, Standard-Output ist nur eine lokale CSV).

**Daraus folgende bindende Regeln für die Implementierung**:

1. **Ausschließlich `OfflineEmissionsTracker` importieren, nie `EmissionsTracker`.**
   Kein Konfigurationsschalter, sondern eine Code-Entscheidung — sollte durch
   einen Test abgesichert werden, der sicherstellt, dass `EmissionsTracker` nirgends
   im Projekt importiert wird.
2. **`country_iso_code` immer explizit setzen**, passend zur bestehenden
   `ECOLOGITS_ELECTRICITY_MIX_ZONE`-Konfiguration (z. B. `"DEU"`) — ohne diesen
   Parameter kann `OfflineEmissionsTracker` die Netzdaten nicht auflösen.
3. **`output_methods`/`save_to_api` nie setzen** — der Default (kein API-Output)
   ist bereits das gewünschte Verhalten; hier ist Unterlassen die Regel.

**Einsatzort im Code** (Zielbild aus dem ursprünglichen Plan, nie gebaut —
siehe ÜBERHOLT-Hinweis oben): `analysis_service.analyze_with_ollama()`
wird mit einem `OfflineEmissionsTracker`-Context-Manager umschlossen; das
Ergebnis (Energie, CO₂e) fließt als neuer Wert `analysis_footprint` in die
`/api/analyze`-Antwort, getrennt von `sustainability` (das bleibt für den
Versand-Fußabdruck reserviert).

**Offene Punkte für die Implementierung** (nicht heute zu klären):
- Genaues Feld-Mapping der CodeCarbon-Rückgabe (`EmissionsData`-Objekt) auf unser
  bestehendes `{"energy_wh":..., "co2_grams":...}`-Schema.
- Neue Abhängigkeit `codecarbon` in `requirements.txt` — wie beim
  `ecologits`-Onboarding zunächst nur `requirements.txt` ergänzen und lokal
  installieren lassen, bevor Code geschrieben wird (gleiches Vorgehen wie beim
  ersten EcoLogits-Onboarding).
- Wie das Frontend den neuen `analysis_footprint`-Wert zeigt (vermutlich eine
  neue, eigene Kachel, klar von der Versand-Schätzung unterschieden).

**Scope-Erweiterung nötig, um die entfernte "Stromkosten"-Kachel zu ersetzen
(siehe unten).** Aktuell ist CodeCarbon hier nur für den Analyseschritt
vorgesehen (`analyze_with_ollama()`). Die entfernte "Stromkosten"-Kachel hing
aber am **Versand**-Fußabdruck (`energy_wh` aus der Vorab-Schätzung bzw. dem
tatsächlichen lokalen Sendevorgang) — einem anderen, separaten Ollama-Aufruf im
Code. Damit ein künftiger CodeCarbon-basierter Stromkosten-Ersatz diese Lücke
wirklich schließt, müsste der Anwendungsbereich explizit auf den tatsächlichen
lokalen Inferenz-/Sendeaufruf erweitert werden, nicht nur die Analyse — das ist
hier bewusst als offener Punkt festgehalten, keine stille Annahme.

**Aussagekräftige Kachel-Beschriftung, wenn der Ersatz gebaut wird.** Falls
CodeCarbon am Ende sowohl Analyse- als auch Versand-Stromkosten misst, entstehen
möglicherweise **zwei** unterschiedliche Stromkosten-Zahlen (Analyseschritt vs.
tatsächliche Inferenz). Die Kachel(n) müssen dann so benannt sein, dass für den
Anwender eindeutig ist, welche der beiden gemeint ist — "Stromkosten" allein
(wie in der jetzt entfernten Kachel) wäre dafür zu unspezifisch. Konkrete
Benennung ist nicht heute zu entscheiden, nur als Anforderung für die spätere
Umsetzung festgehalten.

### 2. Versand-Schätzung: live statt statischer Vergleich

**Entfernung des alten Vergleichs: `[ERLEDIGT]`.** **Live-Ersatz (Server-Funktion, siehe unten): `[ERLEDIGT]`** — `/api/estimate-footprint` ist vollständig gebaut, siehe "Entscheidung getroffen und umgesetzt" weiter unten.

Die bisherige "Original vs. optimiert"-Logik (`optimized_payload()` in
`app/routes/api.py`, das `#optimization-comparison`-Widget in
`dashboard.html`/`dashboard.js`) ist entfernt — `optimized_payload()` gelöscht,
`analysis_payload()` hängt keinen `"optimized"`-Schlüssel mehr an, das Widget
samt `renderOptimizationComparison()` ist aus Template/JS entfernt. Der reine
Formulierungsvorschlag (`analysis.optimized_prompt`, die Vorschlagsliste, der
"Optimierten Prompt verwenden"-Button) bleibt unverändert bestehen — nur die
CO₂-Vergleichszahlen sind weg. `ECOLOGITS_INTEGRATION.md` §4/§6/§8 sind
entsprechend mit "ÜBERHOLT"-Hinweisen markiert (Inhalt bleibt als historische
Aufzeichnung stehen). Regressionstest: `test_analyze_never_returns_optimized_comparison`
in `tests/test_routes.py`.

**Damals noch offen, inzwischen erledigt**: der Live-gekoppelte Ersatz
(`/api/estimate-footprint`) ist seit "Entscheidung getroffen und umgesetzt"
weiter unten vollständig gebaut, inklusive Formel-Fallback bei
unvollständiger Provider-Konfiguration (Nachtrag 25). Der hier beschriebene
Zwischenzustand (nur die Vorab-Schätzung aus `/api/analyze`, keine
Live-Aktualisierung) ist nicht mehr aktuell.

**Neues Verhalten**: die EcoLogits-Schätzung bezieht sich nur noch auf den
**aktuellen Inhalt des Textfelds, das tatsächlich gesendet würde** — ob das der
Original-Prompt, Ollamas Vorschlag unverändert, oder eine eigene Bearbeitung davon
ist, spielt keine Rolle mehr für die Berechnungslogik. Der Nutzer bearbeitet den
Text im `#optimized`-Textfeld, die Schätzung aktualisiert sich mit — ohne
Bewertung "besser/schlechter als das Original", nur eine ehrliche Zahl für das,
was gerade dasteht.

**Warum das die Sensibilisierung eher stärkt als der alte Vergleich**: es macht aus
einer (strukturell fast immer negativen) KI-Bewertung ein interaktives Werkzeug —
der Nutzer kürzt/ändert selbst und beobachtet die Wirkung in Echtzeit, statt eine
fixe, oft demotivierende Bewertung gegen einen Vorschlag zu sehen, den er nicht
beeinflusst hat.

### Das technische Kernproblem: woran soll sich eine Live-Zahl überhaupt bewegen?

EcoLogits' Formel hängt ausschließlich von der **Ausgabe**-Tokenanzahl ab, nicht
vom Eingabetext (siehe `ECOLOGITS_INTEGRATION.md` §3/§4). Ohne Bezugspunkt würde
eine Live-Zahl beim Tippen also einfach nicht reagieren — der bisherige Bezug
("relativ zu Ollamas Vorschlag") entfällt mit der neuen Architektur.

**Lösung**: eine *absolute* statt einer *relativen* Heuristik — die erwartete
Ausgabelänge wird direkt proportional zur aktuellen Eingabelänge geschätzt
(`erwartete_ausgabe ≈ RATIO × aktuelle_eingabe_token`), statt eines fixen
globalen Werts (vormals `DEFAULT_EXPECTED_OUTPUT_TOKENS`) oder eines Vergleichs
zu einem anderen Text. Jede Texteingabe hat dann automatisch einen plausiblen,
sich bewegenden Bezugspunkt — unabhängig von jeder Vergleichslogik.

**Teilweise vorgezogen umgesetzt `[ERLEDIGT für `/api/analyze`]`**: Im Zuge des
Findings "Kacheln zeigen veraltete Werte nach Prompt-Optimierung" (siehe unten)
hat sich gezeigt, dass die feste Konstante das eigentliche Problem war — auch
ganz ohne Live-Endpunkt: eine erneute `/api/analyze`-Analyse des optimierten
(längeren) Prompts lieferte identische EcoLogits-Kacheln, weil beide Durchläufe
denselben fixen `output`-Wert verwendeten. Deshalb wurde genau diese
proportionale Heuristik bereits **direkt in `analysis_payload()`**
(`app/routes/api.py`) vorgezogen, unabhängig vom noch unentschiedenen
`/api/estimate-footprint`-Endpunkt weiter unten: `EXPECTED_OUTPUT_RATIO`
(neue Config, `.env.example`, Default `6`) ersetzt `DEFAULT_EXPECTED_OUTPUT_TOKENS`
vollständig; `output = max(1, round(tokens * EXPECTED_OUTPUT_RATIO))`. Der
`RATIO`-Wert ist weiterhin ein **nicht kalibrierter Platzhalter** (keine
`UsageLog`-Daten vorhanden, siehe Checkliste) — die Kalibrierungsaufgabe bleibt
offen, gilt jetzt aber für einen bereits produktiv genutzten Wert, nicht mehr
nur für ein zukünftiges Feature.

### Server-Funktion (kein Client, keine externe LLM-Anfrage)

**Wichtige Klarstellung, die in der Diskussion aufkam**: "Server" bedeutet hier
**unser eigener Flask-Server**, nicht Anthropic oder ein anderes LLM. Weder die
Live-Schätzung noch eine Änderung im Textfeld lösen jemals eine externe Anfrage
aus — das würde den Kerngrundsatz *"Analyse und Versand sind getrennt,
externe Übertragung erfolgt nie automatisch"* verletzen. Ein tatsächlicher
Versand an ein LLM passiert weiterhin ausschließlich über die bestehende,
bewusste "Senden"-Aktion.

> **Update**: `/api/estimate-footprint` existiert inzwischen vollständig, für
> beide hier skizzierten Eingabepfade — genutzt für den "Optimierten Prompt
> verwenden"-Klick (siehe Finding weiter unten, "Option #2") **und** für einen
> neuen "Fußabdruck schätzen"-Button beim Folgeprompt-Feld (`#chat-input`).
> Die beiden Grundsatzentscheidungen darunter (serverseitig/clientseitig,
> "live" beim Tippen) sind getroffen — siehe "Entscheidung getroffen und
> umgesetzt" weiter unten. Echtes Live-Tippen (ohne Klick) wurde bewusst
> **nicht** umgesetzt.

Endpunkt `/api/estimate-footprint` — ruft nur bereits vorhandene, rein lokale
Funktionen auf (`estimate_tokens()`, `ecologits_service.compute_impacts()`),
kein Ollama-Aufruf, kein DB-Schreiben:

**Eingabe, je nach Aufrufkontext:**
- **`#prompt`/`#optimized`** (vor dem Versand, noch kein Provider gewählt):
  `{"text":..., "model_class": "local_small"}` — `model_class` stammt aus
  `recommendation.model_class` der letzten `/api/analyze`-Antwort; der Server
  schlägt nur im bestehenden `MODELS`-Katalog nach (reine Dict-Suche, keine neue
  Ollama-Analyse, keine neue Compliance-Prüfung).
- **`#chat-input`** (Provider bereits aktiv, echte Konversation läuft):
  `{"text":..., "provider_id":..., "model_name":...}` (`model_name` optional,
  nur bei Anthropic mit Modellwahl) — Server lädt den `ProviderConfiguration`-
  Datensatz nur lesend und nutzt dessen echte `ecologits_provider`/
  `eco_active_params_b`-Werte, analog zu `send()` heute, nur ohne Versand.

**Berechnung**: `tokens = estimate_tokens(text)` →
`expected_output_tokens = round(tokens × RATIO)` → `compute_impacts(expected_output_tokens, ...)`.

**Ausgabe**: dieselbe `sustainability`-Struktur wie bei `/api/analyze`/`/api/send`
— `renderSustainabilityTiles()` im Frontend kann unverändert wiederverwendet werden.

**Bewusste Auslassungen**: kein Schreiben in `UsageLog` (würde `/api/usage/summary`
verfälschen), keine Compliance-Neuprüfung (bleibt bei `send()` verankert), CSRF-
Schutz wie bei jedem verändernden Aufruf im Projekt.

### Entscheidung getroffen und umgesetzt `[ERLEDIGT]`

Die beiden zuvor offenen Grundsatzfragen sind entschieden:

1. **Serverseitig vs. clientseitig → serverseitig.** Wie oben beschrieben:
   liefert echte EcoLogits-Genauigkeit statt einer im Frontend duplizierten
   Näherungsformel.
2. **"Live" beim Tippen vs. expliziter Auslöser → expliziter Button.** Kein
   Live-Update und kein Debounce — die `RATIO`-Heuristik ist eine grobe
   Näherung (siehe Kalibrierungspunkt unten), ein bei jedem Tastenanschlag
   "live" reagierender Wert würde eine Genauigkeit suggerieren, die die
   Schätzung nicht hat (dieselbe Art Verfälschung wie das ursprüngliche
   Vergleichsproblem, nur andersherum). Ein expliziter, bewusster Klick ist
   ehrlicher als scheinbare Echtzeit — passt auch zum bestehenden
   Projektgrundsatz "Analyse und Versand sind getrennte, bewusste Aktionen".

**Umsetzung**: `/api/estimate-footprint` wurde um den zweiten, bereits hier
skizzierten Eingabepfad ergänzt — `{"text":..., "provider_id":...,
"model_name":...}`, verarbeitet von der neuen Funktion
`estimate_footprint_for_provider()` (`app/routes/api.py`): lädt die
`ProviderConfiguration` nur lesend, nutzt für Anthropic-Provider dieselbe
Modell-/Preis-Auflösung wie `send()` (`ANTHROPIC_MODELS`, `copy.copy()` für
den EcoLogits-Modellnamen), berechnet Token/Kosten/Sustainability neu — ohne
Versand, ohne `UsageLog`-Eintrag. `request_latency_seconds` ist dabei ein
fester Platzhalter (`ESTIMATE_REQUEST_LATENCY_SECONDS = 2.0`), da für eine
noch nicht gesendete Nachricht keine echte Latenz existiert.

Frontend: neuer Button **"Fußabdruck schätzen"** neben dem Folgeprompt-Feld
(`#chat-input`, `app/static/js/dashboard.js`) — löst `estimateChatFootprint()`
aus, zeigt Ausgabe-Token/Kosten/CO₂e/Indikator für den *gerade eingegebenen,
noch nicht gesendeten* Text in einer eigenen kleinen Vorschauzeile
(`#chat-estimate-result`), getrennt von der kumulierten "Kosten und
Nutzung"-Zusammenfassung, die weiterhin nur tatsächlich versendete Nachrichten
zählt. Schließt damit eine bisher fehlende Lücke: für Folgeprompts gab es
bislang **gar keine** Vorab-Schätzung, nur die Werte nach dem tatsächlichen
Versand.

Cache-Buster auf `v='16'` erhöht. Neue Tests:
`test_estimate_footprint_for_active_provider_returns_sustainability`,
`test_estimate_footprint_rejects_unknown_provider` in `tests/test_routes.py`.
`pytest`: 79/79 grün. Live verifiziert (Server ausgeliefertes JS enthält
`estimateChatFootprint`/`chat-estimate-btn`, `dashboard.js?v=16`).

**Nachtrag 1**: Die erste Fassung der Vorschauzeile zeigte nur Token/Kosten/CO₂e,
nicht Energie/Wasser (Rückmeldung nach dem ersten Live-Test). Ergänzt in
`estimateChatFootprint()` — `v='17'`.

**Nachtrag 2 (Bugfix)**: `continueChat()` leerte nach erfolgreichem Versand
zwar `#chat-input`, nicht aber `#chat-estimate-result` — nach dem Senden blieb
die Schätzung der vorherigen (jetzt bereits versendeten) Nachricht sichtbar
unter dem neuen, leeren Eingabefeld stehen. Fix: `element("#chat-estimate-result").textContent = ""`
ergänzt direkt neben `input.value = ""` in `continueChat()` — `v='18'`.

**Zusätzlich, inzwischen erledigt (Nachtrag 32)**: der `RATIO`-Wert selbst
sollte nicht frei geraten, sondern nach Möglichkeit aus echten, bisherigen
Ollama-Antwortlängen kalibriert werden (z. B. aus geloggten `UsageLog`-Einträgen,
falls `ENABLE_PROMPT_LOGGING` aktiv war) — als grober Startwert vertretbar, aber
explizit vorläufig zu kennzeichnen, bis er kalibriert ist.

**Visuelles Feedback bei Wertänderung `[ERLEDIGT]`**: eine Zahl, die sich
"einfach so" im Hintergrund ändert, wird leicht übersehen. Umgesetzt wurde
letztlich kein isoliertes Aufblitzen/Farbwechsel-Element, sondern der
Ring-/Tassen-Füllstandswechsel bei jeder neuen Analyse (siehe
Aktivitätsring-Abschnitt weiter unten) — deckt denselben Bedarf im Rahmen der
ohnehin gebauten bildhaften Darstellung ab, kein separates
Design-Leitfaden-Projekt nötig.

## Was das für `ECOLOGITS_INTEGRATION.md` bedeutet `[ERLEDIGT]`

§4 ("Vergleich Original- vs. optimierter Prompt"), §6 (Vergleichs-Widget) und
die zugehörige Testbeschreibung in §8 sind dort jetzt mit "⚠️ ÜBERHOLT"-Hinweisen
markiert, Inhalt bleibt als historische Aufzeichnung stehen (nicht gelöscht).
Die übrigen Abschnitte (§1–§3, §5, §7, §9–§12: Abhängigkeit,
Konfigurationsrangfolge, `ecologits_service.py`-Kern, Settings-UI,
Dokumentation, Verifikation, bekannte Grenzen) bleiben unverändert gültig — der
Kern der EcoLogits-Anbindung selbst wurde durch die Entfernung nicht angetastet,
nur die Vergleichslogik obendrauf.

## EcoLogits-Kern: Datenherkunft, Offline-Modus, Provider-Anbindung

Dieser Abschnitt hält fest, wie EcoLogits die Werte für CO₂, Wasser und Energie
tatsächlich ermittelt — als gemeinsame Grundlage, bevor wir am Fallback-Verhalten
weiterarbeiten. Nichts hiervon ändert sich durch die Neukonzeption; es ist der
unverändert gültige Kern aus `ECOLOGITS_INTEGRATION.md` §3, hier noch einmal
explizit für dieses Dokument zusammengefasst.

### Woher die Werte kommen

Zwei lokale Datenquellen, beide als Dateien direkt im installierten
`ecologits`-Paket (`.venv/Lib/site-packages/ecologits/data/`):

1. **`models.json`** — Parameteranzahl und Architektur (dicht vs. Mixture-of-
   Experts) pro Anbieter+Modellname. Beispiel, direkt nachvollzogen: Claude
   Haiku 4.5 ist dort als dichtes Modell mit 10–35 Mrd. Parametern hinterlegt,
   Claude Sonnet 4.6 als MoE-Modell mit 440 Mrd. Gesamt-/44–132 Mrd. aktiven
   Parametern — der Unterschied erklärt den Faktor ~16 zwischen beiden Modellen
   bei gleicher Ausgabelänge (0,02 g vs. 0,33 g CO₂e bei 500 Token).
2. **`electricity_mixes.json`** — GWP-/ADPe-/PE-/WUE-Faktoren pro Zone
   (ISO-3166-1-alpha-3-Code, z. B. `DEU`), inkl. `WOR` als Weltdurchschnitt.

Beide werden beim Import des Pakets geladen (`ModelRepository.from_json()`,
`ElectricityMixRepository.from_json()`) — keine Netzwerkabfrage, weder beim
Anbieter-Lookup-Pfad (`llm_impacts()`) noch beim manuellen Pfad
(`compute_llm_impacts()`).

### Offline bestätigt, nicht nur angenommen

Verifiziert am tatsächlichen Quellcode des installierten Pakets: kein
`requests.*`-Aufruf in `ecologits/tracers/utils.py` oder `ecologits/impacts/llm.py`.
Der einzige Netzwerk-Anknüpfungspunkt in EcoLogits überhaupt ist der
SDK-Patching-Modus (siehe unten) — und den nutzen wir bewusst nicht.

**Wo das konfiguriert ist**: nirgends explizit in unserem eigenen Code — die
Datenbasis ist im gepinnten Paket selbst eingebacken (`requirements.txt`:
`ecologits==0.11.1`). Ein Versions-Update aktualisiert die Datenbasis
automatisch (kann Modelle hinzufügen, aber theoretisch auch umbenennen/entfernen).

### Raw Requests statt SDKs — und was das für EcoLogits bedeutet

Alle drei Provider-Typen im Projekt sprechen ihre Ziel-API über rohe
`requests`-Aufrufe an, nicht über die jeweiligen offiziellen SDK-Pakete
(`openai`, `anthropic`, `cohere`, `google-genai`, `huggingface_hub`, `mistralai`
— echte, separat installierbare Python-Pakete):

| Provider-Typ | Ziel (`base_url`) | Pfade |
|---|---|---|
| Ollama | typischerweise `http://localhost:11434`, lokal | `/api/tags`, `/api/generate` |
| OpenAI-kompatibel | frei konfigurierbar (OpenAI, Azure, Reseller, selbst gehostet) | `/models`, `/chat/completions` |
| Anthropic | im Projekt aktuell `https://api.anthropic.com` (echte Produktions-API) | `/v1/models`, `/v1/messages` |

Das ist **dasselbe Ziel**, das auch das jeweilige offizielle SDK ansprechen würde
— der Unterschied liegt nur im Weg dorthin (selbst gebauter HTTP-Request vs.
SDK-Komfortschicht). Relevant für EcoLogits: dessen **SDK-Patching-Modus**
(`EcoLogits.init(providers=[...])` + offizielles SDK normal benutzen) patcht zur
Laufzeit die SDK-Methoden, um Modellname/Ausgabe-Tokenanzahl/Latenz automatisch
aus einem ohnehin stattfindenden echten API-Call mitzulesen. Das fügt **keinen
zusätzlichen** Netzwerkaufruf hinzu — es braucht aber zwingend einen Aufruf über
eines der genannten SDK-Pakete, um etwas zum Patchen zu haben. Da im Projekt
nirgends `anthropic.Anthropic().messages.create(...)` aufgerufen wird (sondern
`requests.Session().post(...)` in `app/providers/anthropic.py`), ist dieser
Modus für uns **technisch nicht anwendbar** — unabhängig davon, ob wir ihn
wollten. Deshalb ausschließlich der manuelle Modus (`llm_impacts()` /
`compute_llm_impacts()`, siehe `ecologits_service.py`).

## Heutiges Verhalten bei nicht gefundenem Modell (Ist-Zustand)

Konkret nachvollzogen am aktuellen Code (`compute_impacts()` in
`ecologits_service.py`):

1. Ist `ecologits_provider` auf einem Provider-Datensatz gesetzt (bei unserem
   aktuellen Anthropic-Provider: ja), wird **ausschließlich** der
   Anbieter-Lookup-Pfad versucht (`llm_impacts()`).
2. Wird das exakte `model_name` dort nicht gefunden, liefert EcoLogits
   `impacts.has_errors = True` (Fehlercode `model-not-registered`) →
   `compute_impacts()` gibt `(None, FALLBACK_WARNING)` zurück.
3. **Es gibt aktuell keinen automatischen zweiten Versuch** über den manuellen
   Parameter-Pfad (`compute_llm_impacts()`), selbst wenn auf demselben
   Provider-Datensatz zusätzlich `eco_active_params_b`/`eco_total_params_b`
   gepflegt wären. Die Entscheidung Anbieter-Lookup vs. manuell fällt einmalig
   am Anfang von `compute_impacts()`, bevor überhaupt geprüft wird, ob das
   konkrete Modell existiert.

**Auswirkung, je nach Aufrufer:**
- `/api/analyze` (Vorab-Schätzung): `sustainability_for()` führt das `None`-Ergebnis
  mit der alten linearen Fallback-Formel (`sustainability_service.py`) zusammen
  — der Nutzer sieht weiterhin eine Zahl, nur ungenauer, ohne Hinweis, dass es
  sich um die einfache Formel statt EcoLogits handelt.
- `/api/send` (echter Versand): kein Formel-Fallback (bewusste Entscheidung der
  Vorrunde: kein erfundener Wert für reale Versände). `sustainability` wird
  `null`, `estimated_co2_grams` wird `0` in der Datenbank.

Für unsere aktuell konfigurierten Modelle (Haiku, Sonnet) tritt der Fall nicht
ein — beide sind in der EcoLogits-Datenbank vorhanden. Relevant wird es beim
nächsten Modell, das Anthropic (oder ein anderer Anbieter) veröffentlicht, bevor
wir `ecologits` aktualisiert haben.

## Designvorschlag zur späteren Review

**A. Zweistufiger Fallback statt einstufigem. `[ERLEDIGT]`** `compute_impacts()`
fällt jetzt, wenn der Anbieter-Lookup-Pfad kein Ergebnis liefert (Modell nicht
gefunden oder anderer Fehler), automatisch auf den manuellen Parameter-Pfad
zurück — *falls* auf demselben Provider-Datensatz/Katalogeintrag zusätzlich
`eco_active_params_b`/`eco_total_params_b` gepflegt sind: Anbieter-Lookup →
(bei Fehlschlag) manuelle Parameter → (bei weiterem Fehlschlag oder fehlenden
Parametern) alte Formel/`None`. Schließt die Lücke zwischen "Modell exakt in
der DB" und "gar keine EcoLogits-Zahl", ohne die Ehrlichkeits-Regel bei
`/api/send` zu verletzen (dort bleibt `None` weiterhin `None`, wenn auch der
manuelle Pfad keine Parameter hat). Beim erfolgreichen Rückfall auf den
manuellen Pfad wird ein eigener, erklärender Hinweis zurückgegeben
(`MANUAL_FALLBACK_WARNING`: *"Modell nicht in EcoLogits-Datenbank gefunden;
Schätzung basiert auf manuellen Parametern statt auf einem bestätigten
Datenbankeintrag."*), damit der Nutzer die geringere Sicherheit der Zahl
erkennen kann. Live verifiziert (siehe Konversation): mit hinterlegten
manuellen Parametern liefert ein unbekannter Modellname jetzt ein Ergebnis
(`mode: compute_llm_impacts`) statt `None`; ohne manuelle Parameter bleibt das
Verhalten unverändert (`None`, ursprüngliche `FALLBACK_WARNING`).
Regressionstest: `test_unknown_model_falls_back_to_manual_parameters_when_available`
in `tests/test_ecologits_service.py`.

**B. Indikator "Modell gefunden" — `[ERLEDIGT, erste Testfassung]`.** Aktuell
trägt jedes EcoLogits-Ergebnis bereits ein internes `mode`-Feld
(`"llm_impacts"` = echter Datenbankeintrag für dieses Modell,
`"compute_llm_impacts"` = manuelle Näherung). Ursprünglicher Vorschlag: ein
kleiner, unaufdringlicher Indikator neben der CO₂e-Kachel, der ehrlich zeigt,
wie vertrauenswürdig die Zahl ist, z. B.:
- ✓ *"EcoLogits-Datenbank"* — Modell exakt gefunden (`mode: llm_impacts`, keine Warnung)
- ≈ *"Näherung"* — manueller Parameter-Pfad oder EcoLogits-Warnung vorhanden (z. B. `model-arch-not-released`, was bei Claude-Modellen laut unserer Verifikation ohnehin immer zutrifft, da Anthropic die Architektur nie veröffentlicht)
- – *"nicht verfügbar"* — kein Ergebnis, alte Formel oder `0`

Das macht die ohnehin vorhandene, aber bisher verborgene Unsicherheits-Information
sichtbar, ohne neue Berechnung — reine Anzeige von Daten, die
`ecologits_service.py` schon zurückgibt. Passt inhaltlich gut zur
Sensibilisierungs-Idee dieses Dokuments: nicht nur *wie viel* CO₂, sondern auch
*wie sicher* die Zahl ist.

**Umgesetzt als bewusst unstylischer erster Wurf, nur zum Testen** (Nutzer-
Vorgabe: "Geht erstmal nur darum zu testen", spätere Feinabstimmung folgt):
- `app/static/js/dashboard.js`: neue Helper-Funktion `ecoIndicatorLabel(sustainability)`
  liest `sustainability.mode` und liefert einen der drei reinen Textwerte
  `"EcoLogits DB"` / `"Näherung"` / `"Nicht verfügbar"` (kein Icon, keine
  Farbe/Styling — bewusst schlicht für den Test).
- `renderSustainabilityTiles()` schreibt diesen Text zusätzlich in je ein neues
  `<small>`-Element pro EcoLogits-Kachel (`#co2-indicator`, `#energy-indicator`,
  `#water-indicator`), ergänzt in `app/templates/dashboard.html`.
- Die Folgeprompt-Zusammenfassung (`#chat-continuation`, `ensureChat()`) hatte
  bisher **keine** Energie-/Wasserwerte, nur Kosten/Token/CO₂ — das war eine
  Lücke, kein Designentscheid. Jetzt ergänzt: `#chat-total-energy` und
  `#chat-total-water` (kumuliert über alle Folgeprompts, analog zu
  `#chat-total-co2`), sowie `#chat-eco-indicator` mit dem Indikator-Text der
  jeweils letzten Runde (`recordUsage()`).
- Cache-Buster in `dashboard.html` von `v='12'` auf `v='13'` erhöht.
- Kein neuer Test möglich (Projekt hat keine JS-Testinfrastruktur, siehe
  AGENTS.md); Backend/Python-Testsuite (`pytest`, 73 Tests) bleibt grün, da nur
  Template/JS geändert wurde. Manuelle Verifikation im Browser steht noch aus.

**Inzwischen final entschieden**: die endgültige visuelle Gestaltung wurde
über Ring-Farbwechsel (Überlauf) und Tassen-Silhouetten gelöst statt über
eine separate Icon-Vorschlag-(A)-Lösung — siehe Checkliste unten.

## Bildhafte Darstellung statt nackter Zahlen (Brainstorm, größtenteils umgesetzt) `[GRÖSSTENTEILS ERLEDIGT]`

> **Hinweis**: Dieser Abschnitt startet als Brainstorm — der spätere Verlauf
> (Icons, Aktivitätsringe, Tassen-Segmente, gemeinsame "Tasse Tee"-Referenz)
> ist über die Nachträge weiter unten sowie die Checkliste am Ende
> vollständig nachvollziehbar und weitgehend umgesetzt. Nur die Wahl
> zwischen Emoji und eigens gezeichneten Silhouetten wurde am Ende bewusst
> zugunsten der Emoji entschieden (siehe Checkliste), nicht offen gelassen.

Greift den Backlog-Punkt *"Dashboard: bildhafte Visualisierung der EcoLogits-Werte"*
aus `Tasklist.md` auf. Grundlage: ein privater Flask-/HTML-Prototyp
(`F:\Workspace\PyProjects\EcoLogits`, zwei Dateien: `vergleich_modelle_impact.py`,
`wasser_vorschau.html`), der als Startvorlage für die finale Dashboard-Umsetzung
dienen soll.

### Analyse des Prototyps

**`wasser_vorschau.html`** — eigenständiges HTML/CSS/Vanilla-JS, kein Server
beteiligt: SVG-Gefäße (Glas 250 mL, Flasche 500 mL) mit geclipptem, animiertem
Wasser-Füllstand (`clip-path` + `transform`), Modell-Umschalter, ein
`bruch()`-Helfer, der Verhältnisse in greifbare Brüche übersetzt ("ca. 1/500"
statt "0,2 %"), `prefers-reduced-motion` bereits berücksichtigt.

**`vergleich_modelle_impact.py`** — eigenständiges CLI-Skript, nutzt
`EcoLogits.init(providers=["anthropic"])` (SDK-Patching-Modus) mit **echten,
live Anfragen an die Anthropic-API**, um automatisch Impact-Werte zu bekommen.

**Bewertung, direkt an unserer heutigen Architektur gespiegelt:**

- ✅ **HTML/CSS/JS-Teil ist 1:1 übernehmbar, kein Kompromiss.** Unser Dashboard
  ist bereits Jinja2 + Vanilla-JS + reines CSS, kein Framework, kein
  Build-Schritt — exakt dieselbe Technikbasis. Die SVG-Füllstand-Technik und
  der `bruch()`-Helfer lassen sich direkt in `app/static/css/style.css` /
  `dashboard.js` übernehmen. "Möglich mit Flask?" ist hier keine echte Frage —
  Flask liefert nur die Seite aus, das Rendering passiert im Browser, wie bei
  `dashboard.js` heute schon.
- ❌ **Der Python-Teil ist nicht übernehmbar.** SDK-Patching + echte
  Live-Anfragen an Anthropic nur für eine *Schätzung* verletzt direkt den
  Kerngrundsatz *"Analyse und Versand sind getrennt, externe Übertragung
  erfolgt nie automatisch"* — und ist genau der SDK-Patching-Modus, den wir
  weiter oben als für uns technisch nicht anwendbar identifiziert haben. Die
  Datenbeschaffung bleibt unser bestehender, rein lokaler
  `ecologits_service.compute_impacts()`-Pfad — nur das Präsentationslayer wird
  übernommen, nicht die Datenbeschaffung.
- ⚠️ **Kalibrierungsproblem, dieselbe Art wie beim Baum/Glas-Backlog-Punkt.**
  Die Demo-Werte (4,1–46,3 mL, mit größeren Claude-3-Modellen und echten
  Cloud-Antworten gerechnet) sind deutlich größer als unsere typischen
  Pro-Prompt-Werte (Größenordnung 0,1 mL in bisherigen Beispielen) — ein
  250-mL-Glas bliebe damit fast leer, kaum aussagekräftig. Zwei Auswege:
  kleinere Referenzgefäße für die Pro-Prompt-Ansicht (siehe Tropfen-Idee
  unten), oder Glas/Flasche für die **kumulierte** Ansicht reservieren (erneut
  der bisher ungenutzte `/api/usage/summary`-Endpunkt, siehe Backlog).

### Brainstorm: eigenständige Metaphern (bewusst nicht die Baum-Wachstumsstadien eines anderen Teams)

Ausgangslage: ein anderes Team nutzt Baum-Wachstumsstadien (Samen → Sprössling →
junger Baum → ausgewachsener Baum). Bewusste Abgrenzung — außerdem passt
"Wachstum über Zeit" eher zu einer kumulierten als zu einer Pro-Anfrage-Ansicht.

**CO₂ (Klimawirkung):**
- **Waage/Balance** — neigt sich mit dem CO₂-Gewicht. Passt sprachlich zur
  bereits bestehenden "CO₂e-**Bilanz**"-Kachel aus diesem Redesign — Bilanz ist
  im Kern eine Waage.
- **Klima-Thermometer** — vertikaler Füllstand wie ein Fieberthermometer, ein
  etabliertes Symbol für Erderwärmung speziell, nicht generisch "Umwelt".
- **Aufblasender Ballon** — Gasmenge, die sich ansammelt (Treibhaus*gas*).

**Energie:**
- **Batterie-Füllstand** — universell verständlich, passt zur im Prototyp
  bereits vorhandenen "Smartphone-Ladung %"-Vergleichsgröße.
- **Glühbirne mit variabler Leuchtkraft** statt Füllstand.

**Wasser:**
- Glas/Flasche aus dem Prototyp bleibt gut — eigene Arbeit, keine fremde Idee.
- Für sehr kleine Pro-Prompt-Mengen: **Tropfen-Reihe** (z. B. 5 Tropfen,
  teilweise gefüllt, wie ein Sterne-Rating) statt eines großen, fast leeren
  Gefäßes — bei winzigen mL-Werten optisch ehrlicher.

**Wichtiger als die Einzelmetapher — eine gemeinsame visuelle Sprache über alle
drei Metriken.** Drei völlig unterschiedliche Illustrationsstile nebeneinander
könnten uneinheitlich wirken. Sauberer: dasselbe Füllstands-/Meter-Prinzip
(Icon-Silhouette + geclipptes Füllelement + Prozentangabe + greifbarer Bruch,
wie in der Wasser-Vorschau bereits gebaut) für alle drei, nur mit anderer
Silhouette (Waage/Batterie/Tropfen) und Akzentfarbe — wirkt dann als *ein
System*, nicht als drei zusammengewürfelte Widgets.

Alles hier ist Brainstorm-Stand, keine Entscheidung — weder Metapher noch
Umsetzungsdetails sind final.

### Erste Testfassung: Icons + Basis-Label + Mini-Meter `[ERLEDIGT, erste Testfassung]`

**Nicht die volle SVG-Füllstand-Umsetzung aus dem Prototyp** — bewusst ein
kleiner, schneller erster Schritt (gleiches Vorgehen wie beim Text-Indikator
weiter oben), um früh sichtbares Feedback zu bekommen, bevor Zeit in die
vollständige Metaphern-Umsetzung fließt.

**Obere Kacheln (`app/templates/dashboard.html`)**:
- Icons als reine Kennzeichnung (Backlog-Punkt A) direkt in die Kachel-Labels
  aufgenommen: ⚖️ CO₂e, 🔋 Energie, 💧 Wasser/ADPe — orientiert an den oben
  gesammelten, bewusst eigenständigen Metaphern (Waage statt Baum), nicht an
  wörtlicher Mengendarstellung.
- Neues `#footprint-basis`-Label über den Kacheln, zeigt "Basis: Originalprompt"
  bzw. "Basis: Optimierter Prompt" — gesetzt in `render()` (`app/static/js/dashboard.js`,
  Originalprompt-Fall) bzw. `refreshFootprint()` (Optimiert-Fall aus Option #2).
  Bewusst **kein** Nebeneinander/Vergleich beider Werte — das wäre wieder die
  ursprünglich verworfene, strukturell verzerrte Vergleichslogik. Nur eine
  neutrale Kennzeichnung, worauf sich die aktuell gezeigte Zahl bezieht.

**Rechte Statusleiste / kumulierter Footprint (`ensureChat()`-Aside)**:
- CO₂e/Energie/Wasser gesamt bekommen dieselben Icons plus je einen schmalen
  Füllbalken darunter (`#chat-total-co2-meter` etc.), aktualisiert in
  `recordUsage()` über eine neue `updateMeter()`-Hilfsfunktion.
- **Wichtig, bewusst nicht die im Prototyp vorhandene kalibrierte
  Referenzgröße**: die Balken sind rein **session-relativ** — "voll" bedeutet
  das Zehnfache des ersten in dieser Unterhaltung beobachteten Werts je
  Metrik (`footprintMeterMax`), keine reale Bezugsgröße (kein Baum, kein
  Liter-Glas). Das war eine bewusste Entscheidung, um der Ehrlichkeits-Linie
  des gesamten Redesigns treu zu bleiben: die "Referenzgefäß-Kalibrierung"
  (siehe Checkliste) war zu diesem Zeitpunkt noch nicht erledigt (später via
  der gemeinsamen "Tasse Tee"-Referenz gelöst, siehe Nachtrag 8 weiter unten),
  also wurde hier noch keine falsche Präzision vorgetäuscht. Ein erklärender
  Hinweistext direkt
  unter den Balken macht das explizit ("Balken zeigen den relativen Verlauf
  in dieser Unterhaltung, keine kalibrierte Referenzgröße."). `footprintMeterMax`
  wird beim Start einer neuen Konversation (`send()`) zurückgesetzt.

Cache-Buster auf `v='19'` erhöht. Kein Backend-/Python-Code betroffen,
`pytest` (79 Tests) bleibt grün als Sanity-Check. Live verifiziert: Icons,
`#footprint-basis` und die Meter-JS-Funktionen werden vom Server korrekt
ausgeliefert.

Offen für eine spätere, ausführlichere Umsetzung: die volle SVG-Füllstand-
Optik aus `wasser_vorschau.html`, die eigentliche Referenzgefäß-Kalibrierung,
und eine finale Entscheidung, ob Waage/Batterie/Tropfen als Silhouetten statt
Emoji verwendet werden sollen.

### Nachtrag nach Live-Test: Meter-Balken unsichtbar (Root Cause: CSP) + Kachel-Restrukturierung `[ERLEDIGT]`

**Finding 1 — Meter-Balken in der Statusleiste waren komplett unsichtbar**
(nur Icons zu sehen, kein Füllbalken, kein Hintergrund). **Root Cause**: die
Balken (und mehrere andere neu hinzugefügte Elemente, u. a. `#footprint-basis`)
wurden mit inline `style="..."`-Attributen direkt in HTML-Strings erzeugt.
Das Projekt setzt aber eine strikte CSP ohne `'unsafe-inline'`
(`app/__init__.py`: `style-src 'self'`) — die blockiert **jedes** inline
`style`-Attribut im HTML (egal ob serverseitig gerendert oder per
`innerHTML` aus JavaScript erzeugt), lautlos und ohne sichtbaren Fehler in
der UI selbst (nur in der Browser-Konsole). Betroffen waren dadurch nicht nur
die neuen Meter-Balken, sondern auch länger schon bestehende Stellen wie das
`position:sticky` der Statusleiste und die `max-height`/`overflow` des
Chat-Nachrichtenbereichs — beides lief seit der ursprünglichen
Chat-Fortsetzen-Implementierung bereits lautlos ins Leere. **Wichtige
Klarstellung, warum ein Teil der bestehenden Styles trotzdem funktionierte**:
`element.style.cssText = "..."`/`element.style.eigenschaft = "..."` als
JavaScript-Zuweisung auf der CSSOM (z. B. das bestehende
`chat.style.cssText = "display:grid;..."` für das zweispaltige Layout) fällt
**nicht** unter die CSP-`style-src`-Beschränkung — nur echte HTML-`style`-
Attribute (statisch im Template oder per `innerHTML`-String) sind betroffen.
Das erklärt, warum ein Teil der Seite sichtbar korrekt aussah, während andere
Teile lautlos nicht griffen.

**Fix**: Alle betroffenen inline `style="..."`-Attribute in
`app/templates/dashboard.html` und den `innerHTML`-Strings in
`app/static/js/dashboard.js` durch benannte CSS-Klassen in
`app/static/css/style.css` ersetzt (`.eco-panel-tiles`, `.footprint-basis`,
`.chat-messages`, `.chat-actions`, `.chat-estimate-result`, `.chat-summary`,
`.meter`, `.meter-fill` + Modifikatoren `.co2`/`.energy`/`.water`,
`.meter-note`). Die einzige weiterhin dynamische Eigenschaft (Balkenbreite in
`updateMeter()`) bleibt per `meter.style.width = ...` gesetzt — das ist eine
CSSOM-Zuweisung, keine Inline-Attribut-Änderung, also von der CSP unberührt.

**Finding 2 — Wunsch nach eigenem Kachel-Rahmen für die EcoLogits-Werte**:
CO₂e/Energie/Wasser sollten optisch wie ein eigenes Panel wirken (klare
Kachelkante wie beim linken "Prompt analysieren"-Panel), mit dem
Basis-Label als Fußzeile darin, getrennt von Kosten/Dauer/Compliance.
**Umsetzung**: neue Struktur in `dashboard.html` — ein `<div class="panel">`
mit `<h2>Fußabdruck</h2>`, darin `.eco-panel-tiles` (3-spaltiges Grid ohne
einzelne Kachel-Rahmen je Wert, da der äußere `.panel`-Rahmen bereits die
Kartenoptik liefert) sowie `#footprint-basis` als Fußzeile mit oberer
Trennlinie. Die verbleibenden drei Kacheln (Kosten/Dauer/Compliance) bleiben
in der bestehenden `.metrics`-Kachelreihe, deren Spaltenzahl von 4 auf 3
angepasst wurde.

Cache-Buster auf `v='21'` erhöht. `pytest` (79 Tests) bleibt grün (reine
CSS/HTML/JS-Änderung, kein Backend betroffen). Live verifiziert: CSP-Header
bestätigt (`style-src 'self'`, kein `unsafe-inline`), keine verbliebenen
inline `style="`-Attribute mehr in ausgeliefertem HTML/JS, alle neuen
CSS-Klassen werden korrekt ausgeliefert, `.panel`/`.eco-panel-tiles`-Struktur
im gerenderten HTML bestätigt.

**Nachtrag 3**: Wasser und ADPe teilten sich bisher eine Kachel (eine große
Zahl in Litern, ADPe nur als kleine Zusatzzeile in µg Sb-Äq. darunter) —
obwohl es fachlich zwei komplett unabhängige EcoLogits-Größen sind
(`impacts.wcf` vs. `impacts.adpe`, unterschiedliche Einheiten, keine
Verrechnung). Das wirkte wie ein einzelner kombinierter Wert. Mit der neuen
Panel-Struktur (individuelle Kacheln innerhalb des "Fußabdruck"-Panels) gibt
es keinen Platzgrund mehr, sie zusammenzuhalten — deshalb aufgetrennt in zwei
eigenständige Kacheln (💧 Wasser, ⛏️ ADPe), je mit eigenem Tooltip und
eigenem Indikator (`#water-indicator`/`#adpe-indicator` statt geteiltem
`#water-indicator`). `.eco-panel-tiles` von 3 auf 4 Spalten erweitert
(inkl. Responsive-Anpassung bei 900px). Cache-Buster `v='22'`.

**Lehre für künftige UI-Änderungen an diesem Projekt**: wegen der strikten
CSP grundsätzlich **keine** inline `style="..."`-Attribute mehr verwenden
(weder im Template noch per `innerHTML`) — entweder eine CSS-Klasse in
`style.css` anlegen, oder bei wirklich dynamischen Werten
`element.style.eigenschaft = wert` (CSSOM) auf einem bereits im DOM
befindlichen Element setzen.

**Nachtrag 2 (nach nochmaligem Live-Test)**: Zwei weitere Feinjustierungen.
(1) ADPe-Tooltip ergänzt: erklärt jetzt explizit, dass die angezeigte
Einheit "Sb-Äq." für "Antimon-Äquivalent" steht (Sb = chemisches Symbol für
Antimon) — vorher stand nur "Antimon-Äquivalent" ausgeschrieben im Tooltip,
ohne die Abkürzung mit der tatsächlich angezeigten Einheit zu verknüpfen.
(2) Die drei Fußabdruck-Werte hatten durch die Panel-Restrukturierung ihre
individuelle Kachel-Optik verloren (nur noch der äußere Panel-Rahmen war
sichtbar) — das entsprach nicht dem gewünschten "Stil des Dashboards
beibehalten". Fix: `.eco-panel-tiles article` bekommt dieselbe Karten-
Deklaration wie `.metrics article` (Selektor-Liste in `style.css` erweitert),
sodass CO₂e/Energie/Wasser wieder als einzelne Kacheln erscheinen —
zusätzlich zum umschließenden `.panel`-Rahmen, nicht statt ihm.

**Nachtrag 5 — Bugfix: Wasser rundete bei kurzen Prompts auf 0**: Live-Test
zeigte "0 L" bei kurzen Prompts (z. B. "Wie alt ist die Erde?"). Root Cause,
dieselbe Fehlerklasse wie der historische ADPe-Bug: `water_liters` wurde in
`_to_impacts_dict()` direkt in Litern auf 4 Nachkommastellen gerundet — bei
kurzen Prompts (wenige Dutzend geschätzte Ausgabe-Token) liegt der reale
Wasserverbrauch aber im einstelligen Mikroliter- bis niedrigen
Milliliter-Bereich (nachgerechnet: 8,6e-6 L für 30 Ausgabe-Token bei einem
lokalen kleinen Modell), rundet in Litern also fast immer zu exakt 0 — der
Wert war real vorhanden, nur unterhalb der Rundungsschwelle. **Fix**: Feld auf
`water_ml` umgestellt (`× 1000`, analog zur ADPe-µg-Umrechnung), betrifft
`ecologits_service.py`, alle Frontend-Stellen (Kachel, Meter, Folgeprompt-
Schätzung, kumulierte Summe, Tooltip), Tests und die Schema-Referenzen in
`ECOLOGITS_INTEGRATION.md` (dort mit Verweis auf den damaligen Feldnamen,
nicht stillschweigend umgeschrieben). Live nachgerechnet: derselbe kurze
Prompt zeigt jetzt `water_ml: 0.0086` statt `0.0`. Cache-Buster `v='24'`,
`pytest` (79 Tests) grün.

**Nachtrag 6 — Referenzgrößen für Energie/Wasser in der Statusleiste
`[ERLEDIGT, CO₂/ADPe im Backlog]`**: Der Nutzer bemängelte zu Recht, dass die
rein session-relativen Meter-Balken ohne Bezug zu einer bekannten
Alltagsgröße "ohne großen Mehrwert" sind — kein Achtungseffekt bzgl.
bewusster KI-Nutzung. Diskutierte Referenzideen: Energie = Handyladung,
Wasser = täglicher Trinkbedarf (2 L), CO₂ = Kurzstreckenflug, ADPe = noch
offen. Gegenrechnung ergab: **Kurzstreckenflug ist für CO₂ um Größenordnungen
zu groß** (~100–150 kg CO₂ pro Passagier vs. gemessene 0,0106 g kumuliert in
einem Testlauf — ein zehnmillionstel Anteil, unsichtbarer als der schon
verworfene Baum-Vergleich) — bessere Kandidaten wären eine Websuche
(~1–5 g CO₂) oder eine Tasse Tee (~15–20 g CO₂), aber noch nicht entschieden.
ADPe fehlte zudem komplett in der Statusleiste (nur CO₂/Energie/Wasser
gezeigt) und hat keine offensichtliche Alltagsreferenz — Idee "Anteil am
Rohstoffbedarf eines Smartphone-Chips" im Raum, aber ohne belastbare Quelle.
**Entscheidung**: Energie und Wasser jetzt umgesetzt, CO₂ und ADPe bewusst
zurückgestellt (siehe Checkliste), bis passende, belegbare Referenzwerte
gefunden sind.

**Umsetzung** (`app/static/js/dashboard.js`): neue Konstanten
`ENERGY_REFERENCE_KWH = 0.015` (≈ 15 Wh, grober Richtwert für eine typische
Smartphone-Vollladung, moderne Akkus liegen ungefähr zwischen 11 und 20 Wh —
kein exakt zitierter Wert, sondern eine plausible Näherung, analog zur
`RATIO`-Platzhalter-Praxis) und `WATER_REFERENCE_ML = 2000` (2 L täglicher
Trinkbedarf, vom Nutzer selbst als Beispielwert vorgegeben). Neue Funktion
`updateReferenceMeter()` ersetzt für Energie/Wasser die bisherige
session-relative `updateMeter()`-Logik: Balkenbreite = Anteil an der
Referenzgröße (gedeckelt bei 100 %), plus eine **Bruch-Angabe** statt
Prozentzahl (z. B. "≈ 1/517 einer Handyladung" statt "0,19 %") — bei so
kleinen Anteilen ist ein Bruch leichter erfassbar, dieselbe Logik wie der
`bruch()`-Helfer im bereits analysierten `wasser_vorschau.html`-Prototyp.
CO₂ behält die alte, session-relative `updateMeter()`-Logik (`footprintMeterMax`
jetzt nur noch `{co2: ...}`, `energy`/`water`-Keys entfernt, da nicht mehr
gebraucht). Live nachgerechnet mit den tatsächlichen Screenshot-Werten:
Energie 0,029 Wh von 15 Wh → 1/517; Wasser 0,0763 mL von 2000 mL → 1/26.212 —
beide Bruch-Werte plausibel und deutlich griffiger als die vorherigen
Rohprozentzahlen. Cache-Buster `v='25'`, `pytest` (79 Tests) grün (reine
Frontend-Änderung).

**Nachtrag 7 — Energie von kWh auf Wh umgestellt `[ERLEDIGT]`**: Der zuvor
zurückgestellte Backlog-Punkt wurde direkt danach doch umgesetzt. Anders als
bei Wasser/ADPe ging es hier nicht um ein Rundung-auf-0-Problem (Energie
wurde bereits auf 6 Nachkommastellen gerundet, blieb also sichtbar), sondern
um reine Lesbarkeit — Werte wie `0.000029 kWh` sind unnötig schwer zu
erfassen. **Umsetzung**: `energy_kwh` → `energy_wh` (`× 1000`) sowohl in
`ecologits_service.py` (`_to_impacts_dict()`) **als auch** in
`sustainability_service.py` (`estimate_sustainability()`, der alten
Formel-Fallback-Pfad) — beide Pfade liefern das Feld, mussten also
konsistent umbenannt werden, sonst hätte ein Merge aus Formel-Fallback und
EcoLogits-Ergebnis (`{**formula, **(eco_result or {})}` in
`sustainability_for()`) je nach Pfad unterschiedliche Feldnamen geliefert.
Die interne kWh-Basis für die CO₂-Berechnung (`energy * carbon_intensity`,
`carbon_intensity` in g/kWh) blieb unverändert — nur der zurückgegebene
Anzeige-Wert wird umgerechnet. Frontend: alle Stellen (obere Kachel,
kumulierte Summe, Folgeprompt-Vorschau, Energie-Referenzkonstante jetzt
`ENERGY_REFERENCE_WH = 15`) umgestellt. Tests (`test_ecologits_service.py`,
`test_routes.py`) angepasst. Cache-Buster `v='26'`, `pytest` (79 Tests) grün,
live nachgerechnet: `energy_wh: 0.0025` statt `energy_kwh: 0.0000025`.

**Nachtrag 8 — Gemeinsame "Tasse Tee"-Referenz für CO₂/Energie/Wasser
`[ERLEDIGT]`**: Statt drei unabhängiger Referenzgrößen (Handyladung, 2 L
Trinkbedarf, Kurzstreckenflug/Websuche) schlug der Nutzer **eine**
gemeinsame, in sich konsistente Referenz vor: eine Tasse Tee kochen
(250 mL Wasser von ca. 20 °C auf 100 °C). Vorteil gegenüber den vorherigen
Einzel-Referenzen: alle drei Zahlen stammen aus **demselben** Szenario statt
aus drei unabhängigen, unterschiedlich gut belegten Quellen — und schließt
nebenbei den noch offenen CO₂-Backlog-Punkt.

**Herleitung** (grobe physikalische Überschlagsrechnung, keine zitierte
Quelle, analog zur `RATIO`-Platzhalter-Praxis):
- Wasser: 250 mL, direkt.
- Energie: `Q = m·c·ΔT` = 250 g × 4,186 J/(g·K) × 80 K ≈ 83,7 kJ (ideal);
  mit ~85 % Wasserkocher-Wirkungsgrad ≈ 27 Wh, gerundet auf **25 Wh**.
- CO₂: aus der Energie abgeleitet mit demselben `CARBON_INTENSITY_G_PER_KWH`
  (350 g/kWh), das die serverseitige Formel-Schätzung ohnehin schon
  verwendet, statt eine unabhängige Zahl zu suchen: 0,025 kWh × 350 g/kWh =
  **8,75 g**.
- ADPe bewusst ohne Referenz — Teekochen verbraucht keine mineralischen
  Rohstoffe (Herstellungs-, kein Nutzungseffekt); bleibt im Backlog, wird im
  Zweifel vorerst nur aufsummiert ohne Alltagsvergleich gezeigt.

**Umsetzung** (`app/static/js/dashboard.js`): `ENERGY_REFERENCE_WH`/
`WATER_REFERENCE_ML` ersetzt durch `TEA_CUP_WATER_ML = 250`,
`TEA_CUP_ENERGY_WH = 25`, `TEA_CUP_CO2_G = 8.75`. CO₂ nutzt jetzt ebenfalls
`updateReferenceMeter()` (Bruch-Anzeige, label "einer Tasse Tee") statt der
bisherigen session-relativen `updateMeter()`-Logik — `updateMeter()` und
`footprintMeterMax` dadurch komplett entfernt (kein Aufrufer mehr). Alle drei
Meter-Notizen (`#chat-co2-reference`, `#chat-energy-reference`,
`#chat-water-reference`) zeigen dieselbe Formulierung ("≈ 1/N einer Tasse
Tee"), was die gemeinsame Szenario-Klammer zusätzlich verstärkt. Live
nachgerechnet mit den zuletzt gemessenen Screenshot-Werten: CO₂ 1/825,
Energie 1/862, Wasser 1/3.277 — im Gegensatz zu den vorherigen Einzel-
Referenzen (1/517 vs. 1/26.212) jetzt auch untereinander plausibler
vergleichbar. Cache-Buster `v='27'`, `pytest` (79 Tests) grün (reine
Frontend-Änderung).

**Nachtrag 9 — Aktivitätsringe (Apple-Watch-inspiriert) zusätzlich zu den
Balken `[ERLEDIGT]`**: Der Nutzer wollte eine zweite, zusätzliche
Visualisierung der kumulierten "Tasse Tee"-Anteile — drei konzentrische
Fortschrittsringe wie bei den Apple-Watch-Aktivitätsringen, **nur als
Inspiration für das allgemeine Konzept übernommen** (verschachtelte
Ring-Fortschrittsanzeigen sind ein verbreitetes, nicht Apple-exklusives
UI-Muster), nicht Apples konkretes Markendesign kopiert — eigene Farben,
eigene Umsetzung, kein Bezug zu Move/Exercise/Stand. Farben wie vom Nutzer
vorgegeben: Wasser = Blau, CO₂e = Grün, Energie = Rot (zufällig ähnlich zu
Apples Zuordnung, aber unabhängig gewählt und bereits als CSS-Variablen
`--blue`/`--green`/`--red` im Projekt vorhanden). Referenzgrößen: dieselbe
"Tasse Tee"-Kalibrierung wie bei den Balken (250 mL/25 Wh/8,75 g) — die vom
Nutzer angedachte Verkleinerung auf 150 mL wurde **nicht** umgesetzt (bewusst
zurückgestellt, um nicht zwei Dinge gleichzeitig zu ändern); ein Wechsel ist
später eine reine Konstanten-Änderung (`TEA_CUP_WATER_ML`, `TEA_CUP_ENERGY_WH`,
`TEA_CUP_CO2_G` neu herleiten).

**Umsetzung**: reines SVG (`<circle>` mit `stroke-dasharray`/
`stroke-dashoffset`-Technik), keine neue Abhängigkeit. Drei verschachtelte
Kreise (Radius 52/41/30, Ring-Breite 9) in `app/static/js/dashboard.js`
(`ensureChat()`), neue Funktion `updateRing(id, ratio)` liest den Radius
direkt aus dem SVG-Attribut (`getAttribute("r")`) statt ihn doppelt zu
pflegen, setzt `circle.style.strokeDasharray`/`strokeDashoffset` — **CSSOM-
Zuweisung, keine inline `style=""`-Attribute**, damit CSP-konform (gleiche
Lehre wie beim Meter-Balken-Bugfix weiter oben). `updateReferenceMeter()` um
einen `ringId`-Parameter erweitert, ruft `updateRing()` mit demselben
`ratio`-Wert wie den Balken auf — ein Datenpfad für beide Darstellungen,
keine doppelte Berechnung. Farb-/Track-Styling als neue CSS-Klassen
(`.rings`, `.ring-track`, `.ring-fill` + `.water`/`.co2`/`.energy`,
`.ring-legend`) in `style.css`. Kleine Farb-Legende unter den Ringen, da
Farbe allein nicht selbsterklärend ist. Ringe erscheinen zusätzlich zu den
bestehenden Balken/Bruch-Texten, ersetzen sie nicht. Cache-Buster `v='28'`,
`pytest` (79 Tests) grün, live verifiziert (Ring-Markup, `updateRing()` und
CSS-Klassen korrekt ausgeliefert).

**Nachtrag 10 — Bugfix: uneinheitliches Zahlenformat bei der Bruch-Anzeige
`[ERLEDIGT]`**: Live-Test deckte eine Verwechslungsgefahr auf: Der Nutzer las
"Wasser gesamt 1.6003 mL" (normales JS-`toFixed()`-Format, Punkt =
Dezimaltrennzeichen, wie überall sonst in der App: `$ 0.000000`, `0.0106 g`
usw.) im selben Sichtfeld wie den zugehörigen Bruch "≈ 1/156 einer Tasse
Tee" und hielt das für widersprüchlich — Nachrechnen bestätigte, dass die
Bruch-Mathematik korrekt war (250/1,6003 ≈ 156,2), die eigentliche Ursache
war aber eine **Formatierungs-Inkonsistenz**: `updateReferenceMeter()`
nutzte für den Nenner `Math.round(1 / ratio).toLocaleString("de-DE")` —
deutsches Format mit **Punkt als Tausendertrennzeichen** —, während jede
andere Zahl in der gesamten App mit normaler `toFixed()`-Formatierung
(Punkt als Dezimaltrennzeichen, englische Konvention) ausgegeben wird. Bei
kleinen Nennern (z. B. "156") fällt das nicht auf, bei größeren (z. B.
"1/26.212" aus einem früheren Beispiel) sieht der Punkt aber aus wie ein
Dezimaltrennzeichen und wird leicht falsch gelesen — exakt das, was hier
passierte. **Fix**: `toLocaleString("de-DE")` entfernt (war die einzige
Stelle im gesamten Frontend, die es nutzte); ebenso das `.replace(".", ",")`
im `≥1`-Zweig (z. B. "1,3× einer Tasse Tee") entfernt, da auch das eine
Insel deutscher Formatierung in einer sonst durchgehend englisch
formatierten App war. Jetzt durchgängig dieselbe Konvention wie der Rest
der App. Cache-Buster `v='29'`, `pytest` (79 Tests) grün, live verifiziert.

**Nachtrag 11 — Tassengröße auf 150 mL reduziert + Sensibilisierungs-
Hochrechnung "500 KI-Anfragen" + CO₂-Icon getauscht `[ERLEDIGT]`**:

**(1) Tasse Tee: 250 mL → 150 mL.** Linear aus der bestehenden Herleitung
skaliert (Faktor 0,6 — Energie ist bei gleicher Temperaturdifferenz
proportional zur Wassermenge, keine neue Physik nötig): `TEA_CUP_WATER_ML =
150`, `TEA_CUP_ENERGY_WH = 15` (vorher 25 × 0,6), `TEA_CUP_CO2_G = 5.25`
(vorher 8,75 × 0,6). Wirkt sowohl auf die Balken/Bruch-Anzeige als auch auf
die Ringe, da beide dieselben drei Konstanten über `updateReferenceMeter()`
nutzen — eine Änderungsstelle genügt.

**(2) Neue Sensibilisierungs-Ansicht: "500 KI-Anfragen (hochgerechnet)".**
Idee des Nutzers: zusätzlich zur bisherigen "Kosten und Nutzung"-Ansicht
(Ist-Zustand dieser Unterhaltung) zeigen, was ein 500-facher Multiplikator
der bisherigen Nutzung bedeuten würde — Sensibilisierungs-Testfassung, **kein
Anspruch auf eine reale Nutzerzahl-Prognose**, klar so beschriftet
(`REQUEST_MULTIPLIER = 500`, Kommentar im Code). Rechnet
`cumulativeCo2/-Energy/-Water × 500` gegen dieselbe Tasse-Tee-Referenz und
zeigt das Ergebnis in einem **zweiten**, separat beschrifteten Ring-Satz
(eigene IDs `#ring-*-500x`) unterhalb der bestehenden Ringe, mit
kombinierter Zeile "Absolutwert · Bruch/Vielfaches" pro Metrik statt
zusätzlicher Balken (Nutzer wollte explizit "eine zweite Ring-Darstellung",
keine dritte Balkenreihe). Neue Funktion `updateProjectedMetric()`, teilt
sich die Bruch-Formatierung mit den bestehenden Balken/Ringen über die neu
extrahierte Hilfsfunktion `fractionLabel()` (keine doppelte Formatierlogik).
ADPe bleibt unverändert außen vor.

**(3) CO₂-Icon getauscht: ⚖️ → 🌿.** Nutzerwunsch, das Waage-Symbol
durchgängig gegen ein Blatt-Symbol zu ersetzen ("doppelblättriges
Baumblatt o. ä."). Betrifft beide Stellen, an denen ⚖️ vorkam: die obere
Fußabdruck-Kachel (`dashboard.html`) und die "CO₂e gesamt"-Zeile in der
Statusleiste (`dashboard.js`). **Kurzer Hinweis zur Einordnung** (keine
Ablehnung, nur zur Nachvollziehbarkeit festgehalten): weiter oben im
Brainstorm-Abschnitt hatten wir uns bewusst gegen Baum-Symbolik
entschieden, weil ein anderes Team bereits Baum-**Wachstumsstadien** als
eigenständiges Kachel-Konzept nutzt. Ein einzelnes Blatt-Icon als reine
Kennzeichnung (kein Wachstumsstadien-System) ist davon inhaltlich
unabhängig — deshalb kein Widerspruch, nur als Kontext dokumentiert.

**Bekannter kleiner Rundungs-Randfall** (nicht behoben, niedrige Priorität):
Liegt der 500x-Wert knapp unter der Referenz (z. B. Verhältnis ≈ 0,97),
zeigt `fractionLabel()` "≈ 1/1" statt "≈ 1×" — mathematisch korrekt
(`Math.round(1/0.97) = 1`), aber optisch etwas unglücklich in diesem engen
Grenzbereich. Nicht behoben, da rein kosmetisch und nur bei zufälligem
Auftreffen nahe der Grenze sichtbar.

Cache-Buster `v='30'`, `pytest` (79 Tests) grün, live verifiziert
(Icon-Tausch, neue Konstanten und `updateProjectedMetric()` korrekt
ausgeliefert; Hochrechnungs-Mathematik separat mit Beispielwerten
nachgerechnet).

**Nachtrag 12 — Überlauf-Darstellung bei ≥1× Tasse Tee `[ERLEDIGT]`**: Nach
dem ersten Live-Test der 500er-Hochrechnung fiel auf, dass ein gedeckelter
Ring bei 1,0× genauso aussieht wie bei 5× — die eigentliche Vielfachheit
ging visuell komplett verloren, nur der kleine Text darunter verriet sie.
Diskutierte Optionen: (A) nur eine "Achtung, überschritten"-Markierung am
Ring, (B) Mehrfach-Umlauf im Ring selbst (bei drei ohnehin engen
verschachtelten Ringen aber schnell unübersichtlich), (C) eine
Tassen-Icon-Reihe (Nutzer-Idee). Entscheidung: **Kombination aus A und
einer vereinfachten Variante von C**, nicht B — der Ring bleibt als
"schneller Blick, im Rahmen oder drüber"-Indikator einfach, die genaue
Vielfachheit wandert in eine eigene, dafür besser geeignete Darstellung.

**Umsetzung**:
- `updateRing()` togglet jetzt eine `overflow`-CSS-Klasse auf dem Kreis,
  sobald `ratio >= 1` (`circle.classList.toggle(...)` — DOM-Klassen-API,
  von der CSP unberührt, anders als ein inline `style=""`). Neue
  Ring-Klassen `.ring-fill.overflow.water/.co2/.energy` in `style.css`
  fügen einen farbigen `drop-shadow`-Leuchtrand hinzu — reine
  Aufmerksamkeits-Markierung, zeigt keine Vielfachheit.
- Neue Funktion `renderCupSegments()`: eine Reihe kleiner Segmente
  (abgerundete Balken, keine echte Tassen-Grafik — Emoji lassen sich nicht
  sauber teilfüllen) statt einer Tasse-Icon-Reihe im engeren Sinne. Volle
  Segmente = ganze Vielfache, ein zusätzliches teilgefülltes Segment (per
  CSS-Custom-Property `--fill`, gesetzt über `element.style.setProperty()`
  — ebenfalls CSSOM, CSP-unkritisch) für den Rest. Auf 10 sichtbare
  Segmente gedeckelt, darüber hinaus als Text ("+X") statt einer ausufernden
  Reihe. Nur in der **500er-Hochrechnung** ergänzt, nicht in der
  "Kosten und Nutzung"-Ansicht pro Konversation — dort bleiben Werte
  realistisch fast immer <1×, das eigentliche Problem tritt dort kaum auf.
- `updateProjectedMetric()` um einen `segmentsId`-Parameter erweitert, ruft
  `renderCupSegments()` mit demselben `ratio`-Wert wie Ring und Text auf —
  ein Datenpfad für alle drei Darstellungen.

Live nachgerechnet mit den zuletzt beobachteten Werten: Wasser 1/3 → ein
teilgefülltes Segment (33 %); CO₂e 1,2× → ein volles + ein teilgefülltes
Segment (20 %); Energie 1,1× → ein volles + ein teilgefülltes Segment
(10 %) — die beiden zuvor optisch kaum unterscheidbaren "vollen" Ringe
(1,1× vs. 1,2×) sind jetzt über die Segmentgröße klar unterscheidbar.
Cache-Buster `v='31'`, `pytest` (79 Tests) grün, live verifiziert (neue
CSS-Klassen, `renderCupSegments()` und Segment-Container korrekt
ausgeliefert).

**Nachtrag 13 — Ring-Leuchtrand kaum sichtbar + echte Tassen-Silhouette
`[ERLEDIGT]`**: Live-Test von Nachtrag 12 zeigte, dass der `drop-shadow`-
Leuchtrand am Ring im dunklen Theme praktisch untergeht — "hübsch, aber man
sieht es nicht wirklich" (Nutzer-Feedback). Außerdem waren die
Segment-"Tassen" bisher nur generische abgerundete Balken, keine erkennbare
Tassenform.

**Fix 1 — Ring-Überlauf jetzt per Farbwechsel statt Glow.** `.ring-fill.overflow`
überschreibt die Metrik-Farbe (Blau/Grün/Rot) durch `var(--yellow)`
(bestehende Akzentfarbe), sobald `ratio >= 1` — ein klarer, kontraststarker
Farbtausch statt eines im Dunkeln kaum wahrnehmbaren Unschärfe-Effekts.
Funktioniert unabhängig vom Hintergrund, da es eine feste Deckfarbe ist,
kein Filter. Verzichtet bewusst auf Ring-Verdickung oder eine zweite
Ring-Geometrie (Radien/Abstände der drei verschachtelten Ringe sind mit nur
~2 Einheiten Lücke zwischen den Ringen zu eng für zusätzliche Geometrie,
ohne benachbarte Ringe optisch zu berühren).

**Fix 2 — echte Tassen-Silhouette statt Balken, außerdem größer.** Neue
gemeinsame SVG-Vorlage `CUP_ICON_SVG` (Tassenkörper-Pfad + Henkel-Pfad +
Umriss-Pfad), über `createCupSegment()` pro Segment eingefügt (`viewBox
0 0 24 28`, angezeigt bei 26×30px — deutlich größer als die vorherigen
13×17px-Balken, wie vom Nutzer vorgeschlagen "im Zweifel etwas größer").
Füllung weiterhin über dieselbe `--fill`-Custom-Property wie zuvor, jetzt
aber per CSS `clip-path:inset(calc(100% - var(--fill,0%)) 0 0 0)` auf den
Tassenkörper-Pfad angewendet statt auf ein Rechteck — füllt die Tasse
optisch von unten, wie eine Flüssigkeit. Leere Segmente (noch nicht
erreichte Vielfache) zeigen nur den Umriss in gedämpfter Farbe, keine
Füllung — bleiben aber als Tasse erkennbar, nicht als leerer Blindslot.

Cache-Buster `v='32'`, `pytest` (79 Tests) grün, live verifiziert (neue
SVG-Vorlage, `createCupSegment()`, CSS-Farbtausch-Regel und
`clip-path`-Füllregel korrekt ausgeliefert). Echte visuelle Beurteilung
(wirkt die Tassenform erkennbar, ist der Farbtausch jetzt deutlich genug)
steht noch aus — abhängig vom nächsten Live-Test des Nutzers.

**Nachtrag 14 — Ring in der 500er-Hochrechnung entfernt + "große nummerierte
Tasse" statt "+X,Y"-Text `[ERLEDIGT]`**: Nach dem Farbtausch-Fix blieb der
grundsätzliche Eindruck, dass der Ring als Konzept hier nicht überzeugt —
er löst sein eigenes Deckelungsproblem nicht so elegant wie die Tassen es
tun, und erfordert zusätzlich eine separate Farb-Legende. Entscheidung:
**Ring in der 500er-Hochrechnung ersatzlos entfernt** (der Ring in der
"Kosten und Nutzung"-Ansicht pro Konversation bleibt vorerst unverändert
bestehen — das war explizit nur ein erster Schritt, keine grundsätzliche
Ring-Abschaffung).

**Zusätzlich neue Idee des Nutzers, um den bisherigen "+X,Y"-Text-Fallback
zu ersetzen**: Statt bei mehr als 10 Tassen auf einen Bruchzahl-Text
umzusteigen, wird eine **volle Zehnerreihe durch eine einzelne größere
Tasse mit der Zahl "10" darin ersetzt** — dadurch bleibt die Darstellung
durchgehend eine ganze, leicht lesbare Zahl statt einer Nachkommastelle.
Weitere Anfragen füllen wieder eine neue Reihe kleiner Tassen, bis auch die
wieder zu einer großen "10"-Tasse wird (z. B. 23,4× → zwei große
"10"-Tassen + drei volle + eine 40 % gefüllte kleine Tasse = 23,4). Der
alte "+X,Y"-Text bleibt als **Fallback für den unwahrscheinlichen Fall**
erhalten, dass selbst das noch zu viele große Tassen ergäbe (> 5 große
Tassen, also > 50× — bei Bedarf zeigt die Reihe dann 5 große Tassen plus
"+X,Y" für den Rest), genau wie vom Nutzer gewünscht ("um dieses Szenario
abzufangen").

**Umsetzung**: `cupIconMarkup()` (vorher `CUP_ICON_SVG`-Konstante) nimmt
jetzt einen optionalen Zahlenparameter und rendert bei Bedarf ein
zentriertes `<text>`-Element in der Tasse (dunkle Schriftfarbe `#052015`
für Kontrast auf den hellen Pastellfarben, gleiches Prinzip wie der
bestehende `button.primary`-Text). `renderCupSegments()` neu strukturiert:
`bigCupCount = floor(ratio / 10)`, gedeckelt auf `maxBigCups = 5` sichtbare
große Tassen, darüber hinaus der Text-Fallback für den nicht mehr gezeigten
Rest. Große Tassen bekommen zusätzlich die Klasse `big` (`.cup-segment.big
.cup-icon` skaliert auf 40×46px statt 26×30px). `updateProjectedMetric()`
verliert den `ringId`-Parameter, `updateRing()`-Aufruf und die
zugehörige HTML-Struktur (zweiter Ring-Satz + Farb-Legende) für die
500er-Sektion sind komplett entfernt; die Ring-Infrastruktur selbst
(`updateRing()`, CSS-Klassen) bleibt unangetastet, da die "Kosten und
Nutzung"-Ringe sie weiterhin nutzen.

Rechnerisch nachgeprüft (Python-Simulation derselben Logik): 23,4 → zwei
große "10"-Tassen + drei volle + eine 40 %-Tasse; 60 → fünf große
"10"-Tassen + Text-Fallback "+10.0"; 3,0 → exakt drei volle Tassen, keine
leere Rest-Tasse (Rundungstoleranz beachtet). Cache-Buster `v='33'`,
`pytest` (79 Tests) grün, live verifiziert (keine 500x-Ring-IDs mehr im
ausgelieferten JS, neue Logik und CSS-Klassen korrekt vorhanden).

**Nachtrag 15 — Bugfix: "volle Reihe" passte nicht zur tatsächlichen
Bildschirmkapazität `[ERLEDIGT]`**: Live-Test zeigte falsch aussehende
Gruppierungen. Root Cause: `segmentsPerRow = 10` war eine reine Annahme,
wie viele Tassen "eine Zeile" ausmachen — wie viele tatsächlich in die
260px breite Statusleiste passen, hängt aber von Bildschirmauflösung und
Icon-Größe ab. Der Nutzer belegte das mit einem Vergleichs-Screenshot der
vorherigen (Vor-Nachtrag-14-)Implementierung: dort wickelte der
Flex-Zeilenumbruch bei ihm tatsächlich nach **7** Tassen um, nicht nach 10
— die Gruppierungslogik "volle Zeile → große Tasse" war damit von einer
falschen Kapazitätsannahme abhängig und lief bei anderen Auflösungen aus
dem Ruder.

**Fix**: `.cup-segments` von `display:flex` mit auflösungsabhängigem
`flex-wrap` auf `display:grid` mit fest **5 Spalten**
(`grid-template-columns:repeat(5,1fr)`) umgestellt — dadurch ist "eine
Zeile" immer exakt 5 Elemente, unabhängig von Bildschirmbreite oder
Icon-Größe. `segmentsPerRow` in `renderCupSegments()` entsprechend von 10
auf **5** reduziert, damit die logische Gruppierung ("eine große Tasse pro
voller Reihe") wieder zur tatsächlich gerenderten Zeile passt.
`maxBigCups` von 5 auf 8 erhöht (Ceiling vorher 50×, jetzt 40× — bei
kleinerer Gruppengröße sonst zu früh der Text-Fallback gegriffen hätte,
siehe die real beobachteten Werte um 12–13×). Rechnerisch nachgeprüft:
12,7× → zwei große "5"-Tassen + zwei volle + eine 70 %-Tasse (= 5 Elemente,
passt exakt in eine Grid-Zeile); 41× → acht große "5"-Tassen + eine volle
(wickelt korrekt in zwei Grid-Zeilen). Cache-Buster `v='34'`, `pytest`
(79 Tests) grün, live verifiziert (neue Werte und Grid-CSS-Regel korrekt
ausgeliefert).

**Nachtrag 16 — 500er-Ansicht reduziert: eigene Kachel, nur noch Tassen,
Legende statt Zahlen `[ERLEDIGT]`**: Nutzer-Feedback nach dem letzten
Live-Test: "passt so, perfekt" — als nächsten Schritt die Darstellung
bewusst verschlanken. Drei Änderungen:

1. **Exakte Werte entfernt.** Die kombinierte Zeile pro Metrik
   ("495.7 mL · ≈ 3.3× einer Tasse Tee") ist komplett weg — nur noch die
   Tassen-Segmentreihen selbst. `updateProjectedMetric()` dadurch stark
   vereinfacht (kein `textId`/`label`/`unit`/`decimals`-Parameter mehr,
   reine Verhältnisrechnung + `renderCupSegments()`-Aufruf).
2. **Eigene Kachel statt loser Sektion in der Statusleiste.** Die
   "500 KI-Anfragen"-Ansicht bekommt jetzt dieselbe `.panel`-Kartenoptik wie
   die oberen Einzelkacheln (`Fußabdruck`, `Prompt analysieren`) — als neue
   `.projection-panel`-Klasse innerhalb der bestehenden `.chat-summary`-Aside
   verschachtelt. Bewusst **eine** Kachel für alle drei Metriken zusammen,
   nicht drei einzelne wie beim oberen Fußabdruck-Panel ("wird sonst zu
   unruhig", Nutzer-Zitat) — die drei Tassenreihen stehen einfach
   übereinander in derselben Karte.
3. **Legende statt Beschriftung pro Zeile.** Da keine Zahlen mehr pro Zeile
   stehen, gibt es auch keine Label-Zeile ("💧 Wasser gesamt") mehr direkt
   über jeder Tassenreihe — stattdessen eine gemeinsame Legende unter einem
   `<hr>` am Kachelende (`💧 Wasser · 🌿 CO₂e · 🔋 Energie`, dieselben Icons
   wie überall sonst im Projekt), plus ein neuer Hinweis "Referenz: 150 mL
   Tasse heißer Tee." direkt darunter. Überschrift von "500 KI-Anfragen
   (hochgerechnet)" auf **"500 KI-Anfragen (Näherung)"** geändert. Der
   bestehende Testfassungs-Disclaimer ("keine reale Nutzerzahl-Prognose")
   bleibt unverändert erhalten — das war kein Teil der "reduzieren"-Bitte,
   sondern eine separate Ehrlichkeits-Kennzeichnung.

Cache-Buster `v='35'`, `pytest` (79 Tests) grün, live verifiziert (neue
Überschrift, Legende, Referenz-Hinweis und `.projection-panel`-CSS korrekt
ausgeliefert).

**Nachtrag 17 — Legende umbrach in zwei Zeilen + Testfassungs-Hinweis
entfernt `[ERLEDIGT]`**: Live-Test zeigte, dass die Farb-Legende
("💧 Wasser · 🌿 CO₂e · 🔋 Energie") in der schmalen `.projection-panel`
nicht in eine Zeile passte — Root Cause: die bisherige Legende
(wiederverwendete `.ring-legend`-Klasse) rendert jedes Element als eigenes
Flex-Item mit zusätzlichem farbigem Punkt (`<i>`) **und** Emoji **und**
Text, macht jedes Item unnötig breit für eine 260px-Statusleiste mit
24px-Kachel-Padding.

**Fix**: neue, schlankere Klasse `.cup-legend` — ein einzelner Fließtext-
Absatz ("💧 Wasser · 🌿 CO₂e · 🔋 Energie") statt drei Flex-Items mit
zusätzlichem Farbpunkt. Der Farbpunkt entfällt komplett — die Emoji
(💧/🌿/🔋) sind bereits die im ganzen Projekt etablierte Metrik-Kennzeichnung
und machen den zusätzlichen Punkt redundant, die Tassen selbst tragen die
Farbe ja ohnehin schon. Bewusst **kein** `white-space:nowrap` gesetzt (wäre
ein Clipping-Risiko, falls der Text bei einer bestimmten Auflösung doch
nicht ganz passt) — stattdessen normaler Textfluss, der im Zweifel an
einer Wortgrenze sauber umbricht statt wie zuvor ganze Flex-Items
abzuschneiden. Schriftgröße zusätzlich leicht reduziert (0,78 → 0,75rem).

Zusätzlich auf Nutzerwunsch entfernt: der Testfassungs-Disclaimer-Absatz
("hochgerechnet aus deiner bisherigen Nutzung … keine reale
Nutzerzahl-Prognose") unter dem Referenz-Hinweis — die Überschrift "500
KI-Anfragen (**Näherung**)" trägt die Ehrlichkeits-Kennzeichnung jetzt
allein. Nutzer-Entscheidung, das Design damit für diesen Bereich als
abgeschlossen zu betrachten ("wir werden das so behalten").

Cache-Buster `v='36'`, `pytest` (79 Tests) grün, live verifiziert (neue
`.cup-legend`-Klasse und entfernter Disclaimer-Text korrekt ausgeliefert —
verbleibende Codestellen mit dem Wort "Testfassung" sind nur interne
Kommentare, kein sichtbarer UI-Text mehr).

**Nachtrag 18 — Erklärender Hinweistext ergänzt `[ERLEDIGT]`**: Der Nutzer
fragte nach weiterem Optimierungsbedarf und schlug einen zusammenfassenden
Satz vor, was die Kachel eigentlich zeigt. Ursprünglicher Formulierungs-
vorschlag ("500 weitere Anwender stellen vergleichbare Anfragen") war
sprachlich naheliegend, aber nicht ganz präzise: `REQUEST_MULTIPLIER = 500`
wird auf die **kumulierte bisherige Nutzung im gesamten Chat**
(`cumulativeCo2/-Energy/-Water × 500`) angewendet, nicht auf eine einzelne
Anfrage — bei mehreren bereits gesendeten Nachrichten würde "500 Anfragen"
das Ergebnis unterschätzen (z. B. bei 5 bisherigen Nachrichten entspräche
die Hochrechnung eher 2.500 Einzelanfragen). Gemeinsam präzisierter Text:
**"Hochgerechnet: Fußabdruck, wenn deine bisherige Nutzung in diesem Chat
500 andere Anwender ebenfalls so ausführen würden."** — trifft die
tatsächliche Rechnung unabhängig davon, wie viele Nachrichten der Chat
bisher enthält.

**Umsetzung**: neuer `<p class="meter-note">`-Absatz, dezent unterhalb von
"Referenz: 150 mL Tasse heißer Tee." ergänzt (gleiche kleine, gedämpfte
Textdarstellung), Kachel-Kopf (Überschrift → Tassen → Legende) bleibt
dadurch unverändert clean. Cache-Buster `v='37'`, `pytest` (79 Tests)
grün, live verifiziert (neuer Erklärtext korrekt ausgeliefert).

**Nachtrag 19 — Sidebar neu strukturiert: EcoLogits-Werte als eigene Kachel
`[ERLEDIGT]`**: Nutzer wollte die restliche Statusleiste konsistent zur
"500 KI-Anfragen"-Kachel gestalten, damit man den eigenen Chatverlauf und
die Hochrechnung im selben Stil nebeneinander sieht. Neue Struktur (drei
Blöcke statt zwei in derselben `.chat-summary`-Aside):

1. **"Kosten und Nutzung"** — jetzt nur noch Kosten-/Token-Werte (Letzte
   Runde, Input, Output, Gesamtkosten, Gesamttoken). Ring und die
   CO₂e-/Energie-/Wasser-Zeilen samt Balken sind hier raus.
2. **Neue Kachel "Fußabdruck dieser Unterhaltung"** (`.panel
   .projection-panel`, gleiche Kartenoptik wie die "500 KI-Anfragen"-Kachel
   und die oberen Einzelkacheln) — enthält den bestehenden Ring (Wasser/
   CO₂e/Energie, unverändert übernommen, **nicht** entfernt, anders als bei
   der 500er-Ansicht), darunter ein `<hr>`, dieselbe kompakte
   `.cup-legend`-Zeile wie bei der 500er-Kachel ("💧 Wasser · 🌿 CO₂e ·
   🔋 Energie"), derselbe Referenz-Hinweis ("Referenz: 150 mL Tasse heißer
   Tee.") und die "Letzte Runde: EcoLogits DB"-Indikatorzeile (thematisch
   hierher verschoben, vorher lose zwischen den Balken).
3. **"500 KI-Anfragen (Näherung)"** — unverändert.

**Bewusst keine Balken und keine Einzelwerte mehr in der neuen Kachel** —
genau wie bei der 500er-Ansicht nur Ring + gemeinsame Legende + Referenz,
keine "0,0669 g"/"≈ 1/78"-Texte pro Metrik mehr. Deckt sich mit dem
Reduktions-Wunsch aus Nachtrag 16, jetzt konsequent auch für die
Pro-Konversations-Ansicht angewendet.

**Aufräumen als Folge**: `updateReferenceMeter()` und `fractionLabel()`
wurden dadurch vollständig ungenutzt (einzige Aufrufstellen waren die jetzt
entfernten Balken-Zeilen) — beide Funktionen komplett entfernt statt als
toter Code liegen zu bleiben. `recordUsage()` ruft jetzt direkt `updateRing()`
mit inline berechnetem Verhältnis auf. Ebenso vollständig ungenutzt und
entfernt: die CSS-Klassen `.meter`, `.meter-fill` (+ Farbvarianten) und
`.ring-legend` (+ Punkt-Varianten) — `.meter-note` (für die Referenz-/
Erklärtexte) bleibt bestehen, wird weiterhin gebraucht.

Cache-Buster `v='38'`, `pytest` (79 Tests) grün, live verifiziert (neue
Kachel-Überschrift ausgeliefert, keine toten ID-Referenzen mehr im JS,
keine toten CSS-Regeln mehr in `style.css`).

**Nachtrag 20 — Kompakte Werte-Zeile zurück in "Fußabdruck dieser
Unterhaltung" `[ERLEDIGT]`**: Frage des Nutzers: fehlt hier der
Sensibilisierungsfaktor, wenn komplett auf Zahlen verzichtet wird? Wichtige
Unterscheidung zur "500 KI-Anfragen"-Kachel: diese Kachel zeigt **echte,
tatsächlich gemessene** Werte für die laufende Unterhaltung, keine
Näherung/Hochrechnung — anders als bei der bewusst zahlenfreien
500er-Ansicht spricht hier nichts dagegen, die Zahl als faktische
Verankerung neben dem intuitiven Ring zu zeigen (ähnliches Muster wie
Ring+Zahl in Fitness-/Health-Apps). Ausdrücklich **nicht** die alte,
"unruhige" Darstellung (drei fette Überschriften + Balken + Bruch-Text pro
Metrik) reaktiviert, sondern eine einzige kompakte, gedämpfte Textzeile mit
allen drei Werten und den etablierten Icons: "💧 X mL · 🌿 X g · 🔋 X Wh",
direkt unter dem Ring, vor dem Trennstrich. Neues Element
`#chat-eco-values`, befüllt in `recordUsage()` direkt aus den bereits
vorhandenen `cumulativeWater`/`cumulativeCo2`/`cumulativeEnergy`-Werten
(keine neue Berechnung nötig). Cache-Buster `v='39'`, `pytest` (79 Tests)
grün, live verifiziert.

**Nachtrag 21 — Werte-Zeile und Legende zusammengelegt `[ERLEDIGT]`**:
Live-Test zeigte zwei Probleme mit Nachtrag 20: (1) Werte-Zeile und
Legende zeigten dieselben drei Icons doppelt ("💧 0,4055 mL …" direkt über
"💧 Wasser · 🌿 CO₂e · 🔋 Energie") — redundant. (2) Die einzeilige
Werte-Zeile ("💧 X mL · 🌿 X g · 🔋 X Wh") passte je nach Wertlänge nicht
immer in die 260px-Statusleiste und brach mitten im Element um (Icon vom
zugehörigen Wert getrennt sichtbar im Screenshot).

**Fix**: Werte-Zeile und Legende zu **drei separaten Zeilen** zusammengelegt
— jede Zeile kombiniert Icon, Label und Wert in einem ("💧 Wasser ·
**0,4055 mL**", "🌿 CO₂e · **0,0546 g**", "🔋 Energie · **0,1550 Wh**"),
untereinander statt nebeneinander. Behebt beide Probleme gleichzeitig: kein
Icon mehr doppelt gezeigt, und jede Zeile ist kurz genug, um zuverlässig in
eine Zeile zu passen, unabhängig von der Werte-Länge. Reihenfolge bewusst
identisch zur Tassen-Reihenfolge in der "500 KI-Anfragen"-Kachel (Wasser →
CO₂e → Energie), damit beide Kacheln konsistent wirken. Die separate
`.cup-legend`-Zeile in dieser Kachel entfällt komplett (bleibt für die
500er-Kachel unverändert bestehen, wo es keine Werte-Redundanz gibt).

**Umsetzung**: drei neue Elemente `#chat-eco-water`/`#chat-eco-co2`/
`#chat-eco-energy` statt des einen kombinierten `#chat-eco-values`-Absatzes;
`recordUsage()` entsprechend angepasst. Cache-Buster `v='40'`, `pytest`
(79 Tests) grün, live verifiziert.

**Nachtrag 22 — Feinjustierung: Abstand vor dem Trennpunkt bei "CO₂e"
`[ERLEDIGT]`**: Das tiefgestellte "₂" ließ den Abstand vor dem "·" optisch
knapper wirken als bei "Wasser ·"/"Energie ·", obwohl der Quelltext
identische Leerzeichen enthielt. Ein einfaches doppeltes Leerzeichen hätte
nichts bewirkt (Browser fassen mehrere Leerzeichen im HTML zu einem
zusammen) — stattdessen ein geschütztes Leerzeichen (`&nbsp;`) nach "CO₂e"
ergänzt, das tatsächlich zusätzlichen sichtbaren Abstand erzeugt. Cache-Buster
`v='41'`, `pytest` (79 Tests) grün, live verifiziert.

**Nachtrag 23 — "Kosten und Nutzung" ebenfalls in eine `.panel`-Kachel
verpackt `[ERLEDIGT]`**: Letzter Schritt zur durchgängigen Konsistenz der
Statusleiste. Vorher lag "Kosten und Nutzung" (Letzte Runde/Input/Output/
Gesamtkosten/Gesamttoken) lose direkt in der äußeren gestrichelten
`.chat-summary`-Aside, während "Fußabdruck dieser Unterhaltung" und
"500 KI-Anfragen" bereits als solide `.panel`-Karten davon abgesetzt waren
— optisch uneinheitlich (ein loser Block + zwei Karten). Diskutierte
Alternative (Kosten und Fußabdruck in einer gemeinsamen Karte
zusammenlegen) wurde bewusst verworfen, um Geld- und Umwelt-Kennzahlen
nicht wieder zu vermischen, nachdem genau diese Trennung in den vorherigen
Schritten bewusst erarbeitet wurde.

**Umsetzung**: Inhalt von "Kosten und Nutzung" unverändert (keine
Feldänderungen), nur in ein zusätzliches `<div class="panel
projection-panel">` verpackt — jetzt drei gleich gestaltete Karten
übereinander in der Statusleiste. Da `.projection-panel{margin-top:18px}`
jetzt auch auf die erste Karte träfe (doppelter Abstand zusammen mit dem
Padding der äußeren Aside), zusätzliche Regel `.chat-summary>
.projection-panel:first-child{margin-top:0}` ergänzt. Der äußere
gestrichelte Rahmen der Statusleiste bleibt bewusst bestehen (Nutzer-
Entscheidung: "behalten wir erstmal bei") — wirkt jetzt als lockere
Klammer um die drei Karten statt als eigener Inhaltsträger.

Cache-Buster `v='42'`, `pytest` (79 Tests) grün, live verifiziert (alle
drei Karten mit einheitlicher `.panel projection-panel`-Struktur korrekt
ausgeliefert).

**Nachtrag 24 — CodeCarbon-Idee verworfen, stattdessen eigene lokale
Energie-/CO2-Formel für Ollama-Sends `[ERLEDIGT]`**: Der ursprüngliche
Plan aus `docs/carbon_tool_eval.md` sah CodeCarbon für die lokale
Voranalyse (Ollama-Call in `/api/analyze`) vor. Im Gespräch kam der
begründete Einwand, dass ein zusätzlicher Fußabdruck-Wert für den
Analyse-Hintergrundschritt selbst kein sinnvoller Mehrwert ist — er ist
kein Teil der bewussten Sende-Entscheidung und würde nur mit der
eigentlichen "Fußabdruck dieses Requests"-Anzeige konkurrieren. Der Scope
wurde daraufhin verschoben: sinnvoll ist ein echter Wert dort, wo er
bisher fehlt — beim tatsächlichen lokalen Versand an Ollama (EcoLogits
deckt nur Cloud-/API-Provider ab), um lokal vs. Cloud vergleichbar zu
machen.

**CodeCarbon dafür geprüft und verworfen**: CodeCarbon misst reale
Hardware-Energie nur über RAPL (Linux/Intel) oder das veraltete Intel
Power Gadget. Die Entwicklungsmaschine hier hat einen AMD Ryzen 7 8840U
ohne dedizierte GPU (`nvidia-smi` nicht vorhanden) — unter dieser
Konstellation fällt CodeCarbon selbst auf einen CPU-TDP-Tabellen-Schätzwert
× Auslastung zurück, also wieder nur eine Formel-Schätzung statt der
realen Messung, die in `carbon_tool_eval.md` das eigentliche
Alleinstellungsmerkmal von CodeCarbon gegenüber EcoLogits war. Damit
entfiel der Grund, die zusätzliche (schwerere) Abhängigkeit
(`requests`, `pynvml`, `arrow` u. a.) einzuführen.

**Entscheidung**: eigene, deutlich leichtgewichtigere Formel statt
CodeCarbon — CPU-Auslastung via `psutil` (plattformunabhängig, keine
Admin-Rechte nötig) direkt vor/nach dem `generate()`-Call gemessen,
kombiniert mit einer manuell konfigurierbaren CPU-TDP (`LOCAL_CPU_TDP_WATT`,
**kein** erfundener Default — ohne Wert bleibt die Anzeige bewusst "nicht
verfügbar", statt eine Zahl vorzutäuschen, analog zu den bestehenden
manuellen EcoLogits-Parametern). CO2 wird daraus wie überall sonst im
Projekt über die vorhandene `CARBON_INTENSITY_G_PER_KWH`-Konstante
abgeleitet (`app/services/local_energy_service.py`). Diese Formel ist
in der Genauigkeit CodeCarbons eigenem Fallback auf dieser Hardware
gleichwertig (beides TDP × Auslastung), aber transparent nachvollziehbar
statt einer Blackbox-Library-internen Logik.

**Wasser/ADPe bleiben strukturell unerreichbar** — sowohl CodeCarbon als
auch die eigene Formel modellieren nur Energie/CO2 aus Laufzeit-
Stromverbrauch. Wasserverbrauch (Kühlung im Rechenzentrum) und ADPe
(Rohstoffverbrauch der Hardwareherstellung) sind Lifecycle-Konzepte aus
EcoLogits/Boavizta, die keine CPU-Auslastungsmessung je liefern kann —
das ist kein Implementierungsdetail, das später nachgerüstet werden
könnte, sondern ein methodischer Scope-Unterschied.

**Priorität gegenüber EcoLogits**: Ist für ein Ollama-Modell bereits
`eco_active_params_b`/`eco_total_params_b` gepflegt (z. B. bekanntes
Llama-Modell mit bekannter Parameterzahl), liefert `compute_impacts()`
weiterhin ein vollständiges EcoLogits-Ergebnis inkl. Wasser/ADPe — das
hat Vorrang, da es die informativere Schätzung ist. Die lokale
CPU-Formel greift nur als Fallback, wenn EcoLogits nichts liefert (der
Regelfall bei lokalen Modellen ohne hinterlegte Parameterzahl).

**Umsetzung**: `app/services/local_energy_service.py::measure_local_generation()`
(neu), `LOCAL_CPU_TDP_WATT`-Konfig (`config.py`, `.env.example`, kein
Default), Fallback-Verdrahtung in `POST /api/send` (`app/routes/api.py`)
nur für `provider_type == "ollama"` und nur wenn `compute_impacts()`
`None` liefert. Neuer `sustainability.mode`-Wert `"local_cpu_estimate"`,
Frontend-Label "Lokale CPU-Schätzung" in `ecoIndicatorLabel()` ergänzt.
Neue Abhängigkeit: `psutil` (deutlich leichter als `codecarbon`).

Tests: `tests/test_local_energy_service.py` (neu, 3 Tests) + 3 neue
Tests in `tests/test_routes.py` (Fallback ohne manuelle EcoLogits-Parameter,
Warnung bei fehlender `LOCAL_CPU_TDP_WATT`-Konfiguration, EcoLogits-Vorrang
bei vorhandenen manuellen Parametern). Cache-Buster `v='43'`, `pytest`
(85 Tests) grün, live verifiziert (Label und Cache-Buster korrekt
ausgeliefert).

**Nachtrag 25 — Bugfix: Kacheln zeigten Werte für einen Sekundenbruchteil,
fielen dann auf "nicht verfügbar" zurück `[ERLEDIGT]`**: Live-Test von
Nachtrag 24 (Prompt "Was ist ein Gnu?", Zielmodus "lokales Ollama-Modell").

**Ursache**: Zwei nacheinander laufende Requests aktualisieren dieselben
Kacheln mit unterschiedlichen Datenquellen. (1) `/api/analyze` →
`sustainability_for()` nutzt den **Modell-Katalogeintrag** (`local-small`/
`local-large` in `model_catalog.py`) mit fest hinterlegten Demo-EcoLogits-
Parametern (`eco_active_params_b: 3`, `eco_total_params_b: 3`) → liefert
sofort ein volles Ergebnis. (2) `render()` wählt danach automatisch den
passenden Ollama-Provider im Dropdown und triggert `selectedProviderEstimate()`
→ `/api/estimate-footprint` mit `provider_id` → `estimate_footprint_for_provider()`
nutzt stattdessen die **echte `ProviderConfiguration`** aus der Datenbank.
Ist dort (wie im konkreten Testfall) nur `eco_total_params_b` gepflegt, aber
nicht `eco_active_params_b`, bricht `_compute_via_manual_parameters()` in
`ecologits_service.py` sofort mit `None` ab (beide Werte sind Pflicht) —
die Kacheln fallen auf "–"/"nicht verfügbar" zurück. Der neue lokale
CPU-Formel-Fallback aus Nachtrag 24 greift hier bewusst nicht: er braucht
einen echten `generate()`-Aufruf zum Messen, den es bei einer reinen
Vorab-Schätzung (`/api/estimate-footprint`) nicht gibt (siehe
`test_estimate_footprint_requires_no_ollama_call`).

**Entscheidung**: `estimate_footprint_for_provider()` bekommt denselben
Formel-Fallback wie `sustainability_for()` an anderer Stelle im Code —
statt hart auf "nicht verfügbar" zu fallen, wenn die reale Provider-
Konfiguration unvollständig ist, wird (sofern eine `model_class` bekannt
ist) zusätzlich die generische Token-Formel aus `sustainability_service.py`
berechnet und mit einem eventuellen EcoLogits-Ergebnis gemerged — genau wie
beim ursprünglichen `/api/analyze`-Aufruf. EcoLogits bleibt Vorrang, wenn
verfügbar (überschreibt die Formel-Werte inkl. Wasser/ADPe); ist es nicht
verfügbar, bekommt das Ergebnis den neuen `mode`-Wert `"formula"`, damit
der Indikator nicht fälschlich "Nicht verfügbar" trotz angezeigter Zahlen
meldet.

**Umsetzung**: `estimate_footprint_for_provider()` (`app/routes/api.py`)
bekommt einen optionalen `model_class`-Parameter, sucht damit den
passenden `MODELS`-Katalogeintrag für die Formel-Konstanten
(`input_energy`/`output_energy`), mergt wie gehabt. `POST /api/estimate-footprint`
reicht `model_class` aus dem Request-Body durch. Frontend
(`refreshTilesForSelectedProvider()`, `estimateChatFootprint()` in
`dashboard.js`) sendet jetzt `model_class: last.recommendation.model_class`
mit, sofern bereits eine Analyse vorliegt. Neuer Indikator-Text "Grobe
Schätzung" für `mode === "formula"`.

Tests: 2 neue in `tests/test_routes.py` (Formel-Fallback bei
unvollständiger Provider-Konfiguration, EcoLogits-Vorrang bleibt erhalten,
wenn vollständig konfiguriert). Cache-Buster `v='44'`, `pytest` (87 Tests)
grün, live verifiziert (Provider mit nur `eco_total_params_b` angelegt,
`/api/estimate-footprint` liefert ohne `model_class` weiterhin `null`
(Rückwärtskompatibilität), mit `model_class` jetzt `mode: "formula"` mit
echten Zahlen statt "nicht verfügbar").

**Nachtrag 26 — Bugfix: "Fußabdruck dieser Unterhaltung" zeigte
"0.0000 mL" statt "nicht verfügbar" bei lokaler CPU-Schätzung
`[ERLEDIGT]`**: Folgefund aus demselben Live-Test wie Nachtrag 25. Der
lokale CPU-Formel-Fallback (Nachtrag 24) liefert nie `water_ml` (siehe
dortige Begründung: Wasserverbrauch ist ein Lifecycle-Konzept, keine
Auslastungsmessung kann es beantworten). `recordUsage()` behandelte
fehlendes `water_ml` bisher wie "0 mL zu dieser Runde", nicht wie
"unbekannt" — die kumulierte Wasseranzeige zeigte dadurch "0.0000 mL"
statt ehrlich "nicht verfügbar" zu sein, obwohl in Wahrheit gar nichts
gemessen wurde.

**Fix**: Neue Zustandsvariable `cumulativeWaterAvailable` (Default `true`,
wie die anderen `cumulative*`-Variablen bei neuem Chat zurückgesetzt).
Sobald `data.sustainability` zwar vorhanden ist, aber `water_ml` darin
fehlt (lokale CPU-Schätzung), kippt sie dauerhaft auf `false` für den Rest
der Unterhaltung — ein einziges Turn ohne Wasserwert macht die kumulierte
Summe unvollständig, nicht nur diesen einen Beitrag. Anzeige in
`recordUsage()` entsprechend auf `cumulativeWaterAvailable ? ... : "–"`
umgestellt. Bewusst nur die Textzeile in "Fußabdruck dieser Unterhaltung"
angepasst (wie angefragt) — Ring und 500er-Tassen-Hochrechnung für Wasser
nicht angefasst, das war nicht Teil der Anfrage.

Cache-Buster `v='45'`, `pytest` (87 Tests, unverändert, kein Backend-Fix)
grün, live verifiziert (`cumulativeWaterAvailable`-Logik korrekt
ausgeliefert).

**Nachtrag 27 — Bugfix: Ollama-Sendevorgang lieferte leere `{}`-Antwort
(erzwungenes JSON-Format) `[ERLEDIGT]`**: Beim Live-Test von Nachtrag 24/25
("Was ist ein Gnu?" über lokalen Ollama-Provider) kam als Antwort nur `{}`
zurück. Bereits vor dieser Session in `Tasklist.md` als niedrig priorisierter
Bug dokumentiert (dort noch mit der Symptomvariante "Antwort auf Englisch,
verschachtelte JSON-Struktur" statt leerem `{}` — gleiche Ursache, je nach
Modell/Prompt unterschiedliche Ausprägung).

**Ursache**: `OllamaService.generate()` (`app/services/ollama_service.py`)
setzte `"format":"json"` fest und unbedingt für jeden Aufruf. Die Methode
wird von zwei Aufrufern geteilt: `analyze_with_ollama()` (interne
Prompt-Analyse, JSON-Ausgabe tatsächlich gewollt) und
`OllamaProvider.generate()` (der echte Sendevorgang, wo eine normale
Fließtext-Antwort erwartet wird). Der erzwungene JSON-Modus zwang auch
echte Chat-Antworten in ein JSON-Korsett — ohne vorgegebenes Schema
antwortet das Modell dann bestenfalls mit verschachtelten Fantasie-Keys,
schlimmstenfalls mit einem leeren `{}`.

**Fix**: `generate()` bekommt einen `json_mode: bool = False`-Parameter;
`"format":"json"` wird nur noch bei `json_mode=True` in den Request-Body
aufgenommen. `analyze_with_ollama()` ruft jetzt explizit
`service.generate(redacted, SYSTEM_PROMPT, json_mode=True)`.
`OllamaProvider.generate()` (echter Sendevorgang) bleibt unverändert und
läuft damit automatisch ohne erzwungenes JSON.

Tests: `tests/test_ollama_service.py` (neu, 2 Tests: `format` fehlt ohne
`json_mode`, ist gesetzt mit `json_mode=True`). `pytest` (89 Tests) grün.
`Tasklist.md`-Eintrag als erledigt markiert.

**Nachtrag 28 — Zwei begleitende Kostenkalkulations-Funde beim selben
Live-Test `[ERLEDIGT]`**: Derselbe Test zeigte einen unerwarteten Preis
("$ 0.000014") für einen lokalen, eigentlich kostenlosen Ollama-Send.
Zwei unabhängige Ursachen gefunden:

**Fund 1 — Provider-Formular-Default**: `providers.html` belegt
"Input-Preis"/"Output-Preis" statisch mit `1`/`5` (\$/Mio. Token) vor —
sinnvoll als Anthropic-Vorschlag, bleibt aber unbemerkt stehen, wenn beim
Anlegen eines lokalen Ollama-Providers nicht manuell auf `0` korrigiert
wird. Fix: `providers.js` bekommt einen `change`-Listener auf
`#provider-type`, der Input-/Output-Preis automatisch auf `0` setzt,
sobald "Lokales Ollama" gewählt wird. Nur bei aktiver Nutzerauswahl (nicht
beim programmatischen Vorbefüllen in `edit()`, da `.value =` keine
`change`-Events auslöst).

**Fund 2 — Währungssymbol hartkodiert**: Die Chat-Kostenanzeigen
("Kosten dieser API-Antwort", "Gesamtkosten" etc.) zeigten unabhängig vom
tatsächlichen Provider immer "\$", obwohl `/api/send` bereits korrekt
`cost_currency` liefert ("USD" nur für Anthropic, sonst "EUR"). Neue
Hilfsfunktion `currencySymbol(currency)` in `dashboard.js`,
`appendChatMessage()` bekommt einen `currency`-Parameter,
`recordUsage()` merkt sich die zuletzt gemeldete Währung
(`lastCostCurrency`, zurückgesetzt bei neuem Chat) für alle
`#chat-*-cost`-Felder inkl. Gesamtkosten.

Cache-Buster `v='46'` (`dashboard.js`), `providers.js` eigener
Cache-Buster `v='3'`. `pytest` (89 Tests) grün, live verifiziert (beide
Änderungen korrekt ausgeliefert).

**Nachtrag 29 — Indikator pro Kachel statt pauschal pro Ergebnis
`[ERLEDIGT]`**: Die oberen Fußabdruck-Kacheln zeigten bei lokaler
CPU-Schätzung/Formel-Fallback für Wasser und ADPe "Grobe Schätzung" bzw.
"Lokale CPU-Schätzung" neben "–" — irreführend, da beide Modi diese
Felder strukturell nie liefern (siehe Nachtrag 24/25), es also gar keine
Schätzung gibt, die den Indikator rechtfertigt.

**Fix**: `renderSustainabilityTiles()` wertet den Indikator jetzt pro
Kachel aus (`indicatorFor(value)`) statt einmal pauschal für alle vier —
zeigt "Nicht verfügbar", wenn das jeweilige Feld selbst `null` ist,
unabhängig vom `mode` des Gesamtergebnisses. Wirkt sich nur auf Wasser/
ADPe bei Formel-/lokaler-CPU-Schätzung aus; CO₂e/Energie sind bei jedem
aktuellen Modus immer gefüllt, wenn `sustainability` überhaupt vorhanden
ist, daher unverändertes Verhalten dort.

Cache-Buster `v='47'`, `pytest` (89 Tests, unverändert) grün, live
verifiziert.

**Nachtrag 30 — Entscheidung: ADPe bleibt bewusst außerhalb der
kumulierten Statusleiste `[ERLEDIGT]`**: Der Backlog-Punkt "ADPe fehlt in
der kumulierten Statusleiste" war seit der Tasse-Tee-Einführung offen —
zur Diskussion stand, ob das für die "Fußabdruck dieser Unterhaltung"-
Karte aus Konsistenzgründen zu den oberen Kacheln (die alle vier Werte
zeigen) nachgeholt werden sollte.

**Entscheidung**: Nein, ADPe bleibt exklusiv in den oberen Kacheln. Zwei
Gründe: (1) ADPe (µg Sb-Äq.) ist kein für Endnutzer intuitiv einordbarer
Wert — genau das hatte schon zum Ausschluss aus der 500er-Hochrechnung
geführt. (2) Die Chat-Gesamtmetrik ist keine technische Rohdaten-Anzeige
wie die oberen Kacheln, sondern bewusst auf die Tasse-Tee-Erzählung
zugeschnitten (Ringe, Icons, Alltagsbezug für CO₂/Energie/Wasser) — ein
Wert ohne passende Alltagsreferenz wäre dort ein Fremdkörper. Die
oberen Kacheln und die Chat-Karte haben unterschiedliche Aufgaben
(neutrale Einzelanalyse vs. Sensibilisierungs-Erzählung) und müssen
deshalb nicht dieselben Felder zeigen — der ursprüngliche
Konsistenz-Gedanke wurde bewusst verworfen.

Keine Code-Änderung, reine Backlog-Entscheidung — der entsprechende
Punkt in der Checkliste unten ist damit erledigt (nicht implementiert,
sondern bewusst nicht umzusetzen beschlossen).

**Nachtrag 31 — Entscheidung: keine Anzeige des lokalen
Analyse-Fußabdrucks am Dashboard, in keiner Form `[ERLEDIGT]`**: Ausgangspunkt
war der Backlog-Punkt "eigene 'Stromkosten'-Kachel für den lokalen
Sende-Fall", seit der `psutil`-Formel (Nachtrag 24) technisch möglich.
Diskutierter Vorschlag: keine eigene Kachel, sondern dezent unter dem
Prompt-Fenster (analog zur Zeichen-/Token-Zeile) Wh und CO2 mit Icons
auflisten — Fokus des Boards bleibt auf dem Versand, lokal nur als
kleiner Zusatzhinweis.

**Zwei Varianten geprüft, beide verworfen**:

1. **Echte `psutil`-Messung des Analyse-Aufrufs.** Mehrere konkrete
   Probleme: (a) Die Prompt-Analyse läuft über das fest konfigurierte
   `OLLAMA_MODEL` **immer**, unabhängig vom gewählten Zielmodus — auch
   bei "Externe Cloud-API" würde eine lokale Wh/CO2-Zahl erscheinen, die
   mit der eigentlichen Sende-Entscheidung nichts zu tun hat. (b) Das
   Analyse-Modell ist nicht dasselbe wie das vom Nutzer für den
   tatsächlichen Versand konfigurierte Ollama-Modell — die Messung würde
   das falsche Modell abbilden. (c) Der Analyse-Workload (langer fixer
   `SYSTEM_PROMPT`, erzwungene JSON-Struktur, kurze Ausgabe) unterscheidet
   sich stark vom tatsächlichen Sende-Workload. (d) `psutil.cpu_percent()`
   ist über die kurzen Analyse-Laufzeiten hinweg messtechnisch verrauscht
   — Gefahr sichtbar unterschiedlicher Werte bei identischem Prompt.
2. **Formel-Schätzung für den Analyse-Schritt selbst** (statt für das
   künftige Sende-Ziel, wie ursprünglich in Nachtrag 25 gemeint). Löst
   Probleme (a)–(c) nicht: die Zahl bliebe unabhängig vom Zielmodus
   sichtbar und würde weiterhin ein anderes Modell/einen anderen Workload
   als den echten Versand abbilden. Zusätzlich technisch lückenhaft: es
   gibt keine Energie-pro-Token-Konstanten für das konkret konfigurierte
   `OLLAMA_MODEL`, nur illustrative Katalog-Demowerte für `local_small`/
   `local_large`, die nicht zwangsläufig zum echten Analyse-Modell passen.

**Übergeordneter Punkt, unabhängig von der Datenquelle**: Beide Varianten
laufen auf dieselbe bereits einmal verworfene Idee hinaus ("Frontend-
Darstellung des Analyse-Fußabdrucks ... Information Overload, kein Teil
der bewussten Sende-Entscheidung", siehe weiter oben in diesem Dokument).
Der Verbrauch des internen Klassifikations-Schritts ist unabhängig von
Messmethode oder Prominenz der Darstellung keine für die Sensibilisierung
des Nutzers relevante Information, da sie nicht das abbildet, worüber der
Nutzer tatsächlich entscheidet (welches Modell/welcher Anbieter für den
Versand).

**Entscheidung**: Kein lokaler Analyse-Fußabdruck am Dashboard, in keiner
Form. Der lokale Sende-Fall bleibt weiterhin ausschließlich über die
bereits bestehenden Mechanismen abgedeckt (obere Kacheln nach Analyse,
tatsächliche Werte nach echtem Versand via `local_energy_service.py`,
siehe Nachtrag 24) — kein zusätzliches, separates Element dafür.

Keine Code-Änderung, reine Backlog-Entscheidung.

**Nachtrag 32 — `RATIO`-Kalibrierung: CLI-Kommando statt Feature-Route
`[ERLEDIGT]`**: Letzter offener EcoLogits-Punkt aus der Checkliste.
`EXPECTED_OUTPUT_RATIO` ist seit Einführung ein Platzhalterwert (`6`,
`config.py`); die Kalibrierung aus echten `UsageLog`-Daten war von Anfang
an als spätere Aufgabe vorgesehen, sobald genug Nutzungsdaten vorliegen.

**Berechnung**: Median aus `estimated_output_tokens / input_tokens` über
alle `UsageLog`-Einträge mit `request_status == "success"`. Median statt
Mittelwert wegen erwarteter Schiefe der Ausgabelängen-Verteilung (viele
kurze, wenige sehr lange Antworten). Wichtig: `estimated_output_tokens`
ist trotz des (historisch gewachsenen) Feldnamens bei echten Sends der
tatsächlich beobachtete Output (`app/routes/api.py::send()` — aus
Anthropics Usage-Stats oder `estimate_tokens()` auf die reale Antwort),
kein Zirkelschluss auf die bisherige Schätzung selbst.

**Form**: Flask-CLI-Kommando `flask calibrate-ratio`
(`app/__init__.py`), Logik in neuem
`app/services/ratio_calibration_service.py::calibrate_expected_output_ratio()`.
Bewusst kein Endpoint/keine UI — gelegentliche Wartungsaufgabe, kein
laufendes Feature. Das Kommando liest nur und gibt eine Empfehlung aus;
die Übernahme in `.env` bleibt ein manueller Schritt. Mindeststichprobe
20 Erfolgs-Sends als Schutz gegen Kalibrierung auf statistisch
bedeutungslosem Rauschen — darunter klare Meldung statt einer unseriösen
Zahl. Zeilen mit `input_tokens == 0` werden übersprungen
(Division-durch-Null-Schutz).

**Status der eigenen Instanz geprüft**: `instance/gateway.db` hatte zum
Zeitpunkt der Umsetzung 0 Einträge in `usage_log`, und
`ENABLE_PROMPT_LOGGING` stand auf `false` — es gab schlicht noch keine
Daten zum Kalibrieren. Auf Nutzerwunsch zusätzlich `ENABLE_PROMPT_LOGGING=true`
in der lokalen `.env` gesetzt, damit ab jetzt Daten für eine spätere
Kalibrierung gesammelt werden. `.env.example` bewusst unverändert (Default
bleibt `false`, Privacy-by-Design für neue Installationen).

Tests: `tests/test_ratio_calibration_service.py` (neu, 6 Tests: kein Datensatz,
Median-Berechnung, ignoriert fehlgeschlagene Sends, ignoriert
`input_tokens == 0`, CLI-Ausgabe bei fehlenden Daten, CLI-Ausgabe mit
Vorschlag). `pytest` (95 Tests) grün. Live verifiziert: `flask
calibrate-ratio` gegen die echte lokale DB meldet korrekt "Zu wenig
Daten" bei 0 Einträgen.

Damit ist die EcoLogits-bezogene Aufgabenliste in diesem Dokument
vollständig abgearbeitet — offene Punkte, die noch bleiben, betreffen
andere Themenbereiche (Prompt-Flow-UX, Fehlermeldungen).

**Nachtrag 33 — Bugfix: Wasser-Tasse in der 500er-Hochrechnung verschwand
komplett bei kleinem Anteil `[ERLEDIGT]`**: Beim finalen Test-Durchlauf
gemeldet: erst lokaler Ollama-Send (Wasser erwartungsgemäß "nicht
verfügbar"), dann ein externer Anthropic-Send — die Wasser-Tasse blieb
trotz gültiger Daten leer. Vermutet wurde ein Cache-/Refresh-Problem.

**Ursache**: keine Cache-Frage, sondern eine feste Schwelle in
`renderCupSegments()` (`app/static/js/dashboard.js`): ein Teil-Tassen-
Segment wurde nur gezeichnet, wenn der Rest-Anteil `remainder > 0.02`
(> 2 %) war. Bei diesem konkreten Prompt lag der Wasser-Anteil (0,0053 mL
von 150 mL Referenz × `REQUEST_MULTIPLIER` 500) bei nur ~1,8 % — unter der
Schwelle, Container blieb leer. CO₂ (~8,6 %) und Energie (~6,7 %) lagen
zufällig darüber und blieben deshalb sichtbar. Reiner Größenordnungs-
Zufall dieses einzelnen Prompts, kein lokal/extern-Unterschied.

**Fix**: Schwelle von `remainder > 0.02` auf `remainder > 0` reduziert —
jeder echte, positive Anteil zeigt jetzt mindestens eine minimal gefüllte
Teil-Tasse (Kontur bleibt in der jeweiligen Metrik-Farbe eingefärbt, siehe
`.cup-segment.partial .cup-outline{stroke:var(--seg-color)}`), statt bei
sehr kleinen, aber realen Werten komplett zu verschwinden.

Kein neuer Test (keine JS-Testinfrastruktur im Projekt, Verifikation wie
bei JS-Änderungen üblich per Live-Server-Check). Cache-Buster `v='48'`,
`pytest` (99 Tests, unverändert) grün, live verifiziert.

**Nachtrag 34 — Energie-Icon von 🔋-Emoji auf eigenes rotes Batterie-SVG
umgestellt `[ERLEDIGT]`**: Optisches Finding — das 🔋-Emoji ist plattform-
abhängig eingefärbt (meist grün), während Ring (`.ring-fill.energy{stroke:var(--red)}`)
und Tassen (`.cup-segments.energy{--seg-color:var(--red)}`) für Energie
bereits durchgängig Rot verwenden. Emoji-Farben lassen sich nicht per CSS
überschreiben, daher ein eigenes kleines SVG statt des Emojis.

**Umsetzung**: Statisches Batterie-Icon (keine dynamische Füllstands-
Logik wie bei den Tassen-Segmenten, rein dekorativ) — Außenkontur rot
umrandet (Erkennbarkeit, Nutzerwunsch), Innenfläche zu 3/4 rot gefüllt,
restliches 1/4 schwarz. Als `<svg class="battery-icon">` in
`app/templates/dashboard.html` (obere Kachel) sowie als
JS-Konstante `BATTERY_ICON` in `app/static/js/dashboard.js`
(wiederverwendet für "Fußabdruck dieser Unterhaltung" und die
500er-Legende, ersetzt dort ebenfalls das 🔋-Emoji). Neue CSS-Klassen
`.battery-icon`/`.battery-outline`/`.battery-empty`/`.battery-fill` in
`style.css`.

Kein neuer Test (rein visuelle Änderung, keine JS-Testinfrastruktur im
Projekt). Cache-Buster `v='50'`, `pytest` (104 Tests, unverändert) grün,
live verifiziert (SVG und CSS an allen drei Stellen korrekt ausgeliefert).

## Bugfix: Wasser/ADPe "nicht verfügbar" für Anthropic-Katalogeinträge `[ERLEDIGT]`

**Symptom**: Die Kachel "Wasser / ADPe" zeigte im Dashboard nach `/api/analyze`
durchgehend "nicht verfügbar", obwohl EcoLogits aktiv war.

**Ursache**: Merge-Konflikt zwischen zwei unabhängig entstandenen Änderungen.
Die Anthropic-Integration hat die Katalogeinträge `cloud_small`/`cloud_large`
in `model_catalog.py` von generischen Platzhaltern auf die echten Claude-Modelle
umgestellt (`model_id: "claude-haiku-4-5-20251001"` bzw. `"claude-sonnet-4-6"`,
`"ecologits_provider": "anthropic"`) — korrekt, weil jetzt bestätigt ist, welcher
Anbieter dahintersteckt. `ecologits_service._compute_via_provider_lookup()` ging
aber davon aus, dass der Modellname immer von einem echten
`ProviderConfiguration`-Objekt kommt (`provider.model_name`); der Vorab-
Schätzpfad (`/api/analyze`) hat zu diesem Zeitpunkt aber nur einen
Katalogeintrag, noch keinen echten Provider (`provider=None`). Die Funktion las
`None.model_name` faktisch als `None`, brach mit `(None, None)` ab — **ganz
ohne Warnung** — und der Aufrufer fiel auf die alte, einfache Formel zurück,
die kein `water_ml`/`adpe_ug_sb_eq` liefert.

**Fix**: `_compute_via_provider_lookup()` liest den Modellnamen jetzt aus
`provider.model_name`, falls ein echter Provider vorhanden ist, sonst aus
`catalog_model.get("model_id")`. Live verifiziert: die Katalogeinträge liefern
jetzt echte, datenbankgestützte Werte (`mode: llm_impacts`) statt der groben
Formel — eine echte Genauigkeitsverbesserung für den Vorab-Schätzpfad, nicht
nur ein Bugfix. Regressionstest:
`test_provider_lookup_path_used_for_catalog_model_via_model_id` in
`tests/test_ecologits_service.py`.

---

## Finding: Kacheln zeigen veraltete Werte nach Prompt-Optimierung `[Fix #1 + Option #2 ERLEDIGT]`

**Symptom** (aus dem ersten Live-Test mit einem Modell in der EcoLogits-DB):
Die Kacheln (CO₂e/Energie/Wasser/Kosten) zeigen nach `/api/analyze` die Werte
für den **Originalprompt**. Übernimmt der Nutzer den optimierten Prompt (Button
"Optimierten Prompt verwenden") und sendet ihn, ist der tatsächliche Prompt
länger (mehr Token) — die tatsächlich beim Versand berechneten Werte liegen
dann höher als das, was die Kacheln vorher versprochen haben.

**Ursache**: Der Klick auf "Optimierten Prompt verwenden" kopiert den Text nur
ins Feld (`prompt.value = ...`) und zeigt einen Toast, löst aber **keine** neue
Analyse aus — die Kacheln bleiben auf dem Stand der letzten `analyze()`
eingefroren. Breiter betrachtet gilt das für **jede** manuelle Änderung am
Prompt-Feld nach der Analyse: `syncSend()` prüft nur, ob überhaupt schon einmal
analysiert wurde (`last` gesetzt), nicht ob der aktuelle Textinhalt noch zur
Analyse passt, die die Kacheln zeigen.

**Zwei sich ergänzende Lösungsbausteine (Diskussion mit Claude, noch nicht
umgesetzt):**
1. **Auto-Re-Analyse beim Übernehmen-Klick** — "Optimierten Prompt verwenden"
   löst direkt `analyze()` auf dem neuen Text aus statt nur `updateCounter()`.
   Kacheln stimmen dann sofort wieder mit dem zu sendenden Text überein.
   Kosten: ein zusätzlicher Ollama-Analyse-Call an dieser Stelle, aber
   wiederverwendet nur bestehende Logik, kein neuer Endpunkt nötig.
2. **"Veraltet"-Guard als generelles Netz** — beim Abschluss von `analyze()`
   den analysierten Text merken (`lastAnalyzedPrompt`). Weicht `prompt.value`
   später davon ab (Tippen, Optimieren-Klick ohne #1, o. ä.), Kacheln/
   Send-Zusammenfassung mit Hinweis "Werte veraltet – bitte erneut
   analysieren" markieren und Send blockieren, bis neu analysiert wurde. Deckt
   auch Fälle ab, die #1 allein nicht abfängt (manuelles Nachbearbeiten des
   Prompt-Felds).

Empfehlung aus der Diskussion: beides — #1 als eigentlicher Fix für den
beschriebenen Fall, #2 als generelle Absicherung. Tradeoff bei #1: zusätzliche
Ollama-Latenz beim Klick, bei großen lokalen Modellen spürbar (siehe
Timeout-Erfahrungen weiter oben in diesem Projekt).

**Fix #1 umgesetzt**: Der Klick-Handler für "Optimierten Prompt verwenden" in
`app/static/js/dashboard.js` übernimmt den Text weiterhin ins Prompt-Feld,
löst jetzt aber direkt `analyze()` aus, statt nur `updateCounter()` zu rufen.
Die Kacheln (CO₂e/Energie/Wasser/Kosten) sowie Empfehlung und
Provider-Vorauswahl spiegeln damit unmittelbar den tatsächlich im Feld
stehenden (optimierten) Text — keine separate Bestätigung mehr nötig. Toast
weist kurz auf die Neuberechnung hin ("Werte werden neu berechnet …"), der
bestehende Analyse-Status übernimmt den Rest der Rückmeldung
(`setAnalyzing()`/"Analyse abgeschlossen."). Cache-Buster auf `v='14'`
erhöht, `pytest` (73 Tests) bleibt grün, Live-Verifikation gegen den
Dev-Server bestätigt die Auslieferung.

**Fix #2 (genereller "Veraltet"-Guard bei jeder manuellen Abweichung vom
analysierten Text) bleibt offen** — deckt Fälle ab, die #1 nicht erfasst
(z. B. Nachbearbeiten des Prompt-Felds nach der Analyse ohne den
Übernehmen-Button).

**Nachtrag aus dem Live-Test von Fix #1**: Beim tatsächlichen Test ("Was ist
Entropie?") zeigte die Auto-Re-Analyse zunächst *trotzdem* keine sichtbare
Änderung der Kacheln — Root Cause war eine zweite, tieferliegende Ursache:
`analysis_payload()` verwendete für `expected_output_tokens` eine **feste
Konstante** (`DEFAULT_EXPECTED_OUTPUT_TOKENS`), unabhängig von der
Prompt-Länge. Da EcoLogits' Berechnung nur von der Ausgabe-Tokenzahl abhängt
(nicht vom Eingabetext), lieferten Original- und optimierter Prompt bei
gleicher Modellklasse rechnerisch identische CO₂/Energie/Wasser-Werte — Fix #1
löste zwar korrekt eine neue Analyse aus, aber die Analyse selbst konnte gar
nicht anders als dieselbe Zahl zurückgeben. Das ist exakt das schon weiter oben
unter "Das technische Kernproblem" beschriebene Problem, nur schon in
`/api/analyze` aufgetreten statt erst im geplanten Live-Endpunkt. Behoben durch
Vorziehen der dort skizzierten `RATIO`-Heuristik direkt in `analysis_payload()`
— siehe Abschnitt "Das technische Kernproblem" oben für Details zur Umsetzung.

**"Option #2" — `[ERLEDIGT]`, nicht zu verwechseln mit "Fix #2" (Veraltet-Guard)
oben**: Der Klick auf "Optimierten Prompt verwenden" löst jetzt **keine volle
`analyze()` mehr aus**, sondern einen schlanken Recompute ohne Ollama-Aufruf.
Begründung aus der Diskussion: eine erneute Ollama-Optimierung des bereits
optimierten Prompts bringt praktisch nie eine günstigere Modelländerung,
kostet aber die volle Ollama-Latenz — und öffnet potenziell eine
**Endlosschleife** (jeder Klick könnte einen neuen `optimized_prompt`-
Vorschlag erzeugen, der wieder einen neuen Übernehmen-Klick nahelegt, ohne
natürlichen Endpunkt). Ein Recompute ohne Ollama-Aufruf hat keinen neuen
Optimierungsvorschlag zur Folge und bricht diese Schleife strukturell.

**Umsetzung**: neuer, schlanker Endpunkt `POST /api/estimate-footprint`
(`app/routes/api.py`, `estimate_footprint_payload()`) — nimmt `{"text":...,
"model_class":..., "complexity_score":...}` entgegen, sucht `model_class` per
reiner Dict-Suche im bestehenden `MODELS`-Katalog (kein Ollama-Aufruf, keine
neue Compliance-Prüfung, keine DB-Schreibung), und berechnet Token/Kosten/
Dauer/Sustainability neu — exakt dieselben Helper-Funktionen wie
`analysis_payload()` (`estimate_tokens`, `estimate_duration`,
`sustainability_for`, `estimate_cost`), nur ohne Neuklassifikation. Frontend
(`app/static/js/dashboard.js`, neue Funktion `refreshFootprint()`): sendet
den aktuellen Textfeld-Inhalt zusammen mit der **zuletzt empfohlenen**
Modellklasse (`last.recommendation.model_class`) und dem zuletzt bekannten
`complexity_score` (`last.analysis.complexity_score`, aus der letzten echten
Analyse, nicht neu von Ollama ermittelt); aktualisiert damit CO₂e-/Energie-/
Wasser-Kacheln, Kosten, Dauer und die "Bewusst senden"-Zusammenfassung, lässt
Empfehlung/Compliance/Optimierungsvorschlag aber unverändert. Cache-Buster auf
`v='15'` erhöht. Neue Tests: `test_estimate_footprint_scales_with_text_length`,
`test_estimate_footprint_rejects_unknown_model_class`,
`test_estimate_footprint_requires_no_ollama_call` (patcht `analyze_with_ollama`
und prüft `assert_not_called()`) in `tests/test_routes.py`. `pytest`: 77/77
grün. Live verifiziert: kurzer Text → 24 Ausgabe-Token/0,0008 g CO₂e, langer
Text → 180 Token/0,0061 g CO₂e, unbekannte `model_class` → HTTP 400.

Deckt sich inhaltlich mit dem ohnehin geplanten `/api/estimate-footprint`
weiter oben — dessen Grundidee (reine Katalog-Suche statt Ollama-Aufruf) wurde
hier für den konkreten Klick-Fall vorgezogen. Die dortigen offenen
Grundsatzentscheidungen (serverseitig vs. clientseitig, "live" beim Tippen)
betreffen weiterhin nur das größere, noch nicht gebaute Live-Tipp-Feature für
`#prompt`/`#chat-input` — bleiben unverändert offen.

### Folgefund nach Live-Test von Option #2: Originalprompt wird beim Übernehmen überschrieben `[TODO]`

**Symptom** (aus dem Test von Option #2, kein Fehler, aber UX-Störgefühl):
Klick auf "Optimierten Prompt verwenden" kopiert den Text weiterhin nach
`#prompt` — der vom Nutzer selbst eingegebene Originaltext ist damit
kommentarlos verschwunden, ohne visuellen Hinweis warum. Der Button tut nicht
ganz das, was er sagt: "verwenden" klingt nach *zusätzlich nutzen*, faktisch
*ersetzt* er den Originaltext im Feld, das eigentlich "Prompt" (nicht
"optimierter Prompt") heißt.

**Ursache, strukturell**: `send()` liest beim Versand ausschließlich
`prompt.value` — es gibt aktuell keinen eigenständigen Begriff von "das, was
tatsächlich gesendet wird" getrennt von "das, was im `#prompt`-Feld steht".
Der Kopiervorgang ist deshalb keine kosmetische Entscheidung, sondern
funktional notwendig, solange dieses eine Feld beides sein muss.

**Sofort geprüfte Kleinlösung (nicht gewählt)**: nur eine visuelle
Rückmeldung beim Überschreiben (Aufblitzen/Toast) hinzufügen — behebt das
Symptom, aber nicht die eigentliche Ursache, und der Originaltext bliebe
weiterhin unwiederbringlich weg.

**Bevorzugte, größere Lösung (Entscheidung des Nutzers: das machen wir)**:
`#optimized` wird zur eigentlichen Sende-Quelle, statt seinen Inhalt nach
`#prompt` zu kopieren. `#prompt` bleibt unangetastet stehen — der Nutzer sieht
weiterhin seinen Originaltext, und der Button tut exakt das, was draufsteht.

**Grober Umsetzungsgedanke** (noch nicht im Detail entschieden):
- Ein aktiver "Sende-Text"-Zustand in `dashboard.js`, der nach `analyze()`
  zunächst `#prompt` entspricht, aber beim Klick auf "Optimierten Prompt
  verwenden" auf `#optimized` umschaltet — ohne `#prompt` zu verändern.
- `send()` sendet diesen Zustand statt direkt `prompt.value`.
- `refreshFootprint()` (Option #2) liest dann direkt aus `#optimized`, statt
  wie heute erst den Umweg über einen Kopiervorgang nach `#prompt` zu gehen.
- Reset-Verhalten nach dem Senden (`#discard`-Checkbox, aktuell werden
  `#prompt`/`#optimized` geleert) muss den Sende-Zustand mit zurücksetzen.
- Mögliche zusätzliche Klarheit: Button-Beschriftung/Feld-Label prüfen, ob sie
  nach der Umstellung noch treffend sind (z. B. macht ein Editieren von
  `#prompt` nach diesem Klick weiterhin Sinn, sollte dann aber den
  Sende-Zustand wieder auf `#prompt` zurückschalten).

---

## Finding: Kacheln passten sich nicht an eine manuelle Provider-/Modellwahl an `[ERLEDIGT]`

**Frage vor dem nächsten Live-Test**: Passen sich die EcoLogits-Kacheln an,
wenn der Nutzer im "Bewusst senden"-Bereich manuell einen anderen Provider
oder ein anderes Modell wählt als das von der Analyse empfohlene? Antwort:
**nein, bisher nicht** — war keine bewusste Entscheidung, sondern eine
unbemerkte Lücke.

**Ursache**: `selectedProviderEstimate()` (`app/static/js/dashboard.js`),
ausgelöst bei jedem `change`-Event auf `#provider`/`#send-model`,
aktualisierte bisher **ausschließlich** die Kosten-Kachel (`#cost`) anhand des
tatsächlich gewählten Providers — inklusive Warnhinweis bei teurerer manueller
Wahl (Haiku→Sonnet). Die CO₂e-/Energie-/Wasser-Kacheln blieben dabei
unangetastet und zeigten weiterhin die Werte der ursprünglich **empfohlenen**
Modellklasse aus `/api/analyze` — unabhängig davon, was der Nutzer danach im
Dropdown wählte. Der tatsächliche Versand (`/api/send`) rechnete schon immer
korrekt mit dem wirklich verwendeten Provider; betroffen war nur die Vorschau
vor dem Senden.

**Fix**: `selectedProviderEstimate()` ruft jetzt bei jeder Provider-/
Modelländerung `refreshTilesForSelectedProvider()` auf — nutzt denselben
`/api/estimate-footprint`-`provider_id`-Pfad wie schon `estimateChatFootprint()`
für Folgeprompts, ersetzt damit auch die bisherige lokal in JS dupliziert
berechnete Kostenformel (jetzt einzige Quelle: der Server, konsistent mit dem
tatsächlichen Sendepfad). Aktualisiert `#cost`, alle drei Kacheln via
`renderSustainabilityTiles()` und die "Bewusst senden"-Zusammenfassungszeile
(`#send-summary`), damit deren Kosten-/CO₂e-Angabe nicht denselben
Alt-Zustand-Fehler wiederholt. Schlägt der Aufruf fehl (z. B. Provider noch
nicht vollständig konfiguriert), bleiben die zuletzt bekannten Werte
kommentarlos stehen, statt bei jedem Dropdown-Wechsel eine Fehlermeldung zu
zeigen.

**Nebenbei behoben**: `renderSustainabilityTiles()` ging bisher davon aus,
dass `sustainability` nie `null` ist (stimmte für `/api/analyze`, das immer
mindestens die alte Formel liefert) — für den Provider-Pfad kann es das aber
sein (kein Formel-Fallback für echte Provider, dieselbe Ehrlichkeits-Regel wie
bei `/api/send`). Ohne den Null-Check hätte ein Provider ohne EcoLogits-
Konfiguration die Seite zum Absturz gebracht statt "–"/"Nicht verfügbar"
anzuzeigen.

Cache-Buster auf `v='20'` erhöht. `pytest` (79 Tests) bleibt grün — reine
Frontend-/JS-Änderung, Backend unverändert (nutzt den bereits getesteten
`/api/estimate-footprint`-`provider_id`-Pfad). Live verifiziert, dass die
neue Funktion vom Server ausgeliefert wird; ein echter Provider-Wechsel im
Browser ist mangels JS-Testinfrastruktur nicht automatisiert testbar und
sollte manuell verifiziert werden.

---

## Nebenfund beim Indikator-Test: irreführende Fehlermeldung bei ungültigem Modellnamen `[TODO]`

**Nicht direkt EcoLogits-Thema, aber beim Testen von Designvorschlag B
(Indikator "Nicht verfügbar") aufgefallen** — hier trotzdem festgehalten, damit
er nicht verloren geht.

**Symptom**: Um die "Nicht verfügbar"-Anzeige zu testen, wurde ein
Anthropic-Provider mit einem in der EcoLogits-DB unbekannten (und bei Anthropic
tatsächlich nicht existierenden) Modellnamen angelegt. Die Konfiguration selbst
speichert erfolgreich; beim tatsächlichen Versand erscheint aber "Provider ist
nicht erreichbar" — obwohl die Anfrage die echte Anthropic-API durchaus
erreicht.

**Ursache**: `AnthropicProvider._request()`
(`app/providers/anthropic.py:31-42`) behandelt nur 401/403, 429 und ≥500
gesondert. Ein ungültiger Modellname liefert von Anthropic ein reguläres
**HTTP 400**, das durchfällt bis `response.raise_for_status()`. Das dabei
geworfene `requests.exceptions.HTTPError` ist eine Unterklasse von
`requests.RequestException` und landet deshalb im generischen
`except`-Zweig, der zu "Anthropic ist nicht erreichbar." verfälscht wird. Die
Anfrage kam tatsächlich an und wurde beantwortet — nur die Fehlermeldung ist
falsch. Derselbe Musterfehler steckt in `app/providers/openai_compatible.py`
(analoger `_request()`-Aufbau, `"Provider ist nicht erreichbar."`).

**Auswirkung über den Testfall hinaus**: Das betrifft nicht nur den
EcoLogits-Indikator-Test — jeder echte Anthropic-Provider mit einem
Tippfehler oder veralteten Modellnamen zeigt Nutzern denselben irreführenden
"nicht erreichbar"-Text statt eines Hinweises auf das eigentliche Problem
(ungültiges Modell/fehlerhafte Anfrage).

**Möglicher Fix** (noch nicht umgesetzt): in beiden `_request()`-Methoden
einen zusätzlichen Zweig für 400 (bzw. generisch für unbehandelte 4xx) mit
eigenem, treffenderem Text ergänzen, z. B. "Anthropic/Provider hat die Anfrage
abgelehnt — ungültiges Modell oder fehlerhafte Anfrage."

---

## Offene Entscheidungen (Zusammenfassung)

> **Phasenwechsel**: Die EcoLogits-Kernarbeit (Berechnung, Fallback-Stufen,
> Indikator-Funktionalität, Versand-Schätzung) gilt als inhaltlich
> abgeschlossen, ebenso die bildhafte Darstellung. Von ursprünglich vier
> zurückgestellten, nicht rein optischen Punkten ist die `RATIO`-Kalibrierung
> inzwischen erledigt (Nachtrag 32); drei verbleibende — allesamt nicht
> EcoLogits-spezifisch, sondern allgemeine Prompt-Flow-/Fehlermeldungs-Themen
> — bleiben bewusst zurückgestellt (mit ⏸ markiert). Die zurückgestellten
> Punkte sind nicht vergessen, nur nicht mehr aktuelle Priorität.

- [x] **Entscheidung: CodeCarbon verworfen** — auf dieser Zielhardware (Windows, AMD, keine GPU) keine echte Messung, sondern selbst nur ein TDP-Fallback-Schätzwert; ersetzt durch eine eigene, leichtgewichtige `psutil`-basierte Formel (siehe Nachtrag 24). Feld-Mapping und `requirements.txt`-Eintrag damit hinfällig — `psutil` statt `codecarbon` ergänzt.
- [ ] **Verworfen** — Frontend-Darstellung des Analyse-Fußabdrucks (lokaler Ollama-Voranalyse-Schritt): explizit als "Information Overload" ohne Sensibilisierungs-Mehrwert eingestuft, kein Teil der bewussten Sende-Entscheidung — nicht mehr geplant
- [x] **Entscheidung: serverseitig** (`/api/estimate-footprint`) statt clientseitig für die Versand-Schätzung — umgesetzt
- [x] **Entscheidung: kein Live-Tippen** — expliziter "Fußabdruck schätzen"-Button statt Live-Update/Debounce, um keine Genauigkeit vorzutäuschen, die die `RATIO`-Heuristik nicht hat — umgesetzt für `#chat-input`
- [x] `RATIO`-Heuristik (statt fixer `DEFAULT_EXPECTED_OUTPUT_TOKENS`-Konstante) vorgezogen direkt in `/api/analyze` umgesetzt (`EXPECTED_OUTPUT_RATIO`, Default `6`)
- [x] `RATIO`-Kalibrierung umgesetzt: `flask calibrate-ratio`-CLI-Kommando liest echte `UsageLog`-Daten (Median-Vorschlag, Mindeststichprobe 20) — Übernahme in `.env` bleibt manueller Schritt; siehe Nachtrag 32
- [x] Visuelles Feedback bei Wertänderung (Aufblitzen/Farbwechsel) — umgesetzt als Ring-/Tassen-Füllstandswechsel bei jeder neuen Analyse, nicht als separates Aufblitzen/Farbwechsel-Element wie ursprünglich skizziert
- [x] Alten Prompt-Vergleich entfernen (`optimized_payload()`, Widget, Tests) + `ECOLOGITS_INTEGRATION.md` §4/§6/§8 als überholt markiert
- [x] "Stromkosten"-Kachel entfernen (EcoLogits-Schätzung × Haushaltsstrompreis) — Ersatz später über CodeCarbon
- [x] Bugfix: Wasser/ADPe "nicht verfügbar" für Anthropic-Katalogeinträge (`_compute_via_provider_lookup()` liest jetzt auch `catalog_model["model_id"]`)
- [x] Energie-/CO2-Abdeckung für lokalen Ollama-Sende-/Inferenzaufruf ergänzt — nicht über CodeCarbon (verworfen), sondern eigene `psutil`-CPU-Auslastungsformel als Fallback, wenn EcoLogits kein Ergebnis liefert; siehe Nachtrag 24
- [x] **Entscheidung: keine Anzeige lokaler Analyse-Energie/CO2 am Dashboard** (weder als eigene "Stromkosten"-Kachel noch als dezente Zeile unter dem Prompt-Fenster) — geprüft und verworfen, siehe Nachtrag 31
- [x] Zweistufiger Fallback (Anbieter-Lookup → manuelle Parameter → Formel) entschieden und umgesetzt
- [x] Entscheidung: Indikator "Modell gefunden/Näherung/nicht verfügbar" — ja, erste unstylische Textfassung an allen EcoLogits-Kacheln + Folgeprompt-Zusammenfassung umgesetzt; finales Styling/Platzierung noch offen
- [x] Finales Styling des Indikators (Icon/Farbe statt reinem Text) — umgesetzt über Ring-Farbwechsel (Überlauf) und Tassen-Silhouetten statt einer separaten Icon-Vorschlag-(A)-Lösung
- [x] Erste Testfassung: Icons (⚖️/🔋/💧) an oberen Kacheln + Meter-Zeile in der Statusleiste umgesetzt; finale Metapher (Silhouetten statt Emoji) weiterhin offen
- [x] Basis-Label ("Basis: Originalprompt"/"Basis: Optimierter Prompt") an oberen Kacheln umgesetzt — bewusst kein Nebeneinander-Vergleich
- [x] Finale Metapher pro Metrik (CO₂/Energie/Wasser) ausgewählt — Emoji (🌿/🔋/💧) bleiben dauerhaft, kein Wechsel zu Silhouetten
- [x] Referenzgefäß-Kalibrierung entschieden — eine gemeinsame "Tasse Tee" (150 mL) für Pro-Chat- und 500er-Hochrechnungs-Ansicht statt separater Tropfen-/Glas-/Flasche-Abstufung
- [x] Gemeinsames Meter-Prinzip für die kumulierte Statusleiste umgesetzt (session-relative Füllbalken, einheitliches Prinzip über CO₂/Energie/Wasser) — Übertragung auf weitere Stellen/finale Optik noch offen
- [x] Finding: Kacheln nach "Optimierten Prompt verwenden" veraltet — Fix #1 (Auto-Re-Analyse beim Übernehmen-Klick) umgesetzt
- [ ] ⏸ **Zurückgestellt** — Finding: Kacheln nach "Optimierten Prompt verwenden" veraltet — Fix #2 ("Veraltet"-Guard bei jeder Abweichung von `lastAnalyzedPrompt`) umsetzen
- [x] "Option #2": `/api/estimate-footprint` gebaut und in "Optimierten Prompt verwenden" verdrahtet — kein Ollama-Aufruf mehr bei diesem Klick, Kacheln aktualisieren sich anhand der zuletzt empfohlenen Modellklasse
- [ ] ⏸ **Zurückgestellt** — Folgefund: "Optimierten Prompt verwenden" überschreibt `#prompt` kommentarlos — `#optimized` als eigentliche Sende-Quelle umbauen, `#prompt` bleibt für den Nutzer unangetastet stehen (saubere Lösung, vom Nutzer priorisiert)
- [ ] ⏸ **Zurückgestellt** — Nebenfund: irreführende "nicht erreichbar"-Meldung bei HTTP 400 in `anthropic.py`/`openai_compatible.py` — eigenen Fehlerzweig für 400/unbehandelte 4xx ergänzen
- [x] Finding: Kacheln passten sich nicht an manuelle Provider-/Modellwahl an — `selectedProviderEstimate()` nutzt jetzt `/api/estimate-footprint` (`provider_id`-Pfad) statt nur die Kosten lokal neu zu berechnen
- [x] Bugfix: Meter-Balken unsichtbar — Root Cause CSP (`style-src 'self'`) blockierte inline `style="..."`-Attribute; alle betroffenen Stellen auf benannte CSS-Klassen umgestellt
- [x] EcoLogits-Kacheln (CO₂e/Energie/Wasser) in eigenes `.panel` mit Fußzeilen-Basis-Label ausgegliedert, getrennt von Kosten/Dauer/Compliance
- [x] Wasser/ADPe in zwei eigenständige Kacheln aufgetrennt (waren vorher fälschlich in einer Kachel kombiniert dargestellt)
- [x] Bugfix: `water_liters` rundete bei kurzen Prompts auf 0 — auf `water_ml` umgestellt (analog zum historischen ADPe-µg-Fix)
- [x] Energie-/Wasser-/CO₂-Referenzgröße in der Statusleiste umgesetzt — vereinheitlicht auf eine gemeinsame "Tasse Tee kochen"-Referenz (250 mL/25 Wh/8,75 g CO₂) statt drei unabhängiger Einzel-Referenzen, Bruch-Anzeige statt Prozent
- [x] Zusätzliche Aktivitätsring-Darstellung (Apple-Watch-inspiriert, eigene Umsetzung) in der Statusleiste ergänzt, dieselbe Tasse-Tee-Referenz wie die Balken
- [x] Tasse-Tee-Referenzgröße von 250 mL auf 150 mL verkleinert (linear skaliert: 15 Wh, 5,25 g CO₂)
- [x] Zusätzliche Sensibilisierungs-Hochrechnung "500 KI-Anfragen" mit eigenem Ring-Satz ergänzt (Testfassung, `REQUEST_MULTIPLIER = 500`)
- [x] CO₂-Icon von ⚖️ auf 🌿 umgestellt (durchgängig)
- [x] Überlauf-Darstellung bei ≥1× Tasse Tee: Ring-Farbwechsel (statt kaum sichtbarem Glow) + echte Tassen-Silhouette (statt Balken, größer) in der 500er-Hochrechnung umgesetzt
- [x] Ring in der 500er-Hochrechnung entfernt (Ring in "Kosten und Nutzung" bleibt vorerst bestehen) — "große nummerierte Tasse pro voller Zehnerreihe" ersetzt den bisherigen "+X,Y"-Text als primäre Darstellung, "+X,Y" bleibt Fallback ab > 5 großen Tassen
- [x] **Entscheidung: ADPe bleibt bewusst außen vor** in der kumulierten Statusleiste (Chat-Gesamtmetrik und 500er-Hochrechnung) — kein fehlendes Feature, sondern finaler Beschluss. Begründung siehe Nachtrag 30.
- [x] Energie-Anzeige von kWh auf Wh umgestellt (`energy_kwh` → `energy_wh`, betrifft EcoLogits- und Formel-Fallback-Pfad)
