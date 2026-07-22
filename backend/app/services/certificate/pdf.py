from pathlib import Path

from reportlab.lib.units import mm

from reportlab.pdfgen import canvas

from app.models.certificate import Certificate


class CertificatePDFService:

    OUTPUT_DIR = Path("uploads/certificates")

    def __init__(self):

        self.OUTPUT_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

    def generate(
        self,
        certificate: Certificate,
    ):

        filename = (
            f"{certificate.certificate_number}.pdf"
        )

        filepath = (
            self.OUTPUT_DIR / filename
        )

        pdf = canvas.Canvas(
            str(filepath),
            pagesize=(297 * mm, 210 * mm),
        )

        pdf.setTitle(
            "VIZU Certificate"
        )

        pdf.setFont(
            "Helvetica-Bold",
            24,
        )

        pdf.drawCentredString(
            420,
            520,
            "CERTIFICATE",
        )

        pdf.setFont(
            "Helvetica",
            14,
        )

        pdf.drawString(
            90,
            470,
            f"Certificate No: {certificate.certificate_number}",
        )

        pdf.drawString(
            90,
            445,
            f"Level: {certificate.level}",
        )

        pdf.drawString(
            90,
            420,
            f"Provider: {certificate.provider}",
        )

        pdf.drawString(
            90,
            380,
            f"Lesen: {certificate.lesen_score}",
        )

        pdf.drawString(
            90,
            355,
            f"Hoeren: {certificate.hoeren_score}",
        )

        pdf.drawString(
            90,
            330,
            f"Schreiben: {certificate.schreiben_score}",
        )

        pdf.drawString(
            90,
            305,
            f"Sprechen: {certificate.sprechen_score}",
        )

        pdf.drawString(
            90,
            265,
            f"Total: {certificate.score}",
        )

        pdf.save()

        return str(filepath)