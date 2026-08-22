from app.extensions import db
from app.models import UsageLog
from app.services.ratio_calibration_service import calibrate_expected_output_ratio


def add_log(app, input_tokens, output_tokens, status="success"):
    with app.app_context():
        db.session.add(UsageLog(
            prompt_hash="x", input_tokens=input_tokens, estimated_output_tokens=output_tokens,
            request_status=status,
        ))
        db.session.commit()


def test_reports_insufficient_data_below_minimum(app):
    with app.app_context():
        result = calibrate_expected_output_ratio(min_samples=20)
    assert result["sufficient"] is False
    assert result["sample_size"] == 0
    assert result["suggested_ratio"] is None


def test_calibrates_median_ratio_from_successful_sends(app):
    # Ratios 2,2,2,2,2,2,2,2,2,2 (10x) und 10,10,...,10 (10x) -> Median liegt zwischen
    # beiden Gruppen; bei geradzahliger Stichprobe ist das der Mittelwert der beiden
    # mittleren Werte (2 und 10) = 6.
    for _ in range(10):
        add_log(app, input_tokens=100, output_tokens=200)
    for _ in range(10):
        add_log(app, input_tokens=100, output_tokens=1000)
    with app.app_context():
        result = calibrate_expected_output_ratio(min_samples=20)
    assert result["sufficient"] is True
    assert result["sample_size"] == 20
    assert result["suggested_ratio"] == 6.0


def test_ignores_failed_requests(app):
    for _ in range(25):
        add_log(app, input_tokens=100, output_tokens=200, status="failed")
    with app.app_context():
        result = calibrate_expected_output_ratio(min_samples=20)
    assert result["sufficient"] is False
    assert result["sample_size"] == 0


def test_ignores_zero_input_tokens_to_avoid_division_by_zero(app):
    for _ in range(25):
        add_log(app, input_tokens=0, output_tokens=5)
    with app.app_context():
        result = calibrate_expected_output_ratio(min_samples=20)
    assert result["sufficient"] is False
    assert result["sample_size"] == 0


def test_cli_command_reports_insufficient_data(app):
    runner = app.test_cli_runner()
    result = runner.invoke(args=["calibrate-ratio"])
    assert "Zu wenig Daten" in result.output


def test_cli_command_reports_suggested_ratio(app):
    for _ in range(20):
        add_log(app, input_tokens=100, output_tokens=300)
    runner = app.test_cli_runner()
    result = runner.invoke(args=["calibrate-ratio"])
    assert "Vorgeschlagener EXPECTED_OUTPUT_RATIO (Median): 3.0" in result.output
