import json
import re
from google import genai

client = genai.Client(api_key="GOOGLE_API_KEY")

VALID_CATEGORIES = {
    "Refund Issue",
    "Ticket Cancellation",
    "Train Delay",
    "Booking Issue",
    "Seat Complaint",
    "Food Complaint",
    "Staff Complaint",
    "Lost Item",
    "Cleanliness",
    "Safety Issue",
    "Other",
}

# Fallbacks tailored by category so questions are never generic
CATEGORY_FALLBACKS = {
    "Seat Complaint": {
        "priority": "Medium",
        "questions": [
            {
                "question": "Was the seat blocked when you boarded?",
                "options": ["Yes at boarding", "Blocked mid-journey", "Entire journey", "Other"],
            },
            {
                "question": "Did you report it to the TTE/coach attendant?",
                "options": ["Yes, they helped", "Yes, no action taken", "No", "Other"],
            },
            {
                "question": "Did you have to stand or shift seats?",
                "options": ["Stood entire journey", "Shifted to another seat", "Adjusted somehow", "Other"],
            },
        ],
    },
    "Train Delay": {
        "priority": "High",
        "questions": [
            {
                "question": "How long was the delay?",
                "options": ["Under 1 hour", "1-3 hours", "Over 3 hours", "Other"],
            },
            {
                "question": "Did you complete the journey?",
                "options": ["Yes, delayed", "Cancelled, didn't travel", "Missed connection", "Other"],
            },
            {
                "question": "Have you filed a TDR?",
                "options": ["Yes, filed TDR", "Reported on RailMadad", "No, first report", "Other"],
            },
        ],
    },
    "Refund Issue": {
        "priority": "High",
        "questions": [
            {
                "question": "Was your ticket cancelled?",
                "options": ["Yes, by me", "Yes, by railways", "Not cancelled yet", "Other"],
            },
            {
                "question": "Was the journey already completed?",
                "options": ["Not started", "Partially completed", "Fully completed", "Other"],
            },
            {
                "question": "How long since cancellation?",
                "options": ["Under 24 hours", "1-3 days", "Over 3 days", "Other"],
            },
        ],
    },
    "Food Complaint": {
        "priority": "Medium",
        "questions": [
            {
                "question": "What was the issue?",
                "options": ["Stale/expired", "Overpriced", "Poor quality", "Other"],
            },
            {
                "question": "Did you report to pantry staff?",
                "options": ["Yes, ignored", "Yes, resolved", "No", "Other"],
            },
            {
                "question": "Do you want a refund or action?",
                "options": ["Refund", "Action on vendor", "Just feedback", "Other"],
            },
        ],
    },
    "Ticket Cancellation": {
        "priority": "High",
        "questions": [
            {
                "question": "Who cancelled the ticket?",
                "options": ["I cancelled online", "Railways cancelled the train", "Waitlist auto-cancelled", "Other"],
            },
            {
                "question": "When was it cancelled relative to departure?",
                "options": ["More than 48 hours before", "Within 48 hours", "After chart prepared", "Other"],
            },
            {
                "question": "Have you received any refund yet?",
                "options": ["Full refund credited", "Partial / deducted", "Nothing credited", "Other"],
            },
        ],
    },
    "Staff Complaint": {
        "priority": "High",
        "questions": [
            {
                "question": "Who was involved?",
                "options": ["TTE / ticket checker", "Coach attendant", "Station staff", "Other"],
            },
            {
                "question": "What happened?",
                "options": ["Rude / unhelpful behaviour", "Asked for extra money", "Did not help with a problem", "Other"],
            },
            {
                "question": "Did you note name, ID, or coach number?",
                "options": ["Yes, I have details", "Partial details", "No details", "Other"],
            },
        ],
    },
    "Lost Item": {
        "priority": "High",
        "questions": [
            {
                "question": "Where was the item last seen?",
                "options": ["On my berth/seat", "In the coach aisle / toilet", "At the station", "Other"],
            },
            {
                "question": "Have you reported it to the TTE or RPF?",
                "options": ["Yes, TTE informed", "Yes, RPF / GRP complaint", "Not yet", "Other"],
            },
            {
                "question": "What item did you lose?",
                "options": ["Bag / luggage", "Phone / electronics", "Documents / wallet", "Other"],
            },
        ],
    },
}

GENERIC_QUESTION_MARKERS = (
    "disrupt your scheduled train journey",
    "filed a complaint on railmadad",
    "what primary outcome are you requesting",
    "please describe your issue",
    "select the option that best describes",
)

CATEGORY_HINTS = {
    "Seat Complaint": ("seat", "berth", "blocked", "occupied", "tte", "stand", "coach", "ac "),
    "Train Delay": ("delay", "late", "hour", "tdr", "missed connection", "running"),
    "Refund Issue": ("refund", "cancel", "credited", "tdr", "journey"),
    "Food Complaint": ("food", "meal", "stale", "pantry", "vendor", "quality", "mrp"),
    "Ticket Cancellation": ("cancel", "refund", "waitlist", "chart"),
    "Staff Complaint": ("staff", "tte", "attendant", "rude", "behaviour"),
    "Lost Item": ("lost", "bag", "luggage", "phone", "wallet", "rpf"),
}


def _infer_from_keywords(complaint_text):
    t = complaint_text.lower()
    if any(k in t for k in ("refund", "money back", "not credited", "amount not")):
        return "Refund Issue", "High"
    if any(k in t for k in ("delay", "delayed", "late by", "running late")):
        return "Train Delay", "High"
    if any(k in t for k in ("food", "meal", "stale", "pantry", "catering", "unhygienic")):
        return "Food Complaint", "Medium"
    if any(k in t for k in ("seat", "berth", "blocked", "occupied", "ac not", "air condition")):
        return "Seat Complaint", "Medium"
    if any(k in t for k in ("cancel", "cancellation")):
        return "Ticket Cancellation", "High"
    if any(k in t for k in ("staff", "tte", "rude", "attendant", "behaviour", "behavior")):
        return "Staff Complaint", "High"
    if any(k in t for k in ("lost", "missing bag", "luggage missing", "theft")):
        return "Lost Item", "High"
    if any(k in t for k in ("dirty", "toilet", "cleanliness", "garbage")):
        return "Cleanliness", "Medium"
    if any(k in t for k in ("safety", "harass", "medical emergency")):
        return "Safety Issue", "Critical"
    if any(k in t for k in ("booking", "irctc", "pnr not", "failed payment")):
        return "Booking Issue", "Medium"
    return None, None


def _get_rule_fallback(complaint_text):
    category, priority = _infer_from_keywords(complaint_text)
    if category and category in CATEGORY_FALLBACKS:
        data = CATEGORY_FALLBACKS[category]
        return {
            "is_valid": True,
            "reason": "",
            "category": category,
            "priority": priority or data["priority"],
            "questions": data["questions"],
        }
    return {
        "is_valid": True,
        "reason": "Analyzed via fallback rules",
        "category": category or "Other",
        "priority": priority or "Medium",
        "questions": [
            {
                "question": "Did this issue disrupt your scheduled train journey?",
                "options": ["Yes, could not travel", "Completed journey with difficulty", "Cancelled in advance", "Other"],
            },
            {
                "question": "Have you already filed a complaint on RailMadad or station counter?",
                "options": ["Yes, filed RailMadad", "Reported to station master", "No, first report", "Other"],
            },
            {
                "question": "What primary outcome are you requesting?",
                "options": ["Fare refund", "Official investigation", "Assistance for onward travel", "Other"],
            },
        ],
    }


def _extract_json(raw_text):
    if not raw_text:
        raise ValueError("Empty Gemini response")
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw_text.strip(), flags=re.IGNORECASE | re.MULTILINE)
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object found in Gemini response")
    return json.loads(cleaned[start : end + 1])


