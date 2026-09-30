from database import get_history


def total_tickets():
    tickets = get_history()
    return len(tickets)


def refund_issue_count():
    tickets = get_history()

    count = 0

    for ticket in tickets:
        if ticket[2] == "Refund Issue":
            count += 1

    return count


def cancellation_count():
    tickets = get_history()

    count = 0

    for ticket in tickets:
        if ticket[2] == "Ticket Cancellation":
            count += 1

    return count


def train_delay_count():
    tickets = get_history()

    count = 0

    for ticket in tickets:
        if ticket[2] == "Train Delay":
            count += 1

    return count


def booking_issue_count():
    tickets = get_history()

    count = 0

    for ticket in tickets:
        if ticket[2] == "Booking Issue":
            count += 1

    return count


def other_count():
    tickets = get_history()

    count = 0

    for ticket in tickets:
        if ticket[2] == "Other":
            count += 1

    return count