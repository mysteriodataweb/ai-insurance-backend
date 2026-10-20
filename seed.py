"""
Seed script for AI Insurance Operations Platform.

Adds realistic sample claims. Risk scores are computed with the real risk engine so the
demo data always matches the rules. Refuses to run on a non-empty database unless --reset
is passed (which DROPS every table first).

    python seed.py            # seed an empty database
    python seed.py --reset    # wipe everything, then seed
"""

import argparse
import asyncio
import sys
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import func, select

from app.database import async_session, engine, Base
from app.models import Claim, ClaimExtraction, Conversation, RiskAssessment, ClaimAction, AuditLog
from app.services.claim_data import compute_missing_fields, low_confidence_fields
from app.services.risk_engine import RiskInputs, calculate_risk, get_recommended_action, get_risk_level
from app.timeutils import utcnow

OPS_REVIEWER = "ops.reviewer@insurance.ai"


def days_ago(n: int) -> date:
    return date.today() - timedelta(days=n)


SAMPLE_CLAIMS = [
    {
        "claim": {
            "customer_name": "Ahmed Benali",
            "customer_email": "ahmed.benali@email.com",
            "policy_number": "POL-2024-001",
            "raw_description": "I had a car accident yesterday in Casablanca. Another vehicle hit my car at an intersection. The front bumper and hood are damaged. I estimate the repair will cost around $3,000. I have the other driver's license plate number and photos of the damage.",
            "incident_type": "Car accident",
            "incident_date": days_ago(1),
            "incident_location": "Casablanca",
            "estimated_amount": Decimal("3000.00"),
        },
        "submitted_hours_ago": 20,
        "status": "approved",
        "extraction": {
            "extracted_data": {
                "incident_type": "Car accident",
                "incident_date": days_ago(1).isoformat(),
                "incident_location": "Casablanca",
                "estimated_amount": 3000,
                "damage_description": "Front bumper and hood damaged",
                "other_party_info": "Other driver's license plate available",
                "policy_number": "POL-2024-001",
            },
            "confidence_scores": {
                "incident_type": 0.95, "incident_date": 0.90, "incident_location": 0.95,
                "estimated_amount": 0.70, "damage_description": 0.85, "other_party_info": 0.80,
                "policy_number": 1.0,
            },
        },
        "conversations": [
            {"role": "agent", "message": "Thank you for submitting your claim. Could you please provide photos of the damage to support your claim?", "message_type": "info_request"},
            {"role": "customer", "message": "Yes, I have photos. I will upload them now. The front of the car is quite badly damaged.", "message_type": "answer"},
        ],
        "actions": [
            {"action": "approved", "performed_by": OPS_REVIEWER, "notes": "All documentation received. Standard processing.", "hours_after": 6},
        ],
    },
    {
        "claim": {
            "customer_name": "Fatima Zahra",
            "customer_email": "fatima.zahra@email.com",
            "policy_number": None,
            "raw_description": "My apartment was flooded last week due to a pipe burst in the building. The living room and kitchen are damaged. Furniture worth $5,000 was destroyed. Water damage to the walls and floor.",
            "incident_type": "Water damage",
            "incident_date": days_ago(7),
            "incident_location": "Rabat",
            "estimated_amount": Decimal("5000.00"),
        },
        "submitted_hours_ago": 30,
        "status": "follow_up",
        "extraction": {
            "extracted_data": {
                "incident_type": "Water damage",
                "incident_date": days_ago(7).isoformat(),
                "incident_location": None,
                "estimated_amount": 5000,
                "damage_description": "Living room and kitchen flooded. Furniture destroyed. Water damage to walls and floor.",
                "other_party_info": None,
                "policy_number": None,
            },
            "confidence_scores": {
                "incident_type": 0.90, "incident_date": 0.75, "incident_location": 0.0,
                "estimated_amount": 0.60, "damage_description": 0.80, "other_party_info": 0.0,
                "policy_number": 0.0,
            },
        },
        "conversations": [
            {"role": "agent", "message": "I understand your apartment was flooded. To process your claim, could you provide your insurance policy number?", "message_type": "question"},
        ],
        "actions": [],
    },
    {
        "claim": {
            "customer_name": "Youssef Alami",
            "customer_email": "youssef@email.com",
            "policy_number": "POL-2024-003",
            "raw_description": "I need to file a claim for my stolen laptop. It was taken from my hotel room in Marrakech while I was at dinner. The laptop is a MacBook Pro worth $2,500. I have a police report.",
            "incident_type": "Theft",
            "incident_date": days_ago(3),
            "incident_location": "Marrakech",
            "estimated_amount": Decimal("2500.00"),
        },
        "submitted_hours_ago": 50,
        "status": "under_review",
        "extraction": {
            "extracted_data": {
                "incident_type": "Theft",
                "incident_date": days_ago(3).isoformat(),
                "incident_location": "Marrakech",
                "estimated_amount": 2500,
                "damage_description": "MacBook Pro stolen from hotel room",
                "other_party_info": "Police report available",
                "policy_number": None,
            },
            "confidence_scores": {
                "incident_type": 0.90, "incident_date": 0.85, "incident_location": 0.90,
                "estimated_amount": 0.75, "damage_description": 0.80, "other_party_info": 0.70,
                "policy_number": 0.0,
            },
        },
        "conversations": [
            {"role": "agent", "message": "I see you filed a theft claim. Do you have a copy of the police report?", "message_type": "question"},
            {"role": "customer", "message": "Yes, I have the police report. The report number is MRK-2026-4521.", "message_type": "answer"},
        ],
        "actions": [],
    },
    {
        "claim": {
            "customer_name": "Sara Idrissi",
            "customer_email": "sara.idrissi@email.com",
            "policy_number": "POL-2024-004",
            "raw_description": "There was a fire in my shop two days ago. The fire started from an electrical fault. The entire inventory was destroyed. I estimate the total loss at $15,000. The fire brigade came and confirmed it was an electrical issue.",
            "incident_type": "Fire",
            "incident_date": days_ago(2),
            "incident_location": "Tangier",
            "estimated_amount": Decimal("15000.00"),
        },
        "submitted_hours_ago": 40,
        "status": "escalated",
        "extraction": {
            "extracted_data": {
                "incident_type": "Fire",
                "incident_date": days_ago(2).isoformat(),
                "incident_location": "Tangier",
                "estimated_amount": 15000,
                "damage_description": "Entire inventory destroyed by fire. Electrical fault confirmed by fire brigade.",
                "other_party_info": "Fire brigade report available",
                "policy_number": None,
            },
            "confidence_scores": {
                "incident_type": 0.95, "incident_date": 0.90, "incident_location": 0.95,
                "estimated_amount": 0.80, "damage_description": 0.90, "other_party_info": 0.85,
                "policy_number": 0.0,
            },
        },
        "conversations": [
            {"role": "agent", "message": "I'm sorry to hear about the fire in your shop. Could you provide the fire brigade report number?", "message_type": "question"},
            {"role": "customer", "message": "The fire brigade report number is TNG-FB-2026-089. They confirmed it was an electrical fault in the wiring.", "message_type": "answer"},
        ],
        "actions": [
            {"action": "escalated", "performed_by": OPS_REVIEWER, "notes": "High-value fire claim escalated for investigation.", "hours_after": 3},
        ],
    },
    {
        "claim": {
            "customer_name": "Karim Mansouri",
            "customer_email": "karim.mansouri@email.com",
            "policy_number": "POL-2023-118",
            "raw_description": "Some jewelry was stolen from my house in Agadir back in July. Rings, a gold necklace and a watch, worth about $18,000 in total. I did not notice it right away. My policy number is POL-2023-118.",
            "incident_type": "Theft",
            "incident_date": days_ago(100),
            "incident_location": "Agadir",
            "estimated_amount": Decimal("30000.00"),
        },
        "submitted_hours_ago": 10,
        "status": "under_review",
        "extraction": {
            "extracted_data": {
                "incident_type": "Theft",
                "incident_date": days_ago(100).isoformat(),
                "incident_location": "Agadir",
                "estimated_amount": 18000,
                "damage_description": "Rings, a gold necklace and a watch stolen from the house",
                "other_party_info": None,
                "policy_number": "POL-2023-118",
            },
            "confidence_scores": {
                "incident_type": 0.90, "incident_date": 0.35, "incident_location": 0.85,
                "estimated_amount": 0.75, "damage_description": 0.85, "other_party_info": 0.0,
                "policy_number": 1.0,
            },
        },
        "conversations": [],
        "actions": [],
    },
    {
        "claim": {
            "customer_name": "Omar Tazi",
            "customer_email": "omar.tazi@email.com",
            "policy_number": None,
            "raw_description": "I was involved in a minor car accident. My car was parked and someone hit it and drove away. I found a dent on the rear bumper. Repair should be around $800.",
            "incident_type": "Car accident",
            "incident_date": days_ago(2),
            "incident_location": "Fez",
            "estimated_amount": Decimal("800.00"),
        },
        "submitted_hours_ago": 2,
        "status": "submitted",
        "extraction": None,
        "conversations": [],
        "actions": [],
    },
]