def _normalize_questions(questions):
    normalized = []
    for q in questions or []:
        if isinstance(q, str):
            q = {"question": q, "options": []}
        text = (q.get("question") or "").strip()
        if not text:
            continue
        opts = [str(o).strip() for o in q.get("options", []) if str(o).strip()]
        if "Other" not in opts:
            opts.append("Other")
        while len(opts) < 4:
            opts.insert(-1, "Not sure")
        normalized.append({"question": text, "options": opts[:4] if "Other" in opts[:4] else opts[:3] + ["Other"]})
    return normalized


def _questions_match_category(questions, category):
    if not questions or len(questions) < 3:
        return False
    blob = " ".join(q.get("question", "") for q in questions).lower()
    if any(marker in blob for marker in GENERIC_QUESTION_MARKERS):
        return False
    hints = CATEGORY_HINTS.get(category)
    if not hints:
        return True
    return sum(1 for hint in hints if hint in blob) >= 1


def _finalize_analysis(data, complaint_text, pnr_number, source="gemini"):
    inferred, inferred_priority = _infer_from_keywords(complaint_text)
    category = (data.get("category") or "").strip()
    if category not in VALID_CATEGORIES:
        category = inferred or "Other"
    if category == "Other" and inferred:
        print(f"[UNIFIED ANALYZER] Overriding category Other -> {inferred} from keywords")
        category = inferred
        if not data.get("priority"):
            data["priority"] = inferred_priority

    questions = _normalize_questions(data.get("questions"))
    if not _questions_match_category(questions, category):
        fallback = CATEGORY_FALLBACKS.get(category)
        if fallback:
            print(f"[UNIFIED ANALYZER] Replacing generic/empty questions with {category} templates ({source})")
            questions = fallback["questions"]
            data["priority"] = data.get("priority") or fallback["priority"]

    data["is_valid"] = bool(data.get("is_valid", True))
    data["reason"] = data.get("reason") or ""
    data["category"] = category
    data["priority"] = data.get("priority") or inferred_priority or "Medium"
    data["questions"] = questions
    data["pnr_number"] = pnr_number
    print(f"[UNIFIED ANALYZER OK] source={source} category={data['category']} priority={data['priority']}")
    for i, q in enumerate(data["questions"], 1):
        print(f"  Q{i}: {q.get('question')}")
    return data


