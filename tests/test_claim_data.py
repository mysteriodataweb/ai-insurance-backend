from datetime import date
from decimal import Decimal

from app.models.claim import Claim
from app.services.claim_data import apply_extracted_to_claim, compute_missing_fields, low_confidence_fields


def make_claim(**fields) -> Claim:
    defaults = dict(customer_name="A", customer_email="a@example.com", raw_description="x" * 30)
    defaults.update(fields)
    return Claim(**defaults)


def test_extracted_values_fill_only_empty_columns():
    claim = make_claim(incident_type="Fire", estimated_amount=None)
    filled = apply_extracted_to_claim(claim, {
        "incident_type": "Theft",
        "incident_date": "2026-08-20",
        "estimated_amount": 1234.5,
        "policy_number": "P" * 80,
    })
    assert claim.incident_type == "Fire"
    assert claim.incident_date == date(2026, 8, 20)
    assert claim.estimated_amount == Decimal("1234.50")
    assert len(claim.policy_number) == 50
    assert sorted(filled) == ["estimated_amount", "incident_date", "policy_number"]


def test_unparseable_values_are_skipped():
    claim = make_claim()
    filled = apply_extracted_to_claim(claim, {"incident_date": "soon", "estimated_amount": -3})
    assert filled == []
    assert claim.incident_date is None


def test_missing_fields_are_computed_from_declared_and_extracted_data():
    claim = make_claim(incident_type="Fire", incident_location="Tangier")
    missing = compute_missing_fields(claim, {"incident_date": "2026-08-20", "damage_description": "", "policy_number": None})
    assert missing == ["estimated_amount", "damage_description", "policy_number"]


def test_low_confidence_only_counts_extracted_fields():
    extracted = {"incident_date": "2026-08-20", "policy_number": None}
    scores = {"incident_date": 0.3, "policy_number": 0.0, "incident_type": "bad"}
    assert low_confidence_fields(extracted, scores) == ["incident_date"]
