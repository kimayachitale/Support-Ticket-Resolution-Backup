from google import genai

client = genai.Client(api_key="GOOGLE_API_KEY")

VALID_PRIORITIES = ["Critical", "High", "Medium", "Low"]


def detect_priority(complaint):

    prompt = f"""You are a railway complaint priority detection AI.

Analyze the complaint and assign a priority level.

Priority Levels:
- Critical
- High
- Medium
- Low

Rules:
Critical - Medical emergency, safety issue, accident
High - Long train delay, refund issue, serious complaint
Medium - Normal complaints
Low - General queries

Complaint:
{complaint}

Return ONLY the priority level name (Critical, High, Medium, or Low). No explanation, no punctuation."""

    priority = "Medium"

    try:
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt,
            config={
                "thinking_config": {"thinking_budget": 0},
                "max_output_tokens": 50,
                "temperature": 0.2
            }
        )
        raw_priority = response.text.strip()

        # Sanitize to match strictly one of the allowed priority levels
        for valid_p in VALID_PRIORITIES:
            if valid_p.lower() in raw_priority.lower():
                priority = valid_p
                break
        else:
            priority = "Medium"

    except Exception as e:
        print(f"[PRIORITY ERROR] {e}")
        priority = "Medium"

    return priority
