import qrcode
import os
from flask import current_app

class QRService:
    @staticmethod
    def generate_prescription_qr(prescription_uuid):
        """
        Generates a QR code for a given prescription UUID and saves it to the static folder.
        Returns the filename of the generated QR code.
        """
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        
        # The QR code will just contain the secure UUID
        data = f"prescription:{prescription_uuid}"
        qr.add_data(data)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        
        filename = f"{prescription_uuid}.png"
        filepath = os.path.join(current_app.config['QR_FOLDER'], filename)
        
        img.save(filepath)
        return filename
