import logging

from ecologits.electricity_mix_repository import electricity_mixes
from ecologits.exceptions import EcoLogitsError
from ecologits.impacts.llm import compute_llm_impacts
from ecologits.tracers.utils import llm_impacts
from ecologits.utils.range_value import RangeValue

logger = logging.getLogger(__name__)
KNOWN_PROVIDERS = {"openai", "anthropic", "cohere", "google_genai", "huggingface_hub", "mistralai"}
FALLBACK_ZONE = "WOR"
FALLBACK_WARNING = "EcoLogits-Berechnung nicht möglich; Standardschätzung wird verwendet."


def _scalar(value: int | float | RangeValue) -> float:
    return value.mean if isinstance(value, RangeValue) else float(value)


def _resolve(field, provider, catalog_model, default=None):
    if provider is not None and getattr(provider, field, None) not in (None, ""):
        return getattr(provider, field)
    if catalog_model is not None and catalog_model.get(field) not in (None, ""):
        return catalog_model[field]
    return default


def _to_impacts_dict(impacts, mode: str) -> dict:
    return {
        "energy_kwh": round(_scalar(impacts.energy.value), 6),
        "co2_grams": round(_scalar(impacts.gwp.value) * 1000, 4),
        "water_liters": round(_scalar(impacts.wcf.value), 4),
        # ADPe liegt typischerweise bei 1e-10..1e-11 kg -- in kg gerundet waere der Wert im
        # Frontend nicht mehr ohne wissenschaftliche Notation darstellbar. Mikrogramm (kg * 1e9)
        # ergibt eine lesbare Groessenordnung, daher der Einheitswechsel im Feldnamen.
        "adpe_ug_sb_eq": round(_scalar(impacts.adpe.value) * 1e9, 4),
        "mode": mode,
    }


def compute_impacts(output_tokens, request_latency_seconds, provider=None, catalog_model=None, app_config=None):
    """Liefert (impacts_dict | None, warning | None) und wirft nie -- Aufrufer fallen bei
    None auf die bestehende Formel in sustainability_service.py zurueck."""
    if not app_config or not app_config.get("ECOLOGITS_ENABLED"):
        return None, None
    eco_provider = _resolve("ecologits_provider", provider, catalog_model)
    zone = _resolve("eco_electricity_mix_zone", provider, catalog_model, app_config.get("ECOLOGITS_ELECTRICITY_MIX_ZONE"))
    try:
        if eco_provider in KNOWN_PROVIDERS:
            return _compute_via_provider_lookup(eco_provider, provider, output_tokens, request_latency_seconds, zone)
        return _compute_via_manual_parameters(provider, catalog_model, app_config, output_tokens, request_latency_seconds, zone)
    except EcoLogitsError as exc:
        logger.warning("EcoLogits-Berechnung fehlgeschlagen: %s", exc)
        return None, FALLBACK_WARNING
    # EcoLogits' Fehlerarten sind nicht vollstaendig dokumentiert (z. B. Pydantic-Validierung
    # bei unplausiblen Parametern) -- diese Schicht darf die Route trotzdem nie zum Absturz bringen.
    except Exception as exc:
        logger.warning("EcoLogits-Berechnung fehlgeschlagen: %s", exc)
        return None, FALLBACK_WARNING


def _compute_via_provider_lookup(eco_provider, provider, output_tokens, request_latency_seconds, zone):
    model_name = provider.model_name if provider is not None else None
    if not model_name:
        return None, None
    impacts = llm_impacts(provider=eco_provider, model_name=model_name, output_token_count=output_tokens, request_latency=request_latency_seconds, electricity_mix_zone=zone)
    if impacts.has_errors:
        return None, FALLBACK_WARNING
    warning = "Schätzung mit Unsicherheiten: " + " ".join(w.message for w in impacts.warnings) if impacts.has_warnings else None
    return _to_impacts_dict(impacts, "llm_impacts"), warning


def _compute_via_manual_parameters(provider, catalog_model, app_config, output_tokens, request_latency_seconds, zone):
    active = _resolve("eco_active_params_b", provider, catalog_model)
    total = _resolve("eco_total_params_b", provider, catalog_model)
    if active is None or total is None:
        return None, None
    pue = _resolve("eco_datacenter_pue", provider, catalog_model, app_config.get("ECOLOGITS_DEFAULT_DATACENTER_PUE"))
    wue = _resolve("eco_datacenter_wue", provider, catalog_model, app_config.get("ECOLOGITS_DEFAULT_DATACENTER_WUE"))
    mix = electricity_mixes.find_electricity_mix(zone=zone) or electricity_mixes.find_electricity_mix(zone=FALLBACK_ZONE)
    if mix is None:
        return None, FALLBACK_WARNING
    impacts = compute_llm_impacts(
        model_active_parameter_count=active,
        model_total_parameter_count=total,
        output_token_count=output_tokens,
        if_electricity_mix_adpe=mix.adpe,
        if_electricity_mix_pe=mix.pe,
        if_electricity_mix_gwp=mix.gwp,
        if_electricity_mix_wue=mix.wue,
        datacenter_pue=pue,
        datacenter_wue=wue,
        request_latency=request_latency_seconds,
    )
    return _to_impacts_dict(impacts, "compute_llm_impacts"), None
