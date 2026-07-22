import qrcode

from pathlib import Path

from app.models.certificate import Certificate


class CertificateQRService:

    OUTPUT_DIR = Path(
        "uploads/certificates/qr"
    )

    VERIFY_URL = (
        "https://verify.vizu.uz/certificate/"
    )

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
            f"{certificate.certificate_number}.png"
        )

        filepath = (
            self.OUTPUT_DIR / filename
        )

        img = qrcode.make(
            self.VERIFY_URL
            + certificate.verification_code
        )

        img.save(filepath)

        return str(filepath)