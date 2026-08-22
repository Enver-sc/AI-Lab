from unittest.mock import patch

from app.services.local_energy_service import NOT_CONFIGURED_WARNING, measure_local_generation


def test_missing_tdp_returns_none_with_warning():
    result, energy, warning = measure_local_generation(lambda: "Antwort", None, 350)
    assert result == "Antwort"
    assert energy is None
    assert warning == NOT_CONFIGURED_WARNING


def test_configured_tdp_computes_energy_and_co2_from_cpu_utilization():
    with patch("app.services.local_energy_service.psutil.cpu_percent", side_effect=[0, 50]):
        result, energy, warning = measure_local_generation(lambda: "Antwort", 30, 350)
    assert result == "Antwort"
    assert warning is None
    assert energy["mode"] == "local_cpu_estimate"
    assert energy["energy_wh"] >= 0
    assert energy["co2_grams"] == round(energy["energy_wh"] / 1000 * 350, 4)


def test_zero_utilization_yields_zero_energy_not_none():
    with patch("app.services.local_energy_service.psutil.cpu_percent", side_effect=[0, 0]):
        _, energy, warning = measure_local_generation(lambda: "Antwort", 30, 350)
    assert warning is None
    assert energy["energy_wh"] == 0
    assert energy["co2_grams"] == 0