async def seed(reset: bool) -> None:
    async with engine.begin() as conn:
        if reset:
            await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as db:
        existing = (await db.execute(select(func.count(Claim.id)))).scalar()
        if existing:
            print(f"Database already contains {existing} claims. Use --reset to wipe it and reseed.")
            return

        now = utcnow()
        for sample in SAMPLE_CLAIMS:
            submitted_at = now - timedelta(hours=sample["submitted_hours_ago"])
            claim = Claim(**sample["claim"], status=sample["status"], created_at=submitted_at, updated_at=submitted_at)
            db.add(claim)
            await db.flush()
            db.add(AuditLog(claim_id=claim.id, event_type="claim_submitted", event_data={"customer_name": claim.customer_name}, actor="customer", created_at=submitted_at))

            extraction_data = sample["extraction"]
            if extraction_data:
                extracted = extraction_data["extracted_data"]
                missing = compute_missing_fields(claim, extracted)
                extracted_at = submitted_at + timedelta(minutes=1)
                db.add(ClaimExtraction(claim_id=claim.id, missing_fields=missing, extraction_raw=None, created_at=extracted_at, **extraction_data))
                db.add(AuditLog(claim_id=claim.id, event_type="ai_extraction_completed", event_data={"missing_fields": missing, "autofilled_fields": [], "rerun": False}, actor="ai_agent", created_at=extracted_at))

                score, signals = calculate_risk(RiskInputs(
                    declared_amount=float(claim.estimated_amount) if claim.estimated_amount is not None else None,
                    extracted_amount=extracted.get("estimated_amount"),
                    incident_date=claim.incident_date,
                    missing_fields=missing,
                    low_confidence_fields=low_confidence_fields(extracted, extraction_data["confidence_scores"]),
                    prior_claims_count=0,
                    today=date.today(),
                ))
                level = get_risk_level(score)
                action = get_recommended_action(level)
                explanation = f"Risk score: {score}/100 ({level}). "
                explanation += ("Signals: " + "; ".join(signals) + ". ") if signals else "No risk signals detected. "
                explanation += f"Recommended action: {action}"
                assessed_at = submitted_at + timedelta(minutes=2)
                db.add(RiskAssessment(claim_id=claim.id, risk_score=score, risk_level=level, signals=signals, explanation=explanation, recommended_action=action, created_at=assessed_at))
                db.add(AuditLog(claim_id=claim.id, event_type="risk_assessed", event_data={"score": score, "level": level, "rerun": False}, actor="system", created_at=assessed_at))
                claim.risk_level = level

            for i, conv in enumerate(sample["conversations"]):
                db.add(Conversation(claim_id=claim.id, created_at=submitted_at + timedelta(minutes=3 + i * 30), **conv))

            for act in sample["actions"]:
                acted_at = submitted_at + timedelta(hours=act["hours_after"])
                db.add(ClaimAction(claim_id=claim.id, action=act["action"], performed_by=act["performed_by"], notes=act["notes"], created_at=acted_at))
                db.add(AuditLog(claim_id=claim.id, event_type=f"claim_{act['action']}", event_data={"performed_by": act["performed_by"], "notes": act["notes"]}, actor="ops_agent", created_at=acted_at))

            print(f"  {claim.customer_name:<16} {claim.status:<14} risk={claim.risk_level}")

        await db.commit()
        print(f"Seeded {len(SAMPLE_CLAIMS)} claims successfully.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--reset", action="store_true", help="drop all tables before seeding (destroys data)")
    asyncio.run(seed(parser.parse_args().reset))
