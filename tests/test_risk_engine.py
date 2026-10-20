from datetime import date, timedelta

from app.services.risk_engine import RiskInputs, calculate_risk, get_risk_level

TODAY = date(2026, 10, 20)


def inputs(**overrides) -> RiskInputs:
    values = dict(
        declared_amount=None,
        extracted_amount=None,
        incident_date=TODAY - timedelta(days=1),
        missing_fields=[],
        low_confidence_fields=[],
        prior_claims_count=0,
        today=TODAY,
    )
    values.update(overrides)
    return RiskInputs(**values)


def test_clean_small_claim_is_low_risk():
    score, signals = calculate_risk(inputs(declared_amount=2500, extracted_amount=2500))
    assert score == 0
    assert signals == []
    assert get_risk_level(score) == "low"


def test_high_risk_is_reachable():
    score, signals = calculate_risk(inputs(
        declared_amount=30000,
        extracted_amount=18000,
        incident_date=TODAY - timedelta(days=100),
        low_confidence_fields=["incident_date"],
    ))
    assert get_risk_level(score) == "high"
    assert len(signals) == 5


def test_score_is_capped_at_100():
    score, _ = calculate_risk(inputs(
        declared_amount=50000,
        extracted_amount=10000,
        incident_date=TODAY - timedelta(days=200),
        missing_fields=["policy_number", "incident_location"],
        low_confidence_fields=["incident_date"],
        prior_claims_count=3,
    ))
    assert score == 100


def test_large_amount_requires_manual_review():
    score, _ = calculate_risk(inputs(declared_amount=15000, extracted_amount=15000))
    assert get_risk_level(score) == "medium"


def test_extracted_amount_used_when_nothing_declared():
    score, signals = calculate_risk(inputs(extracted_amount=12500))
    assert score == 30
    assert "High claim amount" in signals[0]


def test_amount_mismatch_is_flagged():
    _, signals = calculate_risk(inputs(declared_amount=5000, extracted_amount=3000))
    assert any("differs from the description" in s for s in signals)


def test_small_amount_difference_is_tolerated():
    _, signals = calculate_risk(inputs(declared_amount=3100, extracted_amount=3000))
    assert not any("differs" in s for s in signals)


def test_missing_fields_and_timing_signals():
    _, signals = calculate_risk(inputs(missing_fields=["policy_number"], incident_date=TODAY - timedelta(days=45)))
    assert "Missing field: policy_number (+10)" in signals
    assert any(s.startswith("Late reporting (45 days") for s in signals)

    _, signals = calculate_risk(inputs(incident_date=TODAY + timedelta(days=5)))
    assert any("future" in s for s in signals)


def test_repeat_claimant_signal():
    _, signals = calculate_risk(inputs(prior_claims_count=2))
    assert any("2 other claims" in s for s in signals)


def test_levels_boundaries():
    assert get_risk_level(30) == "low"
    assert get_risk_level(31) == "medium"
    assert get_risk_level(70) == "medium"
    assert get_risk_level(71) == "high"
