def calculate_refund(ticket_status, fare):
    """
    IRCTC Railway Ticket Refund Calculation
    """

    if ticket_status.lower() == "cancelled":

        refund_amount = fare * 0.80

        return {
            "refund_eligible": True,
            "refund_amount": refund_amount,
            "reason": "Ticket cancelled successfully. 80% refund is applicable after cancellation charges."
        }


    elif ticket_status.lower() == "completed":

        return {
            "refund_eligible": False,
            "refund_amount": 0,
            "reason": "Journey is completed. Refund is not applicable."
        }


    elif ticket_status.lower() == "in-transit":

        return {
            "refund_eligible": False,
            "refund_amount": 0,
            "reason": "Passenger journey is in progress. Refund cannot be processed."
        }


    else:

        return {
            "refund_eligible": False,
            "refund_amount": 0,
            "reason": "Ticket status not found. Refund decision unavailable."
        }