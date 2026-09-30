from flask import Response
from database import get_history
import csv
import io


def export_csv():

    tickets = get_history()

    output = io.StringIO()

    writer = csv.writer(output)


    writer.writerow([
        "ID",
        "Complaint",
        "Category",
        "PNR Number",
        "Status"
    ])


    for ticket in tickets:
        writer.writerow(ticket)


    csv_data = output.getvalue()


    return Response(
         "\ufeff" + csv_data,   # Excel compatibility
        mimetype="text/csv",
        headers={
            "Content-Disposition":
            "attachment; filename=railway_complaints.csv"
        }
    )