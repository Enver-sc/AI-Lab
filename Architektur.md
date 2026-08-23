Gesamtarchitektur
                Anwender

                   │
                   ▼

        Dashboard (Weboberfläche)

                   │
                   ▼

        Lokaler AI Agent (Agentic AI)

        ├── Prompt Optimizer
        ├── Compliance Checker
        ├── CO2 Calculator
        ├── Cost Calculator
        ├── LLM Router
        ├── Learning Engine
        └── Knowledge Base

                   │
         Entscheidung

     ┌────────────┴─────────────┐

     ▼                          ▼

lokales LLM                Cloud LLM

(Ollama)              (GPT, Claude, Gemini)

---

**Ist-Zustand „Entscheidung"/LLM Router (Stand 2026-08-23):** Der Schritt ist eine
regelbasierte *Empfehlung* (`recommendation_service.py`), kein automatischer
Dispatch. Der eigentliche Versand (`/api/send`) verschickt ausschließlich an die
vom Nutzer im UI manuell bestätigte Provider-/Modellwahl — bewusst so entschieden,
weil jeder Versand laut Compliance-Konzept eine explizite Nutzerbestätigung
braucht, kein automatisch agierender Agent. Dieses Diagramm zeigt noch den
ursprünglichen Woche-1-Entwurf; ein Update inkl. UML-Diagramm der tatsächlichen
Implementierung ist vor der Projektpräsentation am 12.09.2026 geplant.
