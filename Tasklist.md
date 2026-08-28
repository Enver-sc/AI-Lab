Berechnungsgrundlagen – Recherchen
- CO₂ (macht Mario)
- Token / Kosten (macht Enver)
- LLM‑Auswahl (macht Enver)
- Compliance Stufe 1/2 (macht Keng)
- Routing Engine (macht Mario, aber wahrschl. Überlappung zu LLM Auswahl)

Allgemeiner Task für alle
- App analyiseren und Verbesserungsvorschläge

Implementierung Berechnungsgrundlagen
- Beispiel: Steering Files
- Alternativen (macht Mario in Vorbereitung zur Implementierung)
- Auswahl des lokalen LLMs ( Tests)
----

8‑Wochen‑Taskliste**, so dass ihr **spätestens am 12.09.2026** (Tag der Präsentation/Demo) eine stabile Live‑Demo für Euer Projekt *Sustainable AI Gateway*, inklusive einer **vollen Woche Puffer für den Dry‑Run**.  

---

## 🗂️ **Taskliste für 10‑Wochen‑Projektplan (inkl. 1 Woche Dry‑Run)**

---

### **Woche 1 – Projektsetup & Architektur**
- Projektkickoff, Rollen & Verantwortlichkeiten klären  
- Grobarchitektur definieren (Frontend, lokales Analysemodell, LLM‑Routing, Compliance‑Module)  ⚠️ 11.7. definieren und malen :) / Tasks zuweisen ⚠️
- Task Review Weeks - Prio festlegen 
- Git‑Repository einrichten (Code, Docs, Issues, Branching‑Strategie) ✅ Task erledigt
- Online‑Arbeitsumgebung festlegen (Kanban, Kommunikationskanäle, CI/CD‑Pipeline)
  -- WhatsApp - ✅ Task erledigt
  -- GitHub - ✅ Task erledigt
  -- lokale Demoumgebung für jeden - ✅ Task erledigt
  -- Terminabstimmung über Whatsgruppe - ✅ Task erledigt 
  -- CI/CD out of scope - optional Unit Test für Code je nach Projektfortschritt ⚠️
- Cloud Lösung mit GPU bzw Angebot David f. HP Server m. OLLAMA drauf
- Hardware für Demo-Laptop auswählen und vorbereiten - macht jeder auf seiner lokalen Umgebung daheim - ✅ Task erledigt
- SW Umgebung für Projekt lokal aufsetzen
-   Tools festlegen
-     Visual Studio Code
-     GitHub Desktop / Git Bash
-   lokales LLM für OLLAMA auswählen - wird gemacht nach Modellwahl siehe Woche 2
-   Docker Umgebung optional bauen mit Projekt nach Fortschritt ⚠️

---

Hier ist deine **angepasste 8‑Wochen‑Taskliste**, so dass ihr **spätestens am 12.09.2026** eine stabile Live‑Demo zeigen könnt.  
Ich habe die Inhalte verdichtet, Prioritäten neu gesetzt und trotzdem eine **volle Woche für den Dry‑Run** eingeplant.

---

### **Woche 2 – Basisinfrastruktur & Analysemodell (V1)**
- Frontend‑Skeleton erstellen  
- Backend‑API‑Skeleton erstellen  
- Lokales Analysemodell auswählen & integrieren (z. B. kleiner Transformer)  
- Token‑Schätzung + CO₂‑Berechnung (Basisformeln)  
- Erste Trainingsdaten für Prompt‑Analyse sammeln

---

### **Woche 3 – Compliance‑Modul & Modellrouting**
- Compliance‑Regelwerk definieren (Datenschutz, sensible Inhalte, Policies)  
- Compliance‑Klassifikator implementieren (Regel‑basiert + ML‑Heuristik)  
- LLM‑Routing‑Logik implementieren (Modellwahl nach Analyse)  
- Kosten‑Schätzung integrieren (Tokenpreis × Tokenanzahl)  
- Dauer‑Schätzung integrieren

---

### **Woche 4 – Frontend‑Integration**
- Dashboard‑UI für:
  - CO₂‑Fußabdruck  
  - Kosten & Dauer  
  - Compliance‑Score  
  - Modellvorschlag  
  - Optimierungsvorschläge  
- API‑Integration Frontend ↔ Backend ↔ Analysemodell  
- Erste End‑to‑End‑Tests

---

### **Woche 5 – Optimierungsvorschlags‑Engine**
- Regeln & ML‑Heuristiken für:
  - Token‑Reduktion  
  - Modellwahl‑Optimierung  
  - Compliance‑Verbesserung  
- Ausgabeformat definieren (kurz, klar, actionable)  
- Integration ins Dashboard  
- Logging & Feedback‑Loop für Selbstoptimierung

---

### **Woche 6 – Stabilisierung & Performance**
- End‑to‑End‑Tests  
- Performance‑Optimierung auf Demo‑Laptop  
- Fehlerbehandlung, Logging, Telemetrie  
- Dokumentation im Git‑Repo erweitern (Setup, Architektur, API)

---

### **Woche 7 – Demo‑Build & Feinschliff**
- Demo‑Version auf Demo‑Laptop deployen  
- UI‑Polishing  
- Demo‑Storyline erstellen (Beispielprompts, Szenarien)  
- Backup‑Strategie & Fallback‑Modelle vorbereiten  
- Finalisierung der Projektdokumentation

