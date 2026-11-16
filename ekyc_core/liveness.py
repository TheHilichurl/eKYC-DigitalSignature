import cv2
import numpy as np
import os
from .anti_spoof import AntiSpoof, CropImage, parse_model_name

class LivenessDetector:
    def __init__(self, model_dir="models/spoof_detection", device_id=0):
        if not os.path.isabs(model_dir):
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            model_dir = os.path.join(base_dir, model_dir)

        if not os.path.exists(model_dir):
            raise FileNotFoundError(f"Spoof detection model dir not found: {model_dir}")

        self.model_dir = model_dir
        # Only use valid MultiFTNet models from the directory
        self.model_names = [
            f for f in os.listdir(model_dir) 
            if f.endswith(".pth") and "MultiFTNet" in f
        ]
        if not self.model_names:
            raise FileNotFoundError(f"No valid MultiFTNet .pth models found in {model_dir}")

        self.anti_spoof = AntiSpoof(device_id)
        self.cropper = CropImage()

    @staticmethod
    def calculate_blur(image: np.ndarray) -> float:
        """Computes Laplacian variance to assess image blurriness."""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return float(cv2.Laplacian(gray, cv2.CV_64F).var())

    def check_liveness(self, image: np.ndarray, bbox: list, sensitivity: str = "medium") -> dict:
        """
        Runs anti-spoofing prediction on the given face bounding box [x, y, w, h].
        Sensitivity modes:
          - 'high': Strict check. Real probability must dominate (> 0.55).
          - 'medium': Standard threshold (Real >= 0.38).
          - 'low': Lenient mode (Real >= 0.25). Best for laptop webcams at night / monitor glare.
          - 'off': Bypasses anti-spoofing check.
        """
        if sensitivity == "off":
            return {
                "is_real": True,
                "label": 1,
                "score": 1.0,
                "blur_score": 100.0,
                "is_blurred": False,
                "raw_scores": {"fake_0": 0.0, "real_1": 1.0, "fake_2": 0.0},
                "mode": "off"
            }

        blur_score = self.calculate_blur(image)
        is_blurred = blur_score < 40.0

        prediction = np.zeros((1, 3))
        for model_name in self.model_names:
            h_input, w_input, model_type, scale = parse_model_name(model_name)
            param = {
                'org_img': image,
                'bbox': bbox,
                'scale': scale,
                'out_w': w_input,
                'out_h': h_input,
                'crop': True
            }
            if scale is None:
                param['crop'] = False

            img_cropped = self.cropper.crop(**param)
            model_path = os.path.join(self.model_dir, model_name)
            prediction += self.anti_spoof.predict(img_cropped, model_path)

        avg_prediction = prediction / len(self.model_names)
        fake_0 = float(avg_prediction[0][0])
        real_1 = float(avg_prediction[0][1])
        fake_2 = float(avg_prediction[0][2])

        # Adaptive thresholding based on sensitivity
        if sensitivity == "low":
            threshold = 0.25
        elif sensitivity == "high":
            threshold = 0.55
        else:  # medium
            threshold = 0.38

        is_real = bool(real_1 >= threshold and real_1 >= fake_0 * 0.8)
        
        # Determine dominant label
        label = int(np.argmax(avg_prediction))

        return {
            "is_real": is_real,
            "label": 1 if is_real else label,
            "score": real_1 if is_real else max(fake_0, fake_2),
            "blur_score": blur_score,
            "is_blurred": is_blurred,
            "threshold_used": threshold,
            "raw_scores": {
                "fake_0": fake_0,
                "real_1": real_1,
                "fake_2": fake_2
            }
        }
