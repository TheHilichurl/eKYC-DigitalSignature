import os
import unittest
import cv2
import numpy as np

from ekyc_core.crypto_pki import CryptoPKI
from ekyc_core.db_pki import PkiDatabase
from ekyc_core.pdf_signer import PdfSignerEngine
from ekyc_core.engine import EkycEngine

class TestEkycDigitalSignature(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = PkiDatabase("data/test_ekyc_pki.db")
        cls.ekyc = EkycEngine()
        cls.sample_pdf = "data/samples/sample_contract.pdf"
        cls.stamp_img = "data/samples/sample_stamp.png"
        cls.sig_img = "data/samples/sample_signature.png"
        cls.face_sample = "data/samples/suzuka-nakamoto.jpg"
        cls.fake_face_sample = "data/samples/suzuka-nakomo-fake.jpg"

    def test_01_asymmetric_key_generation_and_signing(self):
        """Test RSA-2048 Keypair generation and SHA-256 digital signature."""
        priv_pem, pub_pem = CryptoPKI.generate_key_pair(2048)
        self.assertIn("BEGIN PRIVATE KEY", priv_pem)
        self.assertIn("BEGIN PUBLIC KEY", pub_pem)

        sample_data = b"Electronic Document Contract Content"
        sig_hex = CryptoPKI.sign_data(sample_data, priv_pem)
        self.assertTrue(len(sig_hex) > 100)

        # Verification of authentic data
        is_valid = CryptoPKI.verify_signature(sample_data, sig_hex, pub_pem)
        self.assertTrue(is_valid, "Authentic data must verify successfully")

        # Verification of tampered data
        tampered_data = b"Electronic Document Contract Content - ALTERED"
        is_tampered_valid = CryptoPKI.verify_signature(tampered_data, sig_hex, pub_pem)
        self.assertFalse(is_tampered_valid, "Tampered data must fail cryptographic check")

    def test_02_database_pki_user_and_assets(self):
        """Test storing user with RSA keys and stamp/signature assets in SQLite."""
        priv_pem, pub_pem = CryptoPKI.generate_key_pair(2048)
        user_id = "test_user_01"
        dummy_embedding = np.random.randn(128).astype(np.float32)

        self.db.add_user(
            user_id=user_id,
            name="Nguyen Van Giang",
            id_card="001201004567",
            department="Ban Giam Doc",
            embedding=dummy_embedding,
            avatar_path="data/avatars/test.jpg",
            public_key_pem=pub_pem,
            private_key_pem=priv_pem
        )

        user = self.db.get_user(user_id)
        self.assertIsNotNone(user)
        self.assertEqual(user['name'], "Nguyen Van Giang")
        self.assertEqual(len(user['face_embedding']), 128)

        # Add stamp asset
        self.db.add_asset("asset_stamp_01", user_id, "stamp", "Con Dau Do Cong Ty", self.stamp_img)
        # Add signature asset
        self.db.add_asset("asset_sig_01", user_id, "signature", "Chu Ky Giam Doc", self.sig_img)

        assets = self.db.list_user_assets(user_id)
        self.assertEqual(len(assets), 2)

    def test_03_ekyc_biometric_gatekeeper(self):
        """Test that eKYC correctly validates live face and blocks spoof attacks."""
        img_real = cv2.imread(self.face_sample)
        scan_real = self.ekyc.scan_and_identify(img_real, liveness_mode="low")
        self.assertTrue(scan_real['success'])
        self.assertTrue(scan_real['results'][0]['liveness']['is_real'])

        img_fake = cv2.imread(self.fake_face_sample)
        scan_fake = self.ekyc.scan_and_identify(img_fake, liveness_mode="medium")
        self.assertTrue(scan_fake['success'])
        self.assertFalse(scan_fake['results'][0]['liveness']['is_real'], "Fake face must be detected as spoof")

    def test_04_pdf_stamp_sign_and_tamper_verification(self):
        """Test full pipeline: stamping PDF at coordinates, digital signing, and tamper detection."""
        priv_pem, pub_pem = CryptoPKI.generate_key_pair(2048)
        output_pdf = "data/samples/test_signed_contract.pdf"

        # Sign and stamp onto page 1 at x=380, y=420, width=150, height=70
        res = PdfSignerEngine.stamp_and_sign_pdf(
            input_pdf_path=self.sample_pdf,
            output_pdf_path=output_pdf,
            stamp_image_path=self.stamp_img,
            page_num=1,
            x_pt=380,
            y_pt=420,
            width_pt=150,
            height_pt=150,
            signer_name="Nguyen Van Giang",
            private_pem=priv_pem,
            public_pem=pub_pem,
            id_card="001201004567"
        )

        self.assertTrue(res['success'])
        self.assertTrue(os.path.exists(output_pdf))

        # 1. Verify authentic signed document
        verify_res = PdfSignerEngine.verify_signed_pdf(output_pdf)
        self.assertTrue(verify_res['valid'], "Authentic signed PDF must pass integrity check")
        self.assertEqual(verify_res['signer_name'], "Nguyen Van Giang")

        # 2. Tamper test: Alter 1 byte in the PDF file
        with open(output_pdf, "rb") as f:
            pdf_bytes = bytearray(f.read())
        # Corrupt a byte in the middle of document
        pdf_bytes[500] = (pdf_bytes[500] + 1) % 256

        tampered_pdf = "data/samples/test_tampered_contract.pdf"
        with open(tampered_pdf, "wb") as f:
            f.write(pdf_bytes)

        verify_tampered = PdfSignerEngine.verify_signed_pdf(tampered_pdf)
        self.assertFalse(verify_tampered['valid'], "Tampered PDF must fail cryptographic integrity check")

if __name__ == '__main__':
    unittest.main()

