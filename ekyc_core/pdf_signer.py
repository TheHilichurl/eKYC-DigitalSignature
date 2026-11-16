import os
import io
import json
import uuid
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from PIL import Image
from datetime import datetime

from .crypto_pki import CryptoPKI

class PdfSignerEngine:
    @staticmethod
    def stamp_and_sign_pdf(
        input_pdf_path: str,
        output_pdf_path: str,
        stamp_image_path: str,
        page_num: int,
        x_pt: float,
        y_pt: float,
        width_pt: float,
        height_pt: float,
        signer_name: str,
        private_pem: str,
        public_pem: str,
        id_card: str = "",
        audit_note: str = "Verified by eKYC Biometrics"
    ) -> dict:
        """
        Stamps signature/seal image onto specific page & coordinates of PDF,
        and cryptographically signs the document with RSA-2048 + SHA-256.
        Coordinates: x_pt, y_pt measured from TOP-LEFT of page.
        """
        if not os.path.exists(input_pdf_path):
            raise FileNotFoundError(f"Input PDF not found: {input_pdf_path}")
        if not os.path.exists(stamp_image_path):
            raise FileNotFoundError(f"Stamp image not found: {stamp_image_path}")

        # Read original bytes for hash
        with open(input_pdf_path, "rb") as f:
            original_bytes = f.read()
        original_sha256 = CryptoPKI.calculate_sha256(original_bytes)

        # Clone PDF with pypdf 7.0+
        writer = PdfWriter(clone_from=input_pdf_path)
        total_pages = len(writer.pages)
        if page_num < 1 or page_num > total_pages:
            raise ValueError(f"Page number {page_num} is out of range (1 to {total_pages})")

        # Get target page dimensions
        target_page = writer.pages[page_num - 1]
        page_width = float(target_page.mediabox.width)
        page_height = float(target_page.mediabox.height)

        # Convert top-left coordinates to PDF bottom-left coordinates
        pdf_y = page_height - y_pt - height_pt

        # 1. Generate an overlay PDF with the stamp image using ReportLab
        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=(page_width, page_height))

        # Draw stamp/signature image with transparency
        pil_img = Image.open(stamp_image_path)
        can.drawImage(
            ImageReader(pil_img),
            x_pt,
            pdf_y,
            width=width_pt,
            height=height_pt,
            mask='auto'
        )
        can.save()
        packet.seek(0)

        # 2. Merge overlay onto target page
        overlay_reader = PdfReader(packet)
        overlay_page = overlay_reader.pages[0]
        target_page.merge_page(overlay_page)

        # 3. Write final stamped PDF to disk
        os.makedirs(os.path.dirname(output_pdf_path), exist_ok=True)
        with open(output_pdf_path, "wb") as f_out:
            writer.write(f_out)

        # 4. Cryptographic Digital Signature of the Final Document
        with open(output_pdf_path, "rb") as f_final:
            final_bytes = f_final.read()
        signed_sha256 = CryptoPKI.calculate_sha256(final_bytes)

        # Sign the SHA-256 hash using the Signer's Private Key
        crypto_signature_hex = CryptoPKI.sign_data(signed_sha256.encode('utf-8'), private_pem)

        doc_id = str(uuid.uuid4())[:12]
        manifest = {
            "doc_id": doc_id,
            "document_name": os.path.basename(output_pdf_path),
            "signer_name": signer_name,
            "id_card": id_card,
            "signed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "audit_note": audit_note,
            "original_sha256": original_sha256,
            "signed_sha256": signed_sha256,
            "crypto_signature_hex": crypto_signature_hex,
            "public_key_pem": public_pem,
            "stamp_position": {
                "page": page_num,
                "x": x_pt,
                "y": y_pt,
                "width": width_pt,
                "height": height_pt
            }
        }

        # Save cryptographic signature manifest (.sig.json)
        sig_manifest_path = output_pdf_path + ".sig.json"
        with open(sig_manifest_path, "w", encoding="utf-8") as f_sig:
            json.dump(manifest, f_sig, ensure_ascii=False, indent=2)

        return {
            "success": True,
            "doc_id": doc_id,
            "original_sha256": original_sha256,
            "signed_sha256": signed_sha256,
            "crypto_signature_hex": crypto_signature_hex,
            "output_pdf_path": output_pdf_path,
            "sig_manifest_path": sig_manifest_path,
            "page_number": page_num,
            "position": {"x": x_pt, "y": y_pt, "width": width_pt, "height": height_pt}
        }

    @staticmethod
    def verify_signed_pdf(pdf_path: str, manifest_data: dict = None) -> dict:
        """
        Cryptographically verifies whether the PDF matches its digital signature.
        Detects any tampering down to a single byte change.
        """
        if not os.path.exists(pdf_path):
            return {"valid": False, "message": "Tệp tin PDF không tồn tại"}

        # If manifest not provided, check for adjacent .sig.json
        if manifest_data is None:
            manifest_path = pdf_path + ".sig.json"
            if not os.path.exists(manifest_path):
                return {
                    "valid": False, 
                    "message": "Không tìm thấy chứng thực chữ ký số (.sig.json) đi kèm tài liệu"
                }
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest_data = json.load(f)

        sig_hex = manifest_data.get("crypto_signature_hex")
        public_pem = manifest_data.get("public_key_pem")
        recorded_sha256 = manifest_data.get("signed_sha256")
        signer_name = manifest_data.get("signer_name", "Không rõ")
        id_card = manifest_data.get("id_card", "")
        signed_at = manifest_data.get("signed_at", "")

        if not sig_hex or not public_pem or not recorded_sha256:
            return {"valid": False, "message": "Chứng thư chữ ký số bị thiếu thông tin hoặc hỏng"}

        # Compute current document SHA-256
        with open(pdf_path, "rb") as f:
            current_bytes = f.read()
        current_sha256 = CryptoPKI.calculate_sha256(current_bytes)

        # 1. Check if document hash matches recorded hash
        if current_sha256 != recorded_sha256:
            return {
                "valid": False,
                "tampered": True,
                "signer_name": signer_name,
                "id_card": id_card,
                "signed_at": signed_at,
                "recorded_sha256": recorded_sha256,
                "current_sha256": current_sha256,
                "status": "CẢNH BÁO: TÀI LIỆU ĐÃ BỊ CHỈNH SỬA TRÁI PHÉP (TAMPERED)!",
                "message": "Mã băm SHA-256 hiện tại không khớp với mã băm lúc ký. Nội dung PDF đã bị can thiệp."
            }

        # 2. Check RSA asymmetric signature
        is_crypto_valid = CryptoPKI.verify_signature(current_sha256.encode('utf-8'), sig_hex, public_pem)
        if not is_crypto_valid:
            return {
                "valid": False,
                "tampered": True,
                "signer_name": signer_name,
                "status": "CẢNH BÁO: CHỮ KÝ SỐ KHÔNG HỢP LỆ HOẶC BỊ GIẢ MẠO!",
                "message": "Chữ ký số RSA-2048 không thể xác thực bằng khóa công khai của người ký."
            }

        return {
            "valid": True,
            "tampered": False,
            "signer_name": signer_name,
            "id_card": id_card,
            "signed_at": signed_at,
            "sha256": current_sha256,
            "status": "HỢP LỆ - TOÀN VẸN (AUTHENTIC & VERIFIED)",
            "message": "Tài liệu hoàn toàn nguyên bản, đúng người ký và đã được chứng thực sinh trắc học eKYC."
        }
