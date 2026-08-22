from time import monotonic
from typing import Callable

import psutil

NOT_CONFIGURED_WARNING = "Lokale Energie-/CO2-Schätzung nicht verfügbar: CPU-TDP nicht konfiguriert (LOCAL_CPU_TDP_WATT)."


def measure_local_generation(
    fn: Callable[[], str], tdp_watts: float | None, carbon_intensity: float
) -> tuple[str, dict | None, str | None]:
    """Schaetzt Energie/CO2 aus CPU-Auslastung waehrend fn() laeuft (TDP x Auslastung x Dauer).
    Keine Hardware-Messung: RAPL/Intel-Power-Gadget sind auf dieser Zielplattform (Windows,
    AMD, keine dedizierte GPU) nicht verfuegbar, siehe CARBON_FOOTPRINT_REDESIGN.md."""
    if not tdp_watts:
        return fn(), None, NOT_CONFIGURED_WARNING
    psutil.cpu_percent(interval=None)
    started = monotonic()
    result = fn()
    elapsed_hours = (monotonic() - started) / 3600
    utilization = psutil.cpu_percent(interval=None) / 100
    energy_wh = round(tdp_watts * utilization * elapsed_hours, 4)
    co2_grams = round(energy_wh / 1000 * carbon_intensity, 4)
    return result, {"energy_wh": energy_wh, "co2_grams": co2_grams, "mode": "local_cpu_estimate"}, None