---

### **Woche 8 – Dry‑Run‑Woche (Puffer)**
- Vollständiger Probelauf der Live‑Demo  
- Troubleshooting & letzte Optimierungen  
- Team‑Abnahme  
- Finaler Check der Demo‑Umgebung

---

## 🎯 Ergebnis
Ihr habt am 12.09.2026 eine **stabile, lokal lauffähige Demo**, die CO₂‑Fußabdruck, Kosten, Dauer, Compliance und Optimierungsvorschläge für Prompts liefert.

Wenn du willst, kann ich dir die Taskliste auch als **GitHub‑README‑Taskliste mit Checkboxen** formatieren.

---

## 📋 Backlog / Ideen (nicht priorisiert, nicht terminiert)

### Dashboard: bildhafte Visualisierung der EcoLogits-Werte (Icons/Äquivalente)
Idee: die reinen Zahlen (CO₂e, Energie, Wasser/ADPe, Stromkosten) zusätzlich mit
kleinen, klar verständlichen Bildern/Symbolen unterlegen (z. B. Baum, Wasserglas),
um die Botschaft emotional greifbarer zu machen.

**Wichtiger Kalibrierungs-Befund, bevor das umgesetzt wird**: Pro-Prompt-Werte sind
für wörtliche "Bäume/Wassergläser"-Äquivalente viel zu klein. Beispiel: ein Prompt
erzeugte 0,0168 g CO₂e; ein Baum bindet ca. 21 kg CO₂/Jahr — das wären ca.
1,25 Mio. Prompts pro Baum. "🌳 0,0000008 Bäume" wäre verwirrender als die reine
Zahl, nicht klarer.

Drei mögliche Bausteine (in der Diskussion mit Claude entstanden, noch nicht
umgesetzt):
- **(A) Icons als reine Kennzeichnung** an den bestehenden Stat-Kacheln (Baum für
  CO₂e, Tropfen für Wasser, Glühbirne/Batterie für Energie, Münze für
  Stromkosten) — keine wörtliche Mengenangabe, nur visuelle Zuordnung. Klein,
  risikoarm, kein Backend-Bedarf.
- **(B) Auf die tatsächliche (winzige) Größenordnung kalibrierte Alltags-Äquivalente**
  pro Prompt, z. B. "≈ 0,4 Sekunden LED-Lampe" statt Bäume — Referenzwerte müssten
  recherchiert und als grobe Richtwerte gekennzeichnet werden (wie die bestehenden
  Schätzwerte im Projekt).
- **(C) Neue kumulative Ansicht im Dashboard**, gespeist aus dem bereits
  vorhandenen, aber im Frontend aktuell ungenutzten `/api/usage/summary`-Endpunkt
  (summiert CO₂/Kosten über alle tatsächlich versendeten Prompts, sofern
  `ENABLE_PROMPT_LOGGING=true`). Erst auf dieser aufsummierten Ebene ergeben
  Baum-/Autofahrt-Äquivalente wieder sinnvolle Größenordnungen. Größerer Aufwand
  (neue UI-Sektion), aber langfristig der Ort, an dem die Idee tatsächlich trägt.

Empfehlung aus der Diskussion: (A) + (B) zuerst (klein, schnell), (C) als
separates, größeres Stück Arbeit danach.

### Bug `[ERLEDIGT]`: Ollama-Antworten beim echten Versand auf Englisch und in JSON-Struktur statt normalem Fließtext

**Symptom**: Prompt "Was ist Entropie?" über einen lokalen Ollama-Provider gesendet
→ Antwort auf Englisch, verschachtelt als JSON-artige Struktur
(`"Concept of Entropy" → "Information Theory" → "Definition": "..."`), nicht als
normaler deutscher Fließtext.

**Wahrscheinliche Ursache, bereits am Code nachvollzogen**: `OllamaService.generate()`
(`app/services/ollama_service.py`, Zeile 17) setzt `"format":"json"` **fest und
unbedingt** für jeden Aufruf:

```python
response = self.http.post(f"{self.base_url}/api/generate", json={"model":self.model,"prompt":prompt,"system":system,"stream":False,"format":"json"}, timeout=self.timeout)
```

Diese Methode wird von **zwei** unterschiedlichen Aufrufern geteilt:
- `analysis_service.analyze_with_ollama()` — interne Prompt-Analyse, wo JSON-Ausgabe
  tatsächlich gewollt ist (der `SYSTEM_PROMPT` verlangt explizit ein JSON-Objekt
  mit festen Schlüsseln).
- `app/providers/ollama.py`, `OllamaProvider.generate()` — der **echte
  Sendevorgang** an einen vom Nutzer konfigurierten Ollama-Provider, wo eine
  normale Konversationsantwort erwartet wird, kein JSON.

Da `format: json` unbedingt gesetzt ist, wird auch der echte Sendevorgang in den
strukturierten JSON-Modus gezwungen — das erklärt plausibel sowohl die
verschachtelte Struktur als auch die Sprachumschaltung auf Englisch (Modelle
tendieren im JSON-Modus oft zu englischen Schlüsselbezeichnungen, unabhängig von
der Prompt-Sprache).

