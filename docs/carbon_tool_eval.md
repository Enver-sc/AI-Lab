📄 Analyse: CodeCarbon vs. EcoLogits
Markdown‑Export für GitHub

## 1. Überblick
CodeCarbon und EcoLogits sind Open‑Source‑Tools zur Abschätzung des CO₂‑Fußabdrucks von KI‑Modellen.
Sie verfolgen jedoch grundlegend unterschiedliche Ansätze und ergänzen sich ideal.

## 2. CodeCarbon – Hardwarebasierte Emissionsmessung
Zweck
Messung des realen Energieverbrauchs während der Ausführung eines KI‑Modells.

Funktionsweise
Überwacht CPU‑ und GPU‑Nutzung

Misst reale Energieaufnahme

Berechnet CO₂‑Emissionen basierend auf:

Strommix der Region

PUE des Rechenzentrums

Laufzeit

Hardwaretyp

Stärken
Sehr präzise (echte Messung)

Ideal für lokale Modelle, Trainingsjobs, Benchmarking

Perfekt für das lokale Analysemodell im Sustainable AI Gateway

Schwächen
Funktioniert nur mit Hardwarezugriff

Nicht geeignet für Cloud‑LLMs (OpenAI, Anthropic, Azure etc.)

## 3. EcoLogits – Tokenbasierte CO₂‑Schätzung für LLM‑APIs
Zweck
Schätzung des CO₂‑Fußabdrucks einzelner LLM‑Anfragen – ohne Hardwarezugriff.

Funktionsweise
Berechnet Emissionen basierend auf:

Modelltyp (GPT‑4, Claude, Llama‑3 etc.)

Input‑ und Output‑Tokens

Provider‑Informationen:

Hardware (A100, H100 etc.)

Region

Strommix

PUE

Latenz (als Proxy für Rechenzeit)

Stärken
Funktioniert für alle Cloud‑LLMs

Ideal für Dashboards, die CO₂ pro Prompt anzeigen

Ermöglicht konkrete Optimierungsvorschläge:

kürzerer Prompt

kleineres Modell

begrenzte Antwortlänge

Schwächen
Schätzung, keine Messung

Abhängig von Provider‑Transparenz

Modellprofile müssen gepflegt werden

## 4. Direkter Vergleich
Kriterium	CodeCarbon	EcoLogits
Messprinzip	reale Hardwaremessung	statistische Schätzung
Einsatzort	lokale Modelle	Cloud‑LLMs / APIs
Genauigkeit	sehr hoch	abhängig von Providerdaten
Granularität	Energieverbrauch eines gesamten Jobs	CO₂ pro Prompt
Ideal für	Trainingsjobs, lokale Inference	Nutzer‑Dashboards, Prompt‑Optimierung
Hardwarezugriff nötig	ja	nein


## 5. Relevanz für das Projekt Sustainable AI Gateway
Für das lokale Analysemodell
→ CodeCarbon  
Misst den CO₂‑Fußabdruck der lokalen Voranalyse.

Für die CO₂‑Schätzung der späteren LLM‑Nutzung
→ EcoLogits  
Schätzt den CO₂‑Ausstoß der eigentlichen Anfrage an GPT‑4, Claude, Llama‑Cloud etc.

Für Optimierungsvorschläge an Nutzer
EcoLogits ermöglicht:

CO₂‑Vergleich verschiedener Modelle

Einsparpotenziale durch kürzere Prompts

Einsparpotenziale durch begrenzte Antwortlänge

Einsparpotenziale durch Modellwahl

## 6. Fazit
CodeCarbon = reale Messung

EcoLogits = CO₂‑Schätzung pro Prompt

Beide Tools sind sinnvoll, aber für unterschiedliche Zwecke.

EcoLogits ist entscheidend für die Nutzer‑Sensibilisierung, CodeCarbon für die System‑Selbstbewertung.

## Nachtrag (23.08.2026): CodeCarbon in der Praxis verworfen

Die CodeCarbon-Empfehlung aus dieser Analyse (Abschnitt 2/5, "Perfekt für das
lokale Analysemodell im Sustainable AI Gateway") wurde bei der tatsächlichen
Umsetzung geprüft und **nicht umgesetzt**: Auf der Zielhardware (Windows, AMD,
keine dedizierte GPU) liefert CodeCarbon selbst keine echte Messung, sondern
nur einen TDP-basierten Schätzwert — genau den Ansatz, den das Projekt
stattdessen direkt und ohne die zusätzliche Abhängigkeit über eine eigene,
leichtgewichtige `psutil`-CPU-Auslastungsformel umsetzt
(`app/services/local_energy_service.py`).

Vollständige Begründung und Entscheidungsverlauf: [`CARBON_FOOTPRINT_REDESIGN.md`](CARBON_FOOTPRINT_REDESIGN.md),
Nachtrag 24. Diese Analyse bleibt bewusst unverändert als historische
Aufzeichnung des ursprünglichen Plans stehen — nur dieser Nachtrag verweist
auf die später tatsächlich getroffene Entscheidung.