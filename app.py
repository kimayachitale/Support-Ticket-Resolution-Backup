from flask import Flask, render_template, request
import json

from database import save_ticket, get_history, clear_history
from gemini_helper import generate_reply, make_final_decision
from export_excel import export_excel
from unified_analyzer import analyze_complaint


app = Flask(__name__)


# Load Railway Data
with open("railway_data.json", "r") as file:
    railway_data = json.load(file)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze_ticket():
    passenger_name = (request.form.get("name") or "").strip()
    pnr_input = "".join(ch for ch in (request.form.get("pnr") or "") if ch.isdigit())
    complaint = (request.form.get("ticket") or request.form.get("complaint") or "").strip()

    form_values = {
        "passenger_name": passenger_name,
        "pnr_input": pnr_input,
        "complaint": complaint,
    }

    if not passenger_name or len(pnr_input) != 10 or len(complaint) < 10:
        return render_template(
            "index.html",
            error_message="Please enter your name, a 10-digit PNR, and a complaint of at least 10 characters.",
            **form_values,
        )

    # ── UNIFIED ANALYZER: Validation + Category + Priority + Questions ────────
    analysis = analyze_complaint(complaint)

    if not analysis.get("is_valid", True):
        error_message = (
            f"❌ Invalid Complaint: {analysis.get('reason', 'Please enter a genuine railway-related issue.')}"
        )
        return render_template("index.html", error_message=error_message, **form_values)

    category = analysis.get("category") or "Other"
    priority = analysis.get("priority") or "Medium"
    pnr_number = pnr_input
    questions = analysis.get("questions") or []

    # Save to history with Pending status
    save_ticket(
        complaint,
        category,
        pnr_number,
        "Pending Clarification"
    )

    return render_template(
        "index.html",
        category=category,
        pnr_number=pnr_number,
        priority=priority,
        questions=questions,
        **form_values,
    )


@app.route("/decide", methods=["POST"])
def decide_refund():
    complaint = request.form.get("complaint")
    category = request.form.get("category")
    pnr_number = request.form.get("pnr")
    priority = request.form.get("priority")

    # Collect radio button answers + 'Other' text input
    answers = []
    for i in range(1, 10):
        selected = request.form.get(f"answer_{i}")
        other = request.form.get(f"answer_{i}_other")
        if selected == "Other" and other and other.strip():
            answers.append(f"Other: {other.strip()}")
        elif selected:
            answers.append(selected.strip())

    # Find railway ticket passenger data from PNR
    passenger_data = None
    for ticket in railway_data:
        if str(ticket.get("pnr_number", "")).strip() == str(pnr_number).strip():
            passenger_data = ticket
            break

    # Make final decision using user clarifications
    decision = make_final_decision(complaint, category, answers, passenger_data)

    # Generate short, polite AI reply incorporating verdict
    ai_reply = generate_reply(
        complaint,
        category,
        decision,
        answers
    )

    # Update complaint history with final decision verdict
    save_ticket(
        complaint,
        category,
        pnr_number,
        decision.get("verdict", "Resolved")
    )

    return render_template(
        "index.html",
        complaint=complaint,
        category=category,
        pnr_number=pnr_number,
        priority=priority,
        decision=decision,
        reply=ai_reply,
        answers=answers
    )


@app.route("/history")
def history():
    tickets = get_history()
    total = len(tickets)

    refund = len([t for t in tickets if t[2] == "Refund Issue"])
    cancellation = len([t for t in tickets if t[2] == "Ticket Cancellation"])
    delay = len([t for t in tickets if t[2] == "Train Delay"])
    booking = len([t for t in tickets if t[2] == "Booking Issue"])
    seat = len([t for t in tickets if t[2] == "Seat Complaint"])
    other = len([t for t in tickets if t[2] == "Other"])

    return render_template(
        "history.html",
        tickets=tickets,
        total=total,
        refund=refund,
        cancellation=cancellation,
        delay=delay,
        booking=booking,
        seat=seat,
        other=other
    )


@app.route("/clear")
def clear():
    clear_history()
    return "History Cleared Successfully"


@app.route("/export")
def export():
    return export_excel()


if __name__ == "__main__":
    app.run(debug=True)
