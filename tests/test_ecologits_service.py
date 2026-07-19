from app.services.ecologits_service import FALLBACK_WARNING, compute_impacts

BASE_CONFIG = {
    "ECOLOGITS_ENABLED": True,
    "ECOLOGITS_ELECTRICITY_MIX_ZONE": "DEU",
    "ECOLOGITS_DEFAULT_DATACENTER_PUE": 1.2,
    "ECOLOGITS_DEFAULT_DATACENTER_WUE": 1.8,
}

CATALOG_MODEL = {
    "ecologits_provider": None,
    "eco_active_params_b": 8,
    "eco_total_params_b": 8,
    "eco_datacenter_pue": None,
    "eco_datacenter_wue": None,
    "eco_electricity_mix_zone": None,
}


class FakeProvider:
    def __init__(self, **kwargs):
        self.ecologits_provider = kwargs.get("ecologits_provider")
        self.model_name = kwargs.get("model_name")
        self.eco_active_params_b = kwargs.get("eco_active_params_b")
        self.eco_total_params_b = kwargs.get("eco_total_params_b")
        self.eco_datacenter_pue = kwargs.get("eco_datacenter_pue")
        self.eco_datacenter_wue = kwargs.get("eco_datacenter_wue")
        self.eco_electricity_mix_zone = kwargs.get("eco_electricity_mix_zone")


def test_disabled_returns_none_silently():
    result, warning = compute_impacts(200, 3.0, app_config={"ECOLOGITS_ENABLED": False})
    assert result is None and warning is None


def test_no_app_config_returns_none_silently():
    result, warning = compute_impacts(200, 3.0)
    assert result is None and warning is None


def test_manual_path_used_by_default():
    result, warning = compute_impacts(200, 3.0, catalog_model=CATALOG_MODEL, app_config=BASE_CONFIG)
    assert result["mode"] == "compute_llm_impacts"
    assert result["co2_grams"] > 0
    assert warning is None


def test_adpe_is_in_readable_microgram_range():
    result, _ = compute_impacts(200, 3.0, catalog_model=CATALOG_MODEL, app_config=BASE_CONFIG)
    # Regression guard: adpe_kg_sb_eq (unrounded, kg-scale ~1e-10) rendered as raw scientific
    # notation in the dashboard. adpe_ug_sb_eq must stay in a normal, non-exponential JS number range.
    assert 0 < result["adpe_ug_sb_eq"] < 1000


def test_provider_lookup_path_used_when_ecologits_provider_set():
    provider = FakeProvider(ecologits_provider="openai", model_name="gpt-3.5-turbo")
    result, warning = compute_impacts(200, 3.0, provider=provider, app_config=BASE_CONFIG)
    assert result["mode"] == "llm_impacts"
    assert result["co2_grams"] > 0


def test_missing_params_returns_none_without_warning():
    model = {**CATALOG_MODEL, "eco_active_params_b": None, "eco_total_params_b": None}
    result, warning = compute_impacts(200, 3.0, catalog_model=model, app_config=BASE_CONFIG)
    assert result is None and warning is None


def test_unknown_model_name_falls_back_with_warning():
    provider = FakeProvider(ecologits_provider="openai", model_name="does-not-exist-9000")
    result, warning = compute_impacts(200, 3.0, provider=provider, app_config=BASE_CONFIG)
    assert result is None
    assert warning == FALLBACK_WARNING


def test_unregistered_zone_falls_back_to_world_average():
    model = {**CATALOG_MODEL, "eco_electricity_mix_zone": "ZZZ"}
    result, warning = compute_impacts(200, 3.0, catalog_model=model, app_config=BASE_CONFIG)
    assert result is not None and result["mode"] == "compute_llm_impacts"


def test_provider_field_overrides_catalog():
    provider = FakeProvider(eco_active_params_b=1, eco_total_params_b=1)
    result_provider, _ = compute_impacts(200, 3.0, provider=provider, catalog_model=CATALOG_MODEL, app_config=BASE_CONFIG)
    result_catalog, _ = compute_impacts(200, 3.0, catalog_model=CATALOG_MODEL, app_config=BASE_CONFIG)
    assert result_provider["energy_kwh"] < result_catalog["energy_kwh"]


def test_catalog_falls_back_to_global_config_when_unset():
    low_pue = {**BASE_CONFIG, "ECOLOGITS_DEFAULT_DATACENTER_PUE": 1.0}
    high_pue = {**BASE_CONFIG, "ECOLOGITS_DEFAULT_DATACENTER_PUE": 2.0}
    result_low, _ = compute_impacts(200, 3.0, catalog_model=CATALOG_MODEL, app_config=low_pue)
    result_high, _ = compute_impacts(200, 3.0, catalog_model=CATALOG_MODEL, app_config=high_pue)
    assert result_low["energy_kwh"] < result_high["energy_kwh"]
