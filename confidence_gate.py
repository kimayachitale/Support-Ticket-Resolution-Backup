import json

# Load orders
with open("mock_orders.json", "r") as file:
    orders = json.load(file)


def confidence_score(order_id, category):
    score = 0
    reasons = []

    # Check if Order ID exists
    order = next((o for o in orders if o["order_id"] == order_id), None)

    if order:
        score += 50
        reasons.append("Order ID found")
    else:
        reasons.append("Order ID not found")

    # Check category
    if category != "Other":
        score += 30
        reasons.append("Category identified")
    else:
        reasons.append("Unknown category")

    # Policy available
    score += 20
    reasons.append("Policy available")

    return score, reasons


if __name__ == "__main__":
    order_id = input("Enter Order ID: ")
    category = input("Enter Ticket Category: ")

    score, reasons = confidence_score(order_id, category)

    print("\n===== CONFIDENCE REPORT =====")
    print("Confidence Score:", score, "%")

    print("\nReasons:")
    for reason in reasons:
        print("-", reason)

    if score >= 80:
        print("\nDecision: Grounded Reply")
    else:
        print("\nDecision: Escalate to Human Agent")