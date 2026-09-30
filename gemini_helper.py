from google import genai
import json
import re

client = genai.Client(api_key="GOOGLE_API_KEY")


def _generate_with_fallback(prompt, max_tokens=150, temperature=0.3):
    """Helper to try gemini-3.6-flash first, falling back to gemini-3.5-flash."""
    for model in ["gemini-3.6-flash", "gemini-3.5-flash"]:
        try:
            res = client.models.generate_content(
                model=model,
                contents=prompt,
                config={
                    "thinking_config": {"thinking_budget": 0},
                    "max_output_tokens": max_tokens,
                    "temperature": temperature
                }
            )
            if res and res.text:
                return res.text.strip()
        except Exception:
            continue
    return None


def generate_reply(ticket, category, refund_result, answers=None):
    answers_context = f"User Clarifications: {answers}" if answers else ""

    prompt = f"""You are a railway customer support assistant. Write a VERY SHORT reply (max 3 sentences, under 80 words). Be polite but direct.

Complaint: {ticket}
Category: {category}
Refund Info: {refund_result}
{answers_context}

Rules:
- Do NOT write 'Subject:' or 'Dear Passenger' or 'Warm regards'
- Do NOT write formal email format
- Just give the key answer: what happened, what they can do, done.
- Use plain, friendly language.

Reply:"""

    reply = _generate_with_fallback(prompt, max_tokens=150, temperature=0.4)
    if reply:
        return reply

    return (
        f"Your complaint regarding {category} has been reviewed. "
        f"Status: {refund_result.get('verdict', 'Under review')}. "
        "Please follow the provided instructions or contact helpline 139 for assistance."
    )


def make_final_decision(complaint, category, answers, pnr_data=None):
    """
    Evaluates complaint + clarifying answers + PNR data to reach a final refund decision.
    """
    fare = pnr_data.get("fare", 1500) if pnr_data else 1500
    status = pnr_data.get("status", "Unknown") if pnr_data else "Unknown"

    prompt = f"""You are a railway refund decision engine.

Complaint: {complaint}
Category: {category}
User's Clarifications: {answers}
Ticket Fare: {fare} (Ticket Status: {status})

Based on Indian Railways rules, decide:
- If user cancelled before journey -> "Refund Eligible", amount {round(fare * 0.8)}
- If train delayed > 3 hours and user did not travel -> "Refund Eligible", amount {fare}
- If train delayed > 3 hours and user traveled -> "Partial Refund", amount {round(fare * 0.5)}
- If train cancelled by railways -> "Refund Eligible", amount {fare}
- If journey completed normally -> "No Refund", amount 0
- If unclear or general complaint -> "Needs Review", amount 0

Respond ONLY in raw JSON:
{{
  "verdict": "Refund Eligible",
  "amount": {fare},
  "advice": "1-2 sentence next step for the user"
}}

verdict MUST be one of: "Refund Eligible", "Partial Refund", "No Refund", "Needs Review"."""

    raw = _generate_with_fallback(prompt, max_tokens=250, temperature=0.2)

    if raw:
        try:
            cleaned = re.sub(r"^```json\s*|^```\s*|```$", "", raw, flags=re.MULTILINE).strip()
            data = json.loads(cleaned)
            return {
                "verdict": data.get("verdict", "Needs Review"),
                "amount": int(data.get("amount", 0)),
                "advice": data.get("advice", "Please visit your nearest railway counter or file a TDR online.")
            }
        except Exception:
            pass

    # Safe deterministic fallback based on answers
    answers_str = " ".join([str(a) for a in answers]).lower()
    if "did not travel" in answers_str or ">3 hours" in answers_str or "cancelled" in answers_str:
        return {
            "verdict": "Refund Eligible",
            "amount": round(fare * 0.8),
            "advice": "Eligible for refund under railway delay/cancellation policy. File a TDR online within 72 hours."
        }
    elif "completed" in answers_str or "travelled" in answers_str:
        return {
            "verdict": "No Refund",
            "amount": 0,
            "advice": "Journey was completed. If you faced service deficiency, please lodge a grievance via RailMadad."
        }
    else:
        return {
            "verdict": "Needs Review",
            "amount": 0,
            "advice": "Your request requires manual verification. Please visit your departure station or call helpline 139."
        }