**Root-Cause-Analyse noch nicht abschließend verifiziert** (z. B. nicht getestet,
ob `format: json` weglassen bei echten Sendevorgängen das Problem tatsächlich
behebt) — nur der Code-Fund dokumentiert. Naheliegender Lösungsansatz für später:
`generate()` um einen Parameter erweitern (z. B. `format=None`), sodass
`OllamaProvider.generate()` ohne erzwungenes JSON aufruft, während
`analyze_with_ollama()` weiterhin `format="json"` explizit anfordert.

**Priorität**: niedrig, aktuell nicht zu bearbeiten — nur zur späteren Aufarbeitung
festgehalten.

**Update — behoben**: Root-Cause bestätigt (derselbe Effekt trat erneut auf, diesmal
als leere `{}`-Antwort bei "Was ist ein Gnu?"). Fix wie hier skizziert umgesetzt:
`generate()` bekam einen `json_mode`-Parameter (Default `False`), `"format":"json"`
wird nur noch gesetzt, wenn explizit angefordert. `analyze_with_ollama()` ruft jetzt
`service.generate(redacted, SYSTEM_PROMPT, json_mode=True)`; `OllamaProvider.generate()`
(echter Sendevorgang) bleibt unverändert und läuft damit automatisch ohne erzwungenes
JSON. Siehe `docs/CARBON_FOOTPRINT_REDESIGN.md`, Nachtrag 27.

**Verwandter Folgefund `[ERLEDIGT]`**: Nutzer meldete danach JSON-Antworten von einem
**externen** Provider (Anthropic/OpenAI-kompatibel) — zunächst vermutet, mit dem
`json_mode`-Fix zusammenzuhängen. War es nicht: `send()` schickt Prompts an externe
Provider unverändert weiter, ohne jede eigene Formatierungsvorgabe. Die externe Modell-
Antwort zitierte selbst die Anweisung ("Du hattest gefordert: ...JSON..."), die kam
also aus dem Prompt-Text. Ursache: Der `SYSTEM_PROMPT` der lokalen Analyse
(`analysis_service.py`) verlangt vom Analyse-Modell selbst eine JSON-Antwort — das
Modell übernahm diese Anweisung teils versehentlich in den von ihm vorgeschlagenen
`optimized_prompt`. Klickte der Nutzer "Optimierten Prompt verwenden" und sendete das
an einen externen Provider, wies der Prompt diesen unabsichtlich zu einer JSON-Antwort
an. Fix: `SYSTEM_PROMPT` um eine explizite Klarstellung ergänzt — `optimized_prompt`
ist ein Prompt für ein beliebiges Zielmodell, keine Kopie der eigenen Antwortformat-
Anweisung, und darf selbst keine Formatierungsvorgabe wie "antworte als JSON"
enthalten, außer der Originalprompt verlangt das ausdrücklich. Test:
`tests/test_analysis.py::test_system_prompt_forbids_leaking_own_format_instruction_into_optimized_prompt`
(prüft nur, dass die Anweisung im Prompt-String steht — ob das jeweilige Analyse-Modell
sich daran hält, lässt sich nicht deterministisch testen). `pytest`: 100/100 grün.

### Bug `[ERLEDIGT]`: `/api/analyze` zeigte "Nicht verfügbar" trotz vorhandenem Formel-Schätzwert

**Symptom** (gefunden beim Bauen des Fußabdruck-Detailkapitels in `Architektur.md`
§2.4): Liefert EcoLogits für `/api/analyze` keinen Wert (z. B. `ECOLOGITS_ENABLED=false`
oder unbekanntes Modell ohne manuelle Parameter), zeigte die Kachel trotzdem einen
echten Zahlenwert aus der alten linearen Formel (`sustainability_service.py`) — der
Indikator daneben aber fälschlich "Nicht verfügbar" statt "Grobe Schätzung". Zahl und
Indikator widersprachen sich sichtbar.

**Ursache**: `sustainability_for()` (`app/routes/api.py`, genutzt von `/api/analyze`)
setzte anders als die strukturell gleiche `estimate_footprint_for_provider()` (genutzt
von `/api/estimate-footprint`) kein `mode: "formula"`, wenn `compute_impacts()` `None`
liefert. `ecoIndicatorLabel()` im Dashboard (`dashboard.js`) fällt bei fehlendem `mode`
auf den Default "Nicht verfügbar" zurück, unabhängig davon, ob ein Zahlenwert da ist.

**Fix**: `sustainability_for()` bekam dieselbe `if eco_result is None: sustainability["mode"]
= "formula"`-Ergänzung wie ihr Pendant. Test `test_analyze_falls_back_when_ecologits_disabled`
(`tests/test_routes.py`) um die Regressionsprüfung `sustainability["mode"] == "formula"`
erweitert. `pytest`: 126/126 grün.

**Manueller Retest ausstehend** (noch nicht im Browser verifiziert, bitte vor der
Präsentation einmal nachziehen):
- Dashboard öffnen, `ECOLOGITS_ENABLED=false` in `.env` setzen (oder ein Modell wählen,
  das EcoLogits nicht kennt und keine manuellen `eco_*`-Parameter hat).
