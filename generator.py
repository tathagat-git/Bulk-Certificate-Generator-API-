import os

from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas


def create_certificate_pdf(name, course_name, issue_date, file_path):
    """Creates one certificate PDF using the single fixed template."""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    width, height = landscape(A4)
    c = canvas.Canvas(file_path, pagesize=landscape(A4))

    c.setLineWidth(4)
    c.rect(25, 25, width - 50, height - 50)

    c.setFont("Helvetica-Bold", 40)
    c.drawCentredString(width / 2, height - 120, "CERTIFICATE OF COMPLETION")

    c.setFont("Helvetica", 18)
    c.drawCentredString(width / 2, height - 190, "This is to certify that")

    c.setFont("Helvetica-Bold", 36)
    c.drawCentredString(width / 2, height - 250, name)

    c.setFont("Helvetica", 18)
    c.drawCentredString(width / 2, height - 310, "has successfully completed the course")

    c.setFont("Helvetica-Bold", 26)
    c.drawCentredString(width / 2, height - 360, course_name)

    c.setFont("Helvetica", 14)
    c.drawCentredString(width / 2, 80, f"Date: {issue_date}")

    c.save()