def analyze_complaint(complaint_text):
    """
    Unified analyzer that executes:
      1. Validation
      2. Precise Category Classification
      3. Priority Detection
      4. Targeted, category-specific clarifying questions (3 options + Other)
    All in a single, fast call.
    """
    if not complaint_text or len(complaint_text.strip()) < 10:
        return {
            "is_valid": False,
            "reason": "Complaint is too short to be meaningful.",
            "category": None,
            "priority": None,
            "questions": [],
            "pnr_number": "Not Provided",
        }

    pnr_match = re.search(r"\b\d{10}\b", complaint_text)
    pnr_number = pnr_match.group() if pnr_match else "Not Provided"

    prompt = f"""You are an expert Indian Railway complaint analyzer.

Complaint: "{complaint_text}"

STEP 1 — VALIDATION:
Is this a legitimate railway complaint? Valid topics: train delays,
refunds, cancellations, PNR issues, seat problems, blocked seats,
food quality, staff behavior, lost items, safety, cleanliness, AC.
Invalid: gibberish, weather, politics, general knowledge, abuse, spam.

If INVALID, return:
{{"is_valid": false, "reason": "short reason", "category": null, "priority": null, "questions": []}}

STEP 2 — CATEGORY (be precise, do NOT default to "Other" unless truly unclear):
Choose ONE: "Refund Issue", "Ticket Cancellation", "Train Delay",
"Booking Issue", "Seat Complaint", "Food Complaint", "Staff Complaint",
"Lost Item", "Cleanliness", "Safety Issue", "Other"

Examples:
- "seat is blocked by another person" → "Seat Complaint"
- "train delayed by 5 hours" → "Train Delay"
- "want refund for cancelled ticket" → "Refund Issue"
- "AC not working" → "Seat Complaint"
- "stale food" → "Food Complaint"

STEP 3 — PRIORITY:
Critical (safety/medical), High (delays, refunds, serious issues),
Medium (normal complaints), Low (general feedback).

STEP 4 — QUESTIONS (MOST IMPORTANT):
Generate exactly 3 clarifying questions SPECIFIC to this complaint
and category. Do NOT use generic template questions.
Do NOT copy the examples below word-for-word. Mention details from THIS complaint.

Each question MUST:
- Be tailored to the specific complaint (not reused across categories)
- Have 3 options + "Other"
- Help determine refund eligibility or next action

Examples by category (inspiration only — invent new wording for THIS complaint):
- Seat Complaint ("seat blocked"):
  Q1: "Was the seat blocked when you boarded?" → ["Yes at boarding", "Blocked mid-journey", "Entire journey", "Other"]
  Q2: "Did you report it to the TTE/coach attendant?" → ["Yes, they helped", "Yes, no action taken", "No", "Other"]
  Q3: "Did you have to stand or shift seats?" → ["Stood entire journey", "Shifted to another seat", "Adjusted somehow", "Other"]

- Train Delay:
  Q1: "How long was the delay?" → ["Under 1 hour", "1-3 hours", "Over 3 hours", "Other"]
  Q2: "Did you complete the journey?" → ["Yes, delayed", "Cancelled, didn't travel", "Missed connection", "Other"]
  Q3: "Have you filed a TDR?" → ["Yes, filed TDR", "Reported on RailMadad", "No, first report", "Other"]

- Refund Issue:
  Q1: "Was your ticket cancelled?" → ["Yes, by me", "Yes, by railways", "Not cancelled yet", "Other"]
  Q2: "Was the journey already completed?" → ["Not started", "Partially completed", "Fully completed", "Other"]
  Q3: "How long since cancellation?" → ["Under 24 hours", "1-3 days", "Over 3 days", "Other"]

- Food Complaint:
  Q1: "What was the issue?" → ["Stale/expired", "Overpriced", "Poor quality", "Other"]
  Q2: "Did you report to pantry staff?" → ["Yes, ignored", "Yes, resolved", "No", "Other"]
  Q3: "Do you want a refund or action?" → ["Refund", "Action on vendor", "Just feedback", "Other"]

Now generate 3 questions SPECIFIC to THIS complaint: "{complaint_text}"
using the category you chose in STEP 2.

Return ONLY raw JSON (no markdown, no backticks):
{{
  "is_valid": true,
  "reason": "",
  "category": "chosen category",
  "priority": "chosen priority",
  "questions": [
    {{"question": "...", "options": ["...", "...", "...", "Other"]}},
    {{"question": "...", "options": ["...", "...", "...", "Other"]}},
    {{"question": "...", "options": ["...", "...", "...", "Other"]}}
  ]
}}
"""

    response = None
    last_error = None
    for model in ["gemini-3.6-flash", "gemini-3.5-flash"]:
        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config={
                    "thinking_config": {"thinking_budget": 0},
                    "max_output_tokens": 1500,
                    "temperature": 0.5,
                },
            )
            raw_text = (response.text or "").strip() if response else ""
            print(f"[UNIFIED ANALYZER RAW from {model}] {raw_text[:800]}")
            data = _extract_json(raw_text)
            return _finalize_analysis(data, complaint_text, pnr_number, source=model)
        except Exception as e:
            last_error = e
            raw = "No response"
            if response is not None:
                try:
                    raw = response.text
                except Exception:
                    raw = "Response had no .text"
            print(f"[UNIFIED ANALYZER ERROR on {model}] {e}")
            print(f"[RAW RESPONSE] {raw}")
            continue

    print(f"[UNIFIED ANALYZER] Both models failed ({last_error}); using keyword fallback")
    fallback_data = _get_rule_fallback(complaint_text)
    return _finalize_analysis(fallback_data, complaint_text, pnr_number, source="fallback")