- Einen Prompt analysieren.
- Erwartung: CO₂-/Energie-Kachel zeigt einen Zahlenwert **und** der Indikator daneben
  zeigt "Grobe Schätzung" (nicht mehr "Nicht verfügbar").

### Architektur-/UML-Diagramm der EcoLogits-Implementierung für die Projektpräsentation

**Ziel**: eine Diagramm-Darstellung (UML oder alternative Visualisierung) der
EcoLogits-Integration erstellen — Fallback-Stufen (Anbieter-Lookup → manuelle
Parameter → Formel), beteiligte Module (`ecologits_service.py`,
`sustainability_service.py`, `app/routes/api.py`), Datenfluss zwischen
`/api/analyze`, `/api/estimate-footprint` und `/api/send`.

**Kontext**: Projektpräsentation am 2026-09-12 (Zieltermin, ausgehend vom
2026-08-21) — das Diagramm soll dort gezeigt werden können, um die
EcoLogits-Architektur verständlich zu vermitteln.

**Priorität**: nicht dringend, aber terminlich relevant — rechtzeitig vor der
Präsentation einplanen, nicht erst kurz davor.

### Sequenzdiagramm (Code-Ebene) für den Analyse-Ablauf — für die Präsentation

**Ziel**: ein Sequenzdiagramm, das den tatsächlichen Aufrufverlauf innerhalb
von `analysis_payload()` (`app/routes/api.py`) zeigt — inkl. Nuancen wie
`recommend()` (Empfehlung), das schon *vor* der Dauer-/Nachhaltigkeitsberechnung
läuft, weil Letztere das empfohlene Modell als Eingabe braucht. Ergänzt die
Stationen-Übersicht in `Architektur.md` (§2.1) um die Code-Ebene, ähnlich wie
`docs/TECHNISCHE_DOKUMENTATION.md` §4 das schon fürs Gesamtsystem macht, nur
genauer für diesen einen Ablauf.

**Kontext**: Entstanden beim Cross-Check von Station 2 ("API-Routen") — die
High-Level-Stationen-Sicht ist bewusst grob, für die Präsentation kann ein
Detail-Sequenzdiagramm sinnvoll sein, um Nachfragen zur genauen Reihenfolge
vorzubeugen. Separat vom bereits geplanten EcoLogits-/Fußabdruck-UML-Diagramm
oben — beides zusammen ergibt die Detailebene unter der Stationen-Übersicht.

**Priorität**: zurückgestellt, kommt nach der Stationen-Übersicht und dem
Fußabdruck-Diagramm dran — nur fürs Backlog festgehalten, damit es nicht
verloren geht.

### Reminder: `flask calibrate-ratio` gemeinsam testen, sobald genug echte Sends vorliegen

**Kontext**: `EXPECTED_OUTPUT_RATIO` (Platzhalter `6`) lässt sich per neuem
CLI-Kommando `flask calibrate-ratio` aus echten `UsageLog`-Daten kalibrieren
(Median aus tatsächlich beobachteten Output-/Input-Token-Verhältnissen,
Mindeststichprobe 20 erfolgreiche Sends). Details siehe
`docs/CARBON_FOOTPRINT_REDESIGN.md`, Nachtrag 32.

**Aktueller Stand**: `ENABLE_PROMPT_LOGGING` wurde lokal auf `true` gesetzt,
damit ab jetzt Daten gesammelt werden. Die lokale DB hatte zum Zeitpunkt der
Umsetzung noch 0 Einträge — es braucht also erst eine Weile echte Nutzung.

**To-Do**: In naher Zukunft, sobald genug echte Sends gelaufen sind,
gemeinsam `flask calibrate-ratio` ausführen und prüfen, ob der Vorschlag
plausibel ist, bevor `EXPECTED_OUTPUT_RATIO` in der `.env` angepasst wird.

### Bug `[ERLEDIGT]`: "Benutzerdefinierte Header" im Provider-Formular ohne Wirkung

**Symptom** (beim Ergänzen von Tooltips im Provider-Formular entdeckt):
Das Feld "Benutzerdefinierte Header (JSON)" wird gespeichert
(`custom_headers_json` in `ProviderConfiguration`), aber weder
`OpenAICompatibleProvider` noch `AnthropicProvider` haben dieses Feld beim
eigentlichen API-Aufruf gelesen — die `headers`-Property baute nur
`Accept`/`Content-Type`/`Authorization` bzw. `x-api-key`. Das Feld sah
funktional aus, hatte aber keinerlei Effekt.

**Fix**: Beide `headers`-Properties parsen jetzt `custom_headers_json` und
mergen es in die Request-Header (eigene Werte können Defaults wie
`Authorization` überschreiben, für Gateways mit abweichender
Authentifizierung). Ungültiges JSON wird stillschweigend ignoriert (wie
schon beim Speichern in `apply_provider()` validiert).

Tests: `tests/test_anthropic_provider.py` und neues
`tests/test_openai_compatible_provider.py` (Custom-Header werden
mitgeschickt, ungültiges JSON wird ignoriert). `pytest`: 99/99 grün.

