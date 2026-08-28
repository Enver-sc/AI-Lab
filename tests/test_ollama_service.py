from app.services.ollama_service import OllamaService


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload
        self.status_code = 200

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


class RecordingSession:
    def __init__(self):
        self.last_json = None

    def post(self, url, json, timeout):
        self.last_json = json
        return FakeResponse({"response": "Ein Gnu ist eine Antilopenart."})


def test_generate_omits_format_by_default():
    # Regression: format="json" fest fuer jeden generate()-Aufruf zwang auch echte
    # Chat-Antworten in strukturiertes JSON, siehe Tasklist.md ("Ollama-Antworten beim
    # echten Versand ... in JSON-Struktur"). Ohne json_mode darf "format" gar nicht
    # im Request-Body auftauchen -- Ollama liefert sonst gezwungenermassen JSON statt
    # normalem Fliesstext.
    session = RecordingSession()
    service = OllamaService("http://localhost", "x", session=session)
    answer = service.generate("Was ist ein Gnu?")
    assert "format" not in session.last_json
    assert answer == "Ein Gnu ist eine Antilopenart."


def test_generate_sets_format_json_when_requested():
    session = RecordingSession()
    service = OllamaService("http://localhost", "x", session=session)
    service.generate("Analysiere diesen Prompt.", system="System", json_mode=True)
    assert session.last_json["format"] == "json"


def test_generate_omits_think_by_default_and_sends_it_when_set():
    # think gehoert auf die oberste Payload-Ebene (nicht in options); ohne Angabe
    # bleibt es weg, damit Modelle ohne Thinking-Faehigkeit keinen Fehler bekommen.
    session = RecordingSession()
    service = OllamaService("http://localhost", "x", session=session)
    service.generate("Hallo")
    assert "think" not in session.last_json
    service.generate_raw("Hallo", think=False)
    assert session.last_json["think"] is False
