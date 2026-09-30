import json
import re
from google import genai

client = genai.Client(api_key="GOOGLE_API_KEY")

CATEGORY_QUESTIONS = {
    "Train Delay": [
        {
            "question": "Was your train delayed by more than 3 hours at your boarding station?",
            "options": ["Yes (>3 hours)", "No (<3 hours)", "Not sure", "Other"]
        },
        {
            "question": "Did you undertake the journey or cancel before departure?",
            "options": ["Did not travel", "Completed journey despite delay", "Cancelled ticket beforehand", "Other"]
        }
    ],
    "Refund Issue": [
        {
            "question": "When was the ticket cancelled relative to train departure?",
            "options": ["More than 48 hrs before", "Between 12-48 hrs before", "Less than 12 hrs / After chart", "Other"]
        },
        {
            "question": "What is the refund problem you are facing?",
            "options": ["Refund deducted but not credited", "Deduction amount too high", "TDR rejected", "Other"]
        }
    ],
    "Ticket Cancellation": [
        {
            "question": "Did the railway cancel the train or did you cancel voluntarily?",
            "options": ["Train cancelled by Railways", "Cancelled voluntarily before chart", "Cancelled after chart prep", "Other"]
        },
        {
            "question": "Was your ticket fully confirmed or waitlisted/RAC?",
            "options": ["Confirmed", "RAC", "Waitlisted (WL)", "Other"]
        }
    ],
    "Booking Issue": [
        {
            "question": "Was the payment debited from your account without ticket generation?",
            "options": ["Yes, amount debited", "No, payment failed immediately", "Double payment deducted", "Other"]
        },
        {
            "question": "Have 72 hours passed since the transaction attempt?",
            "options": ["Yes, more than 72 hours", "No, less than 72 hours", "Transaction just happened", "Other"]
        }
    ]
}

DEFAULT_QUESTIONS = [
    {
        "question": "Did this issue prevent you from completing your scheduled journey?",
        "options": ["Yes, could not travel", "Completed journey with difficulty", "Cancelled in advance", "Other"]
    },
    {
        "question": "Have you already filed a TDR (Ticket Deposit Receipt) or complaint on RailMadad?",
        "options": ["Yes, filed TDR", "Reported on RailMadad", "No, this is my first report", "Other"]
    }
]


def get_clarifying_questions(complaint, category):
    """
    Generates 2-3 category-specific clarifying questions with multiple-choice options + 'Other'.
    """
    prompt = f"""You are a railway support assistant. Based on this complaint, generate exactly 2 to 3 clarifying questions. Each question must have 3 short answer options plus "Other".

Complaint: "{complaint}"
Category: {category}

Rules:
- Questions should determine refund eligibility under Indian Railways rules
- Options must be short (1-5 words each)
- Always include "Other" as the last option

Respond ONLY in raw JSON (no markdown, no backticks):
{{
  "questions": [
    {{
      "question": "Was the delay more than 3 hours?",
      "options": ["Yes", "No", "Not sure", "Other"]
    }},
    {{
      "question": "Did you undertake the journey?",
      "options": ["Travelled", "Did not travel", "Partially travelled", "Other"]
    }}
  ]
}}"""

    try:
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt,
            config={
                "thinking_config": {"thinking_budget": 0},
                "max_output_tokens": 350,
                "temperature": 0.2
            }
        )

        text = response.text.strip()
        text = re.sub(r"^```json\s*|^```\s*|```$", "", text, flags=re.MULTILINE).strip()
        data = json.loads(text)
        questions = data.get("questions", [])

        if questions:
            for q in questions:
                opts = q.get("options", [])
                if "Other" not in opts:
                    opts.append("Other")
                q["options"] = opts
            return questions

    except Exception as e:
        print(f"[CLARIFIER INFO] Using tailored category questions: {e}")

    # Fallback to category-curated railway questions
    return CATEGORY_QUESTIONS.get(category, DEFAULT_QUESTIONS)