Im selben Zug: 13 Tooltip-Hilfetexte ("?" mit `title`-Attribut, CSS-Klasse
`.field-help`) im Provider-Formular ergänzt (`app/templates/providers.html`),
u. a. für die zuvor öfter verwirrenden EcoLogits-Felder (Aktive/Gesamt-
parameter, PUE, WUE, Strommix-Zone) sowie Provider-Typ, API Base URL,
Modellname, Hosting-Region, Preise, Kontextfenster und Custom Headers.

### Bug `[ERLEDIGT]`: Prompt und Analyse-Ergebnis gingen beim Seitenwechsel verloren

**Symptom**: Wechsel vom Dashboard zu Provider-Einstellungen und zurück
leerte das Prompt-Feld und alle Analyse-Ergebnisse (Empfehlung, Kacheln,
Kosten/Dauer) — erneute Analyse nötig, keine Historie.

**Ursache**: Provider-Einstellungen ist eine eigene Route (`/settings/providers`),
kein SPA-Tab — der Wechsel dorthin und zurück ist ein vollständiger
Seitenneuaufbau, `dashboard.js` startet jedes Mal komplett neu ohne jede
Persistenz.

**Entscheidung (mit Nutzer abgestimmt)**: Persistenz auf Prompt-Text +
letztes Analyse-Ergebnis begrenzt (kein laufender Chat-Verlauf), Speicherort
`sessionStorage` statt `localStorage` — verschwindet mit dem Tab/Browser,
passt zum bestehenden Privacy-by-Design-Ansatz (Prompts werden serverseitig
standardmäßig nicht gespeichert).

**Umsetzung**: `saveState()`/`restoreState()` in `app/static/js/dashboard.js`,
Schlüssel `sag-dashboard-state`. `saveState()` wird bei jeder Prompt-Änderung
und am Ende von `render()` aufgerufen (das deckt sowohl `analyze()` als auch
den "Optimierten Prompt verwenden"-Klick und den Discard-Reset nach dem
Versand ab). `restoreState()` läuft nach `loadProviders()` (nicht davor —
`render()` braucht das bereits geladene `providers`-Array für die
Dropdown-Vorbelegung), ruft bei vorhandenem Zustand einfach `render()` mit
dem gespeicherten Analyse-Objekt erneut auf statt eigene Restore-Logik zu
duplizieren. Beide Funktionen fangen Storage-Fehler ab (z. B. privater
Modus) und lassen die App sonst unverändert weiterlaufen.

Kein neuer Test (keine JS-Testinfrastruktur im Projekt). Cache-Buster
`v='49'`, `pytest` (99 Tests, unverändert) grün, statisch live verifiziert
(neue Funktionen korrekt ausgeliefert) — interaktive Bestätigung
(sessionStorage-Round-trip im echten Browser) noch durch Nutzer-Test
ausstehend.

### Neue Seite: "Info" im Dashboard-Menü (Version, Autoren, Disclaimer)

**Ziel**: Ein Menüpunkt "Info" mit aktueller Versionsangabe, Autoren
("EnvKeMa" als Platzhalter) und einem kurzen Disclaimer (Open Source, KI
kann Fehler machen, das Board bewertet Prompts nicht inhaltlich).

