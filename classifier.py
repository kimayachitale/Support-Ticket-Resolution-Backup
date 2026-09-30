from google import genai
import re

client = genai.Client(api_key="GOOGLE_API_KEY")

VALID_CATEGORIES = [
    "Refund Issue",
    "Ticket Cancellation",
    "Train Delay",
    "Booking Issue",
    "Seat Complaint",
    "Food Complaint",
    "Staff Complaint",
    "Lost Item",
    "Other"
]


def classify_ticket(complaint):

    prompt = f"""You are an AI railway complaint classification system.

Classify the passenger complaint into exactly one category.

Categories:
- Refund Issue
- Ticket Cancellation
- Train Delay
- Booking Issue
- Seat Complaint
- Food Complaint
- Staff Complaint
- Lost Item
- Other

Complaint:
{complaint}

Return ONLY the exact category name from the list above. No explanation, no punctuation."""

    category = "Other"

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
        raw_category = response.text.strip()

        # Sanitize to match strictly one of the allowed categories
        for valid_cat in VALID_CATEGORIES:
            if valid_cat.lower() in raw_category.lower():
                category = valid_cat
                break
        else:
            category = "Other"

    except Exception as e:
        print(f"[CLASSIFIER ERROR] {e}")
        category = "Other"

    # Extract 10-digit PNR Number
    pnr_match = re.search(r"\b\d{10}\b", complaint)
    if pnr_match:
        pnr_number = pnr_match.group()
    else:
        pnr_number = "Not Provided"

    return {
        "category": category,
        "pnr_number": pnr_number
    }
