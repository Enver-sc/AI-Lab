from unittest.mock import patch


def test_zero_analysis_timeout_means_unlimited(client, csrf, app):
    app.config["OLLAMA_ANALYSIS_TIMEOUT_SECONDS"] = 0
    fallback = ({
        "prompt_category": "test",
        "complexity_score": 10,
        "sensitivity_score": 0,
        "compliance_score": 100,
        "contains_personal_data": False,
        "contains_confidential_data": False,
        "copyright_risk": "low",
        "recommended_model_class": "local_small",
        "optimization_suggestions": [],
        "optimized_prompt": "Hallo",
        "short_reasoning": "Test",
    }, None)
    with patch("app.routes.api.OllamaService") as service_class, patch(
        "app.routes.api.analyze_with_ollama", return_value=fallback
    ):
        response = client.post(
            "/api/analyze",
            json={"prompt": "Hallo"},
            headers={"X-CSRF-Token": csrf},
        )
    assert response.status_code == 200
    assert service_class.call_args.args[2] is None