**Versionierungs-Entscheidung**: Bewusst **keine** manuell gepflegte
Versionsnummer, die bei einem Merge in die Mainline vergessen werden
könnte — genau das war die Sorge im Team-Kontext ("muss auch funktionieren,
wenn Kollegen pushen"). Stattdessen wird die Version automatisch aus Git
abgeleitet (`git describe --tags --always --dirty`, `app/services/version_service.py`),
einmal beim App-Start berechnet und in `app.config["APP_VERSION"]`
zwischengespeichert. Ohne Tags liefert das schlicht den kurzen Commit-Hash
(`+dirty`, falls unversionierte Änderungen vorliegen) — immer korrekt für
den tatsächlich laufenden Stand, ganz ohne dass irgendjemand daran denken
muss, eine Zahl hochzuzählen.

**Damit kein AGENTS.md-Thema** — es gibt keinen Prozess-Schritt, den
jemand befolgen müsste, also auch keine Regel, die dokumentiert werden
müsste. Optional für später (z. B. vor der Präsentation): echte Git-Tags
setzen (`git tag v1.0`), dann zeigt `git describe` automatisch den
Tag-Namen statt nur des Hashes — das ist aber eine freiwillige Verschönerung,
keine Voraussetzung.

**Umsetzung**: `app/routes/main.py` (`GET /info`), neues Template
`app/templates/info.html`, Nav-Link in `app/templates/base.html`. Fällt
auf `"unbekannt"` zurück, wenn kein Git verfügbar ist (z. B. gepackte
Auslieferung ohne `.git`-Ordner).

Tests: `tests/test_version_service.py` (neu, 3 Tests: echter Git-Aufruf in
diesem Repo, Fallback bei fehlendem Git, Fallback bei Subprocess-Fehler),
`tests/test_routes.py::test_info_page_shows_version`. `pytest` (104 Tests)
grün. Live verifiziert: `/info` zeigt aktuell `c3d015a-dirty`.

### Finding (bewusst nicht geändert): Compliance Stufe 1 erkennt Bankdaten-Absicht ohne echte IBAN nicht

**Symptom**: Prompt "Ich möchte an einen Käufer per mail meine Kontodaten
zwecks Überweisung des Kaufbetrags für eine Stereoanlage schicken.
Formuliere mir diese Mail." liefert "Compliance 100/100, keine lokalen
Treffer" — erwartet wurde mindestens ein Treffer, da es um Bankdaten geht.

**Analyse**: Kein Regressionsbug (Git-History von `compliance_service.py`
geprüft — die betroffene Stichwortliste enthielt seit ihrer Einführung nur
"kontostand", nie "Kontodaten"). Zwei unabhängige lokale Prüfmechanismen
greifen hier strukturell nicht: (1) Die IBAN-Erkennung ist prüfsummen-
validiert (`_valid_iban()`, Mod-97) und erkennt nur eine tatsächlich im
Text vorhandene, gültige IBAN — mit einer echten Test-IBAN im Prompt
schlägt der Check nachweislich zu (vom Nutzer verifiziert). Der gemeldete
Prompt enthielt aber keine echte Kontonummer, nur die Absicht, eine zu
verschicken. (2) Die Stichwortliste für "Finanzdaten" (`KEYWORDS` in
`compliance_service.py`) enthält nur `kontostand|steuererklärung|gehalt|
finanzdaten` — "Kontodaten" ist dort nicht gelistet, obwohl semantisch
sehr nah an "Finanzdaten".

**Entscheidung**: Bewusst **nicht** geändert (kurz umgesetzt und wieder
zurückgenommen) — ein Kollege plant ohnehin Arbeiten an genau diesem Teil
der Compliance-Erkennung, daher hier keine Änderung an dessen Funktions-
bereich vornehmen. Für die weitere Arbeit festgehalten: Stufe 1 ist eine
deterministische Muster-/Stichwort-Erkennung, kein semantisches
Verständnis — sie erkennt nur Wörter/Werte, die tatsächlich im Prompt
stehen, keine Absicht ohne Stichwort-Treffer. "Kontodaten" als Synonym zu
"Finanzdaten" wäre eine mögliche, sehr kleine Ergänzung der
`KEYWORDS`-Stichwortliste in `compliance_service.py`, falls gewünscht.

### Finding (nur dokumentiert, nicht geändert): Sensibilitäts-Signal aus der semantischen Analyse verpufft vor Anzeige/Routing

**Reproduktion** — folgenden Prompt im Dashboard analysieren (Zielmodus
"Automatisch"):

> Ich muss einen Käufer per E-Mail meine Kontodaten für die Überweisung
> des Kaufbetrages einer Stereoanlage schicken. Formuliere mir eine
> professionelle und freundliche E-Mail, die lediglich Platzhalter für
> die Kontodaten enthält und den Zweck der Überweisung klar benennt. Die
> E-Mail soll darauf achten, dass der Betrag und der Kaufgegenstand
> erwähnt werden, um Sicherheit zu geben.

**Beobachtung**: Das lokale Ollama-Modell (`gemma4`) formuliert die
angeforderte E-Mail korrekt mit Platzhaltern (`IBAN: [Deine IBAN]` usw.) —
kein Fehlverhalten des Modells selbst. Direkt gegen die beiden lokalen
Prüfmechanismen getestet (`inspect_prompt()` und `analyze_with_ollama()`):

- Regex-Check (`compliance_service.py`): `score: 100`, `findings: []` —
  derselbe bereits bekannte "Kontodaten fehlt als Stichwort"-Fund von oben.
- Semantische Analyse (`analysis_service.py`, dasselbe `gemma4`):
  `sensitivity_score: 50`, `compliance_score: 80`,
  `contains_personal_data: false`, Kategorie `"Email_Drafting"`,
  Begründung: *"Standard-E-Mail-Verfassen mit leicht erhöhter Sensibilität
  aufgrund des Themas Finanzen"*. Das Modell nimmt die erhöhte Sensibilität
  also durchaus wahr.

**Der eigentliche Fund liegt in der Verdrahtung dazwischen, nicht im
Regex-Teil**:

1. `analysis_payload()` (`app/routes/api.py:104`) merged den semantischen
   `compliance_score` zwar in `analysis["compliance_score"]`
   (`min(analysis_score, regex_score)`), aber die im Dashboard sichtbare
   "Compliance"-Kachel liest ausschließlich `data.compliance.score` — den
   reinen Regex-Wert. Der informiertere gemergte Wert wird nirgends im
   Frontend gelesen (geprüft: kein Treffer für `analysis.compliance_score`
   in `dashboard.js`) und ist damit für die Anzeige faktisch tot.
2. `recommend()` (`recommendation_service.py:5`) behandelt einen Prompt
   nur dann als "sensibel" (→ bevorzugt lokal/EU), wenn
   `sensitivity_score >= 60`. Mit `50` liegt dieser Prompt knapp
   **unter** der Schwelle → keine Schutzwirkung. Im Zielmodus
   "Automatisch" empfiehlt das Tool dadurch tatsächlich **cloud_small**
   (externe Cloud-API) für einen Prompt, bei dem es ums Versenden von
   Bankdaten per E-Mail geht — obwohl das Modell selbst die erhöhte
   Sensibilität bereits erkannt hat.

**Status**: Nur als Fund dokumentiert, **keine Code-Änderung
vorgenommen** — betrifft `recommendation_service.py` und die
Anzeige-Verdrahtung in `api.py`/`dashboard.js`, nicht die Stichwortliste
aus dem Fund oben. Mögliche spätere Ansatzpunkte, falls gewünscht:
Schwelle in `recommend()` senken (z. B. 50 statt 60), und/oder den
gemergten `compliance_score` statt des reinen Regex-Werts in der
Dashboard-Kachel anzeigen.

### Finding (nur dokumentiert, im Team zu besprechen): Guardian-Stufe-2 macht Analyse und externen Versand spürbar langsam, meldet fälschlich "nicht erreichbar"

**Symptom** (nach lokalem Pull von `granite4.1-guardian:8b` und Regressionstests
gegen die frisch gemergte Compliance-Stufe-2-PR):

- Die Promptanalyse dauert wesentlich länger als vorher, mit durchgängig
  ~50 % CPU-Last und ~8 GB RAM-Nutzung durch Ollama.
- Auch das Absenden eines Folgeprompts an einen **externen** Provider
  (z. B. Anthropic) dauert jetzt sehr viel länger.
- Unabhängig davon erscheint teils der Hinweis "Stufe-2-Prüfung nicht
  verfügbar (Guardian-Modell nicht erreichbar); die Bewertung basiert nur
  auf Stufe 1.", obwohl das Guardian-Modell in Ollama nachweislich
  vorhanden ist.

**Root-Cause-Analyse (im Code nachvollzogen, ein gemeinsamer Grund für
alle drei Effekte)**:

Laut README läuft Stufe 2 (Guardian) sowohl bei `/api/analyze` **als
auch** bei `/api/send` mit — auch wenn der eigentliche Versand an einen
externen Anbieter geht. Beim Senden wird also erst lokal der
Guardian-Check abgewartet, bevor überhaupt die externe Anfrage (z. B. an
Anthropic) losgeschickt wird — das erklärt die Verzögerung auch beim
externen Versand, nicht Anthropic selbst ist langsamer.

`apply_semantic_check()` (`app/services/guardian_service.py`) verwendet
für den Guardian-`OllamaService`-Aufruf `OLLAMA_TIMEOUT_SECONDS` (Default
`60`) — **nicht** das für den normalen Analyse-Call bewusst unlimitierte
`OLLAMA_ANALYSIS_TIMEOUT_SECONDS`. Auf CPU-only-Hardware ohne GPU (siehe
bereits beim EcoLogits-Thema festgestellt: Ryzen 7 8840U, keine dedizierte
GPU) kann ein 8B-Modell für eine einzelne Inferenz durchaus länger als
60 Sekunden brauchen — die beobachtete CPU-/RAM-Last ist echte laufende
Berechnung, kein Hänger. `check_text()` fängt `OllamaError` pauschal ab
(worunter auch `requests.Timeout` fällt) und zeigt dafür denselben Text
wie bei einem echten Verbindungsfehler — "nicht erreichbar" ist in diesem
Fall technisch irreführend, das Modell existiert, antwortet nur nicht
innerhalb der Zeitgrenze.

**Klargestellt, damit es nicht missverstanden wird**: `OLLAMA_GUARDIAN_MODEL`
ist eine globale `.env`/`config.py`-Einstellung (Default bereits
`granite4.1-guardian:8b`, auch ohne eigenen `.env`-Eintrag aktiv) — **keine**
Einstellung im Dashboard unter Provider-Konfiguration; die beiden Systeme
sind unabhängig voneinander.

**Status**: Nur als Fund dokumentiert, keine Code-Änderung vorgenommen —
Guardian ist die Arbeit eines Kollegen, das braucht Team-Abstimmung.
Mögliche Ansatzpunkte für die Diskussion:
- Eigener, großzügigerer Timeout für den Guardian-Call statt der
  gemeinsamen `OLLAMA_TIMEOUT_SECONDS` (analog zur bestehenden Trennung
  bei `OLLAMA_ANALYSIS_TIMEOUT_SECONDS`).
- Ein kleineres/schnelleres Guardian-Modell zumindest für lokale
  Entwicklung ohne GPU.
- `OLLAMA_GUARDIAN_MODEL` in der lokalen `.env` leer lassen, um Stufe 2
  bei Bedarf individuell zu deaktivieren, ohne Code zu ändern.
- Ehrlichere Fehlermeldung, die zwischen echtem Verbindungsfehler und
  Timeout unterscheidet.

### Bonus für die Demo: RAG-Demonstrator für Compliance-Quellenverweis (Knowledge Base)

**Ziel**: Ein bewusst eng abgegrenzter Demonstrator, der in der Präsentation
zeigt, wie ein Compliance-Fund an einen echten Richtlinientext (DSGVO/KDG)
zurückgeführt werden könnte — als Machbarkeits-Beweis für die im
`Architektur.md` als fehlend markierte "Knowledge Base"-Komponente, **nicht**
als Erweiterung der produktiven Stufe-1/Stufe-2-Prüfung.

**Idee**: Kleine, feste Sammlung von 5–10 Richtlinien-Textschnipseln (z. B.
DSGVO Art. 9, KDG § 11 zu Religionszugehörigkeit) im Code. Für einen
vorbereiteten Demo-Prompt sucht eine leichte Ähnlichkeitssuche (z. B. über
Ollamas `nomic-embed-text`-Embeddings, keine neue schwere Abhängigkeit) den
passenden Schnipsel und zeigt ihn als zusätzliche Quellenangabe an der
Compliance-Kachel an, z. B. "Quelle: DSGVO Art. 9 – besondere Kategorien
personenbezogener Daten".

**Abgrenzung**: Läuft hinter einem eigenen Schalter (z. B. `DEMO_MODE=true`,
nach dem Muster bestehender Feature-Flags wie `ECOLOGITS_ENABLED`) und rührt
die getestete Stufe-1/Stufe-2-Logik nicht an — kein Risiko für den
produktiven Pfad kurz vor der Präsentation. In der Präsentation explizit als
Machbarkeits-Demonstrator ankündigen, nicht als bereits produktives Feature.

**Aufwand**: ~3–4 fokussierte Tage (Snippets aussuchen, Retrieval bauen,
UI-Zeile ergänzen, mit dem echten Demo-Prompt durchtesten).

**Priorität**: Bonus, hinter den Guardian-Themen und den anderen
priorisierten Punkten — nur umsetzen, wenn nach den wichtigeren Punkten
(Guardian-Timeout, Architektur.md, Demo-Storyline) noch Zeit bleibt.

### Finding (bewusst so entschieden, kein Fund): Routing Engine liefert nur Empfehlung, keinen automatischen Dispatch

**Frage beim Präsentations-Check**: Entscheidet und verschickt die im
Architekturdiagramm skizzierte "LLM Router"/"Entscheidung"-Komponente
selbstständig an lokales bzw. Cloud-LLM? Antwort: **nein** — und das ist
kein Bug, sondern bewusst so gebaut.

**Ist-Zustand**: `recommendation_service.py` berechnet aus Sensitivität,
Komplexität, gewähltem Modus und Kontextlänge eine Empfehlung
(Modellklasse + Begründung). Der eigentliche Versand (`/api/send`,
`app/routes/api.py`) verschickt ausschließlich an die vom Nutzer im UI
manuell bestätigte `provider_id` — unabhängig davon, was empfohlen wurde.
Die Empfehlung dient nur der Vorbelegung/Anzeige, nicht dem Dispatch.

**Entscheidung**: Bewusst kein automatischer Versand, weil laut
Compliance-Konzept jeder Versand eine explizite, bewusste Nutzerbestätigung
braucht (siehe README „Analyse und Versand sind technisch getrennt").
`Architektur.md` und `docs/TECHNISCHE_DOKUMENTATION.md` sind entsprechend
präzisiert (2026-08-23), damit dieser Ist-Zustand nicht mit einer
unfertigen Automatisierung verwechselt wird.

**Ausblick**: Eine mögliche Erweiterung wäre, dem Nutzer optional einen
automatischen Versand ohne manuelle Bestätigung anzubieten (z. B. als
Opt-in). Wird separat in einer eigenen Verbesserungs-/Ideenliste geführt
und ist für die Projektpräsentation am 12.09.2026 vorgesehen — Priorität
und Machbarkeit dort noch offen.

### Finding (nur dokumentiert, nicht behoben): Fußabdruck-/Kosten-Kacheln zeigen während laufender Analyse noch das alte Ergebnis

**Symptom** (beim manuellen Testen des gemergten Standes vor dem Push
aufgefallen): Klickt man „Prompt analysieren", zeigt der Button „Analyse
läuft …", aber die Fußabdruck- und Kosten-/Dauer-/Compliance-Kacheln zeigen
weiterhin das Ergebnis der vorherigen Analyse — nicht geleert, nicht als
„wird aktualisiert" markiert.

**Ursache** (`app/static/js/dashboard.js`, `analyze()`, Zeile 711–727): Die
Kacheln werden beim Start einer neuen Analyse nicht zurückgesetzt.
`render(data)` läuft erst, nachdem die Antwort von `/api/analyze`
eingetroffen ist:

```js
setAnalyzing(true);          // Button -> "Analyse laeuft ..."
var data = await api("/api/analyze", ...);
render(data);                 // erst hier werden alle Kacheln aktualisiert
```

Da `/api/analyze` serverseitig ohnehin alles (Ollama-Analyse, Compliance,
Kosten, Fußabdruck) in einer einzigen synchronen Antwort liefert, ist es
technisch ausgeschlossen, dass die angezeigten Werte schon zum neuen Prompt
gehören, solange der Button „Analyse läuft …" zeigt — sie stammen zwingend
vom vorherigen Durchlauf.

**Auswirkung für die Live-Demo**: Bei schnellem Prompt-Wechsel könnte der
Eindruck entstehen, das Ergebnis sei schon für den neuen Prompt da, obwohl
Ollama noch rechnet.

**Status**: Nur als Fund dokumentiert, keine Code-Änderung vorgenommen. Für
die Demo reicht es, kurz zu warten, bis „Analyse abgeschlossen." erscheint,
bevor auf die Werte gezeigt wird. Möglicher späterer Fix: Kacheln beim
Start von `analyze()` dimmen oder leeren, bis die neue Antwort da ist.
