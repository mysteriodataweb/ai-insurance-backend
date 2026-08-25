"""
Seed script for AI Insurance Operations Platform.
Populates the database with realistic sample claims and pre-computed AI data.
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime, date, timedelta
from decimal import Decimal

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import async_session, engine, Base
from app.models import Claim, ClaimExtraction, Conversation, RiskAssessment, ClaimAction, AuditLog


SAMPLE_CLAIMS = [
    {
        "customer_name": "Ahmed Benali",
        "customer_email": "ahmed.benali@email.com",
        "policy_number": "POL-2024-001",
        "raw_description": "I had a car accident yesterday in Casablanca. Another vehicle hit my car at an intersection. The front bumper and hood are damaged. I estimate the repair will cost around $3,000. I have the other driver's license plate number and photos of the damage.",
        "incident_type": "Car accident",
        "incident_date": date(2026, 8, 24),
        "incident_location": "Casablanca",
        "estimated_amount": Decimal("3000.00"),
        "status": "under_review",
        "risk_level": "low",
        "extraction": {
            "extracted_data": {
                "incident_type": "Car accident",
                "incident_date": "2026-08-24",
                "incident_location": "Casablanca",
                "estimated_amount": 3000,
                "damage_description": "Front bumper and hood damaged",
                "other_party_info": "Other driver's license plate available",
                "policy_number": "POL-2024-001",
            },
            "missing_fields": [],
            "confidence_scores": {
                "incident_type": 0.95,
                "incident_date": 0.90,
                "incident_location": 0.95,
                "estimated_amount": 0.70,
                "damage_description": 0.85,
                "other_party_info": 0.80,
                "policy_number": 1.0,
            },
        },
        "risk": {
            "risk_score": 15,
            "risk_level": "low",
            "signals": [],
            "explanation": "Risk score: 15/100 (low). Standard car accident with consistent information, supporting documentation available. Recommended action: Standard processing. No manual review required.",
            "recommended_action": "Standard processing. No manual review required.",
        },
        "conversations": [
            {"role": "agent", "message": "Thank you for submitting your claim. I can see you had a car accident in Casablanca. Could you please provide photos of the damage to support your claim?", "message_type": "info_request"},
            {"role": "customer", "message": "Yes, I have photos. I will upload them now. The front of the car is quite badly damaged.", "message_type": "answer"},
        ],
        "action": {"action": "approved", "performed_by": "ops_agent", "notes": "All documentation received. Standard processing."},
    },
    {
        "customer_name": "Fatima Zahra",
        "customer_email": "fatima.zahra@email.com",
        "policy_number": None,
        "raw_description": "My apartment was flooded last week due to a pipe burst in the building. The living room and kitchen are damaged. Furniture worth $5,000 was destroyed. Water damage to the walls and floor.",
        "incident_type": "Water damage",
        "incident_date": date(2026, 8, 18),
        "incident_location": "Rabat",
        "estimated_amount": Decimal("5000.00"),
        "status": "follow_up",
        "risk_level": "medium",
        "extraction": {
            "extracted_data": {
                "incident_type": "Water damage",
                "incident_date": "2026-08-18",
                "incident_location": "Rabat",
                "estimated_amount": 5000,
                "damage_description": "Living room and kitchen flooded. Furniture destroyed. Water damage to walls and floor.",
                "other_party_info": None,
                "policy_number": None,
            },
            "missing_fields": ["policy_number", "other_party_info", "photos_of_damage"],
            "confidence_scores": {
                "incident_type": 0.90,
                "incident_date": 0.75,
                "incident_location": 0.85,
                "estimated_amount": 0.60,
                "damage_description": 0.80,
                "other_party_info": 0.0,
                "policy_number": 0.0,
            },
        },
        "risk": {
            "risk_score": 45,
            "risk_level": "medium",
            "signals": [
                "Missing supporting documentation",
                "Missing policy number",
            ],
            "explanation": "Risk score: 45/100 (medium). Missing policy number and supporting documentation. Recommended action: Manual review recommended. Check signals before approving.",
            "recommended_action": "Manual review recommended. Check signals before approving.",
        },
        "conversations": [
            {"role": "agent", "message": "I understand your apartment was flooded. To process your claim, I need a few more details. Do you have your policy number?", "message_type": "question"},
            {"role": "agent", "message": "Could you also provide photos of the water damage to support your claim?", "message_type": "question"},
        ],
        "action": None,
    },
    {
        "customer_name": "Youssef Alami",
        "customer_email": "youssef@email.com",
        "policy_number": "POL-2024-003",
        "raw_description": "I need to file a claim for my stolen laptop. It was taken from my hotel room in Marrakech while I was at dinner. The laptop is a MacBook Pro worth $2,500. I have a police report.",
        "incident_type": "Theft",
        "incident_date": date(2026, 8, 22),
        "incident_location": "Marrakech",
        "estimated_amount": Decimal("2500.00"),
        "status": "under_review",
        "risk_level": "medium",
        "extraction": {
            "extracted_data": {
                "incident_type": "Theft",
                "incident_date": "2026-08-22",
                "incident_location": "Marrakech",
                "estimated_amount": 2500,
                "damage_description": "MacBook Pro stolen from hotel room",
                "other_party_info": "Police report available",
                "policy_number": "POL-2024-003",
            },
            "missing_fields": [],
            "confidence_scores": {
                "incident_type": 0.90,
                "incident_date": 0.85,
                "incident_location": 0.90,
                "estimated_amount": 0.75,
                "damage_description": 0.80,
                "other_party_info": 0.70,
                "policy_number": 1.0,
            },
        },
        "risk": {
            "risk_score": 35,
            "risk_level": "medium",
            "signals": [
                "Theft claims require additional verification",
            ],
            "explanation": "Risk score: 35/100 (medium). Theft claim with police report. Standard verification required. Recommended action: Manual review recommended.",
            "recommended_action": "Manual review recommended.",
        },
        "conversations": [
            {"role": "agent", "message": "I see you filed a theft claim. Do you have a copy of the police report?", "message_type": "question"},
            {"role": "customer", "message": "Yes, I have the police report. The report number is MRK-2026-4521.", "message_type": "answer"},
        ],
        "action": None,
    },
    {
        "customer_name": "Sara Idrissi",
        "customer_email": "sara.idrissi@email.com",
        "policy_number": "POL-2024-004",
        "raw_description": "There was a fire in my shop last night. The fire started from an electrical fault. The entire inventory was destroyed. I estimate the total loss at $15,000. The fire brigade came and confirmed it was an electrical issue.",
        "incident_type": "Fire",
        "incident_date": date(2026, 8, 20),
        "incident_location": "Tangier",
        "estimated_amount": Decimal("15000.00"),
        "status": "under_review",
        "risk_level": "high",
        "extraction": {
            "extracted_data": {
                "incident_type": "Fire",
                "incident_date": "2026-08-20",
                "incident_location": "Tangier",
                "estimated_amount": 15000,
                "damage_description": "Entire inventory destroyed by fire. Electrical fault confirmed by fire brigade.",
                "other_party_info": "Fire brigade report available",
                "policy_number": "POL-2024-004",
            },
            "missing_fields": [],
            "confidence_scores": {
                "incident_type": 0.95,
                "incident_date": 0.90,
                "incident_location": 0.95,
                "estimated_amount": 0.80,
                "damage_description": 0.90,
                "other_party_info": 0.85,
                "policy_number": 1.0,
            },
        },
        "risk": {
            "risk_score": 78,
            "risk_level": "high",
            "signals": [
                "Claim amount significantly above average ($15,000+)",
                "Fire damage requires investigation",
            ],
            "explanation": "Risk score: 78/100 (high). High-value fire claim with significant inventory loss. Recommended action: Manual investigation required. Multiple risk signals detected.",
            "recommended_action": "Manual investigation required. Multiple risk signals detected.",
        },
        "conversations": [
            {"role": "agent", "message": "I'm sorry to hear about the fire in your shop. Could you provide the fire brigade report number?", "message_type": "question"},
            {"role": "customer", "message": "The fire brigade report number is TNG-FB-2026-089. They confirmed it was an electrical fault in the wiring.", "message_type": "answer"},
        ],
        "action": {"action": "escalated", "performed_by": "ops_agent", "notes": "High-value fire claim escalated for investigation."},
    },
    {
        "customer_name": "Omar Tazi",
        "customer_email": "omar.tazi@email.com",
        "policy_number": None,
        "raw_description": "I was involved in a minor car accident. My car was parked and someone hit it and drove away. I found a dent on the rear bumper. Repair should be around $800.",
        "incident_type": "Car accident",
        "incident_date": date(2026, 8, 23),
        "incident_location": "Fez",
        "estimated_amount": Decimal("800.00"),
        "status": "submitted",
        "risk_level": "unrated",
        "extraction": None,
        "risk": None,
        "conversations": [],
        "action": None,
    },
]


async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as db:
        for i, claim_data in enumerate(SAMPLE_CLAIMS):
            extraction_data = claim_data.pop("extraction")
            risk_data = claim_data.pop("risk")
            conversations_data = claim_data.pop("conversations")
            action_data = claim_data.pop("action")

            claim = Claim(**claim_data)
            db.add(claim)
            await db.flush()

            if extraction_data:
                extraction = ClaimExtraction(claim_id=claim.id, **extraction_data)
                db.add(extraction)

            if risk_data:
                risk = RiskAssessment(claim_id=claim.id, **risk_data)
                db.add(risk)

            for conv in conversations_data:
                conversation = Conversation(claim_id=claim.id, **conv)
                db.add(conversation)

            if action_data:
                action = ClaimAction(claim_id=claim.id, **action_data)
                db.add(action)

            # Audit logs
            db.add(AuditLog(claim_id=claim.id, event_type="claim_submitted", event_data={"customer_name": claim.customer_name}, actor="customer"))
            if extraction_data:
                db.add(AuditLog(claim_id=claim.id, event_type="ai_extraction_completed", event_data={"status": "success"}, actor="ai_agent"))
            if risk_data:
                db.add(AuditLog(claim_id=claim.id, event_type="risk_assessed", event_data={"score": risk_data["risk_score"], "level": risk_data["risk_level"]}, actor="system"))
            if action_data:
                db.add(AuditLog(claim_id=claim.id, event_type=f"claim_{action_data['action']}", event_data={"performed_by": action_data["performed_by"]}, actor="ops_agent"))

        await db.commit()
        print(f"Seeded {len(SAMPLE_CLAIMS)} claims successfully.")


if __name__ == "__main__":
    asyncio.run(seed())
