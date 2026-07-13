"""Compliance Stufe 1: regelbasierte PII-Erkennung mit Prüfsummen-Validierung.

Alle Beispieldaten sind erfundene bzw. offizielle Testwerte:
- 4111111111111111 ist die offizielle Visa-Testnummer (gültige Luhn-Prüfsumme).
- DE89370400440532013000 ist der übliche IBAN-Testwert (gültige Mod-97-Prüfsumme).
- 86095742719 erfüllt Struktur- und Prüfziffernregeln der deutschen Steuer-ID
  (ISO 7064, MOD 11,10), ist aber keine real vergebene Nummer.
"""
from app.services.compliance_service import inspect_prompt, redact_sensitive


def test_visa_testnumber_with_valid_luhn_is_detected():
    result = inspect_prompt("Bitte belaste die Karte 4111111111111111 mit dem Betrag.")
    assert "Kreditkartennummer" in result["findings"]
    assert result["contains_personal_data"] is True


def test_visa_testnumber_with_spaces_is_detected():
    result = inspect_prompt("Karte: 4111 1111 1111 1111, Gültigkeit egal.")
    assert "Kreditkartennummer" in result["findings"]


def test_sixteen_digits_without_valid_luhn_are_not_flagged():
    result = inspect_prompt("Die Seriennummer 1234567890123456 gehört zum Gerät.")
    assert "Kreditkartennummer" not in result["findings"]


def test_valid_german_iban_is_detected():
    result = inspect_prompt("Überweise das Honorar auf DE89370400440532013000 bis Freitag.")
    assert "IBAN" in result["findings"]
    assert result["contains_personal_data"] is True


def test_de_string_with_invalid_mod97_checksum_is_not_flagged():
    result = inspect_prompt("Die Vorgangskennung DE21370400440532013000 steht im Formular.")
    assert "IBAN" not in result["findings"]


def test_valid_german_tax_id_is_detected():
    result = inspect_prompt("Meine steuerliche Identifikationsnummer lautet 86095742719.")
    assert "Deutsche Steuer-ID" in result["findings"]
    assert result["contains_personal_data"] is True


def test_arbitrary_eleven_digit_number_is_not_flagged_as_tax_id():
    result = inspect_prompt("Die Sendung 12345678901 wurde gestern storniert.")
    assert "Deutsche Steuer-ID" not in result["findings"]


def test_german_phone_formats_are_detected():
    for prompt in (
        "Ruf mich unter +49 170 1234567 zurück.",
        "Die Zentrale erreichst du unter 030 12345678.",
        "Mobil: 0176-23456789 (nur werktags).",
    ):
        result = inspect_prompt(prompt)
        assert "Telefonnummer" in result["findings"], prompt


def test_years_postal_codes_and_prices_are_not_phone_numbers():
    prompt = (
        "Seit 1999 wohnt sie in 04109 Leipzig, ab 2024 in 80331 München; "
        "die Miete stieg von 1.250,50 Euro auf 1399 Euro."
    )
    result = inspect_prompt(prompt)
    assert "Telefonnummer" not in result["findings"]
    assert result["level"] == "green"


def test_many_harmless_number_sequences_do_not_turn_red():
    prompt = (
        "Bestellnummer 9876543210987654, Seriennummer 1234567890123456, "
        "Trackingcode 55555555555555555555, Chargennummer 1111111111111111 "
        "und Artikelnummer 2222222222222222 bitte gemeinsam prüfen."
    )
    result = inspect_prompt(prompt)
    assert result["level"] != "red"
    assert result["contains_personal_data"] is False


def test_multiple_validated_pii_findings_still_reach_red():
    prompt = (
        "Karte 4111111111111111, IBAN DE89370400440532013000, "
        "Steuer-ID 86095742719, erreichbar unter +49 170 1234567, "
        "Mail an max.mustermann@example.com."
    )
    result = inspect_prompt(prompt)
    assert result["level"] == "red"
    assert result["contains_personal_data"] is True


def test_redaction_masks_only_validated_credit_cards():
    assert "4111111111111111" not in redact_sensitive("Karte 4111111111111111 bitte sperren.")
    assert "1234567890123456" in redact_sensitive("Seriennummer 1234567890123456 notieren.")
