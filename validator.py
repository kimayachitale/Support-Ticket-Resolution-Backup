import os
import json
import re
from google import genai

# Reuse same client setup as the rest of the project
client = genai.Client(api_key="GOOGLE_API_KEY")


def is_valid_complaint(complaint_text):
    """
    Validates whether the given text is a legitimate railway-related complaint.

    Returns:
        { "is_valid": True/False, "reason": "short explanation" }

    Safe fallback: returns is_valid=True if Gemini errors out,
    so genuine complaints are never blocked by technical failures.
    """

    # Quick length check — no API call needed
    if not complaint_text or len(complaint_text.strip()) < 10:
        return {
            "is_valid": False,
            "reason": "Complaint is too short to be meaningful."
        }

    prompt = f"""You are a strict validator for an Indian Railway complaint system.
Determine if the following user input is a LEGITIMATE railway-related complaint.

VALID topics: train delays, refunds, cancellations, PNR, booking, seats,
food, staff, lost items, safety, cleanliness, AC, coach issues.

INVALID: gibberish, random sentences, unrelated questions (weather,
politics, general knowledge), abuse, spam, ads, or too short/unclear text.

User Input: "{complaint_text}"

Respond ONLY with raw JSON (no markdown, no backticks):
{{"is_valid": true or false, "reason": "one-line explanation"}}
"""

    try:
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt,
            config={
                "thinking_config": {"thinking_budget": 0},
                "max_output_tokens": 100,
                "temperature": 0.1
            }
        )

        text = response.text.strip()

        # Strip markdown fences if Gemini wraps the response
        text = re.sub(r"^```json\s*|^```\s*|```$", "", text, flags=re.MULTILINE).strip()

        result = json.loads(text)

        print(f"[VALIDATOR] '{complaint_text[:60]}' => is_valid={result.get('is_valid')} | {result.get('reason')}")

        return {
            "is_valid": bool(result.get("is_valid", True)),
            "reason": result.get("reason", "Validation completed.")
        }

    except Exception as e:
        print(f"[VALIDATOR ERROR] {e}")
        # Safe fallback — never block real complaints due to API errors
        return {
            "is_valid": True,
            "reason": "Validation skipped due to error."
        }
