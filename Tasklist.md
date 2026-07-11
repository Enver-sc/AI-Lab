Berechnungsgrundlagen – Recherchen
- CO₂ (macht Mario)
- Token / Kosten (macht Enver)
- LLM‑Auswahl (macht Enver)
- Compliance Stufe 1/2 (macht Keng)
- Routing Engine (macht Mario, aber wahrschl. Überlappung zu LLM Auswahl)

Implementierung Berechnungsgrundlagen
- Beispiel: Steering Files
- Alternativen (macht Mario in Vorbereitung zur Implementierung)

----

8‑Wochen‑Taskliste**, so dass ihr **spätestens am 10.09.** eine stabile Live‑Demo für Euer Projekt *Sustainable AI Gateway*, inklusive einer **vollen Woche Puffer für den Dry‑Run**.  

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

Hier ist deine **angepasste 8‑Wochen‑Taskliste**, so dass ihr **spätestens am 10.09.** eine stabile Live‑Demo zeigen könnt.  
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
Ihr habt am 10.09. eine **stabile, lokal lauffähige Demo**, die CO₂‑Fußabdruck, Kosten, Dauer, Compliance und Optimierungsvorschläge für Prompts liefert.

Wenn du willst, kann ich dir die Taskliste auch als **GitHub‑README‑Taskliste mit Checkboxen** formatieren.
