import os
import shutil
import unittest
import cv2
import numpy as np

from ekyc_core.engine import EkycEngine
from ekyc_core.detector import FaceDetector


class TestBiometricIntegrity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_data_dir = os.path.join("data", "test_bio_tmp")
        os.makedirs(cls.test_data_dir, exist_ok=True)
        cls.engine = EkycEngine(data_dir=cls.test_data_dir)
        cls.giang_img = cv2.imread("data/avatars/avatar_giang_1953.jpg")
        cls.moa_img = cv2.imread("data/avatars/avatar_moa_kikuchi_2008.jpg")
        cls.momoko_img = cv2.imread("data/avatars/avatar_momoko_okazaki_7398.jpg")
        cls.suzuka_img = cv2.imread("data/samples/suzuka-nakamoto.jpg")

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.test_data_dir):
            shutil.rmtree(cls.test_data_dir, ignore_errors=True)

    def test_01_ceiling_wall_noise_never_detected_as_face(self):
        """Ensure empty backgrounds, bright ceiling lights, lines, and noise detect 0 faces."""
        # Bright ceiling with fluorescent rectangle + circle lamp
        ceiling = np.ones((480, 640, 3), dtype=np.uint8) * 210
        cv2.rectangle(ceiling, (150, 80), (490, 140), (255, 255, 255), -1)
        cv2.circle(ceiling, (320, 280), 40, (250, 250, 250), -1)
        cv2.line(ceiling, (0, 200), (640, 200), (140, 140, 140), 2)

        faces_c = self.engine.detector.detect(ceiling)
        self.assertIsNone(faces_c, "Ceiling texture must yield 0 faces")

        scan_res = self.engine.scan_and_identify(ceiling)
        self.assertEqual(scan_res["faces_detected"], 0)

        # Random Gaussian / uniform noise
        rng = np.random.default_rng(42)
        noise = rng.integers(40, 220, (480, 640, 3), dtype=np.uint8)
        faces_n = self.engine.detector.detect(noise)
        self.assertIsNone(faces_n, "Random noise must yield 0 faces")

    def test_02_geometry_filter_rejects_corrupted_landmarks(self):
        """Verify geometric validator catches impossible face boxes or flipped eyes/mouth."""
        # Valid-looking dimensions, but nose is ABOVE eyes -> impossible face
        bad_face = np.array([100, 100, 120, 140,  # x, y, w, h
                             130, 150, 190, 150,  # right eye, left eye
                             160, 120,            # nose ABOVE eye y=150 (invalid!)
                             135, 200, 185, 200,  # mouth
                             0.95], dtype=np.float32)
        self.assertFalse(FaceDetector.is_valid_face_geometry(bad_face, 640, 480))

        # Tiny 12x12 artifact
        tiny_face = np.array([50, 50, 12, 14, 53, 54, 59, 54, 56, 57, 54, 60, 58, 60, 0.90], dtype=np.float32)
        self.assertFalse(FaceDetector.is_valid_face_geometry(tiny_face, 640, 480))

    def test_03_enrollment_validation_and_deduplication(self):
        """Ensure enrollment rejects empty names, ceiling photos, and prevents duplicate CCCD entries."""
        ceiling = np.ones((480, 640, 3), dtype=np.uint8) * 190
        res_bad = self.engine.enroll_person(ceiling, name="Fake User", id_card="999888777")
        self.assertFalse(res_bad["success"], "Cannot enroll an image without a real face")

        res_short = self.engine.enroll_person(self.moa_img, name="A", id_card="111")
        self.assertFalse(res_short["success"], "Cannot enroll a 1-char invalid name")

        # Enroll Moa legitimately
        res1 = self.engine.enroll_person(self.moa_img, name="Moa Kikuchi", id_card="079199008899")
        self.assertTrue(res1["success"])
        uid1 = res1["user"]["id"]

        # Re-enroll same CCCD should update, NOT create duplicate record
        res2 = self.engine.enroll_person(self.moa_img, name="Moa Kikuchi Updated", id_card="079199008899")
        self.assertTrue(res2["success"])
        self.assertEqual(res2["user"]["id"], uid1)
        self.assertEqual(len(self.engine.database.list_all()), 1)

    def test_04_strict_1_to_1_verification_no_cross_user_fallback(self):
        """Verify 1:1 check fails if a DIFFERENT enrolled person appears in front of camera."""
        # Enroll Moa and Giang
        r_moa = self.engine.enroll_person(self.moa_img, name="Moa", id_card="100001")
        r_momoko = self.engine.enroll_person(self.momoko_img, name="Momoko", id_card="100002")
        self.assertTrue(r_moa["success"])
        self.assertTrue(r_momoko["success"])

        moa_id = r_moa["user"]["id"]
        momoko_id = r_momoko["user"]["id"]

        # Present Momoko's face while trying to sign as Moa -> MUST FAIL!
        ver_wrong = self.engine.verify_user_face(self.momoko_img, moa_id, check_liveness=False)
        self.assertTrue(ver_wrong["success"])
        self.assertFalse(ver_wrong["matched"], "Momoko's face must NEVER match Moa's identity in 1:1 mode")

        # Present Momoko's face verifying against Momoko -> MUST PASS!
        ver_right = self.engine.verify_user_face(self.momoko_img, momoko_id, check_liveness=False)
        self.assertTrue(ver_right["success"])
        self.assertTrue(ver_right["matched"], "Momoko's face must verify as Momoko")


if __name__ == "__main__":
    unittest.main()

