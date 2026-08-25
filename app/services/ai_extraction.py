import json
from openai import AsyncOpenAI
from app.config import settings

client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

EXTRACTION_PROMPT = """You are an insurance claim analysis assistant.

Given the following customer claim description, extract structured information.

Return a JSON object with exactly this structure:
{
  "extracted_data": {
    "incident_type": "string or null",
    "incident_date": "YYYY-MM-DD or null",
    "incident_location": "string or null",
    "estimated_amount": "number or null",
    "damage_description": "string or null",
    "other_party_info": "string or null",
    "policy_number": "string or null"
  },
  "missing_fields": ["list of required fields that are missing or unclear"],
  "confidence_scores": {
    "incident_type": 0.0 to 1.0,
    "incident_date": 0.0 to 1.0,
    "incident_location": 0.0 to 1.0,
    "estimated_amount": 0.0 to 1.0,
    "damage_description": 0.0 to 1.0,
    "other_party_info": 0.0 to 1.0,
    "policy_number": 0.0 to 1.0
  }
}

Rules:
- Only extract information that is explicitly stated or clearly implied
- Set confidence to 0.0 for information you are uncertain about
- Never invent information
- If the date is relative (yesterday, last week), calculate the actual date based on today: {today}

Customer claim:
\"\"\"{description}\"\"\"

Respond ONLY with valid JSON, no markdown, no explanation."""


async def extract_claim_info(description: str) -> dict:
    from datetime import date
    today = date.today().isoformat()
    prompt = EXTRACTION_PROMPT.format(description=description, today=today)

    response = await client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        response_format={"type": "json_object"},
    )

    return json.loads(response.choices[0].message.content)
