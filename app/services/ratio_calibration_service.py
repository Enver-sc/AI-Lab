import statistics

from ..models import UsageLog

MIN_SAMPLES = 20


def calibrate_expected_output_ratio(min_samples: int = MIN_SAMPLES) -> dict:
    """Schaetzt EXPECTED_OUTPUT_RATIO aus echten Sends (UsageLog), nicht aus der
    bisherigen Schaetzung selbst -- estimated_output_tokens ist bei echten Sends der
    tatsaechlich beobachtete Output (siehe app/routes/api.py send())."""
    logs = UsageLog.query.filter_by(request_status="success").all()
    ratios = [log.estimated_output_tokens / log.input_tokens for log in logs if log.input_tokens > 0]
    sample_size = len(ratios)
    if sample_size < min_samples:
        return {"sufficient": False, "sample_size": sample_size, "min_samples": min_samples, "suggested_ratio": None}
    return {
        "sufficient": True,
        "sample_size": sample_size,
        "min_samples": min_samples,
        "suggested_ratio": round(statistics.median(ratios), 2),
    }
