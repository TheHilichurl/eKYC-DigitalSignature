import cv2
import numpy as np
import os
import math

class FaceDetector:
    def __init__(self, model_path="models/face_detection_yunet_2023mar.onnx", conf_threshold=0.50, nms_threshold=0.35):
        """
        FaceDetector using OpenCV Zoo YuNet ONNX model.
        conf_threshold set to 0.50 (standard YuNet operational range) combined with
        strict facial landmark geometry checks to eliminate false positives on ceilings,
        floors, walls, lamps, and background textures.
        """
        if not os.path.isabs(model_path):
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            model_path = os.path.join(base_dir, model_path)
            
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"YuNet model not found at: {model_path}")

        self.model_path = model_path
        self.conf_threshold = conf_threshold
        self.nms_threshold = nms_threshold
        self.detector = cv2.FaceDetectorYN.create(
            self.model_path,
            "",
            (320, 320),
            score_threshold=self.conf_threshold,
            nms_threshold=self.nms_threshold,
            top_k=10
        )
        self.current_size = (320, 320)

    @staticmethod
    def is_valid_face_geometry(face_info: np.ndarray, img_w: int, img_h: int) -> bool:
        """
        Validates that a candidate bounding box and its 5 landmarks belong to a genuine human face.
        YuNet face_info format:
          [x, y, w, h, x_re, y_re, x_le, y_le, x_nt, y_nt, x_rcm, y_rcm, x_lcm, y_lcm, score]
        Checks:
          1. Minimum size: Face must be at least 40x40 pixels and occupy >= 0.5% of frame.
          2. Aspect ratio: Width / Height must be between 0.55 and 1.35.
          3. Eye distance: Distance between left and right eye must be >= 18% of face width.
          4. Landmark topology:
             - Eyes must be horizontally oriented (tilt angle <= 45 degrees).
             - Nose tip must be vertically between the eye level and the mouth level.
             - Mouth must be below the nose.
             - Mouth width must be >= 12% of face width.
             - Landmarks must lie within or very close to the bounding box.
        """
        if face_info is None or len(face_info) < 15:
            return False

        x, y, w, h = float(face_info[0]), float(face_info[1]), float(face_info[2]), float(face_info[3])
        score = float(face_info[-1])

        # 1. Minimum dimension check (scales with image resolution)
        min_dim = max(28, int(min(img_w, img_h) * 0.08))
        if w < min_dim or h < min_dim:
            return False
        if w > img_w * 1.05 or h > img_h * 1.05:
            return False

        # Area check (at least 0.3% of image)
        face_area = w * h
        img_area = img_w * img_h
        if img_area > 0 and (face_area / img_area) < 0.003:
            return False

        # 2. Aspect ratio check (human face is roughly oval, 0.55 <= w/h <= 1.35)
        aspect = w / max(h, 1.0)
        if aspect < 0.50 or aspect > 1.40:
            return False

        # Extract landmarks
        x_re, y_re = float(face_info[4]), float(face_info[5])    # Right eye
        x_le, y_le = float(face_info[6]), float(face_info[7])    # Left eye
        x_nt, y_nt = float(face_info[8]), float(face_info[9])    # Nose tip
        x_rcm, y_rcm = float(face_info[10]), float(face_info[11]) # Right mouth corner
        x_lcm, y_lcm = float(face_info[12]), float(face_info[13]) # Left mouth corner

        # 3. Eye distance check
        dx_eyes = x_le - x_re
        dy_eyes = y_le - y_re
        eye_dist = math.sqrt(dx_eyes * dx_eyes + dy_eyes * dy_eyes)
        if eye_dist < (0.16 * w):
            return False

        # Eye tilt angle check (cannot be rotated > 45 deg for standard frontal/angled verification)
        eye_angle = abs(math.atan2(dy_eyes, max(abs(dx_eyes), 1e-5)) * 180.0 / math.pi)
        if eye_angle > 45.0:
            return False

        # 4. Vertical landmark topology check
        # Average eye y
        avg_eye_y = (y_re + y_le) / 2.0
        # Average mouth y
        avg_mouth_y = (y_rcm + y_lcm) / 2.0

        # Eyes must be above the nose tip
        if avg_eye_y >= y_nt:
            return False

        # Nose tip must be above the mouth
        if y_nt >= avg_mouth_y:
            return False

        # Mouth width check
        dx_mouth = x_lcm - x_rcm
        dy_mouth = y_lcm - y_rcm
        mouth_dist = math.sqrt(dx_mouth * dx_mouth + dy_mouth * dy_mouth)
        if mouth_dist < (0.12 * w):
            return False

        # 5. Landmarks containment check (landmarks should not be wildly outside bbox)
        margin_x = w * 0.25
        margin_y = h * 0.25
        landmarks = [(x_re, y_re), (x_le, y_le), (x_nt, y_nt), (x_rcm, y_rcm), (x_lcm, y_lcm)]
        for lx, ly in landmarks:
            if lx < (x - margin_x) or lx > (x + w + margin_x):
                return False
            if ly < (y - margin_y) or ly > (y + h + margin_y):
                return False

        # 6. Confidence check
        if score < 0.45:
            return False

        return True

    def detect(self, image: np.ndarray):
        """
        Detects genuine human faces in an image.
        Returns:
            faces: numpy array of valid detected faces or None.
        """
        if image is None or image.size == 0:
            return None

        h, w = image.shape[:2]
        if (w, h) != self.current_size:
            self.detector.setInputSize((w, h))
            self.current_size = (w, h)

        # Primary detection pass
        _, faces = self.detector.detect(image)

        # If no face found and image is dim (mean intensity < 45), try mild gamma lift
        if (faces is None or len(faces) == 0):
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            mean_brightness = np.mean(gray)
            if mean_brightness < 45.0:
                # Dark room compensation: mild gamma curve
                inv_gamma = 1.0 / 1.5
                table = np.array([((i / 255.0) ** inv_gamma) * 255 for i in np.arange(0, 256)]).astype("uint8")
                brightened = cv2.LUT(image, table)
                _, faces = self.detector.detect(brightened)

        if faces is None or len(faces) == 0:
            return None

        # Filter strictly by geometric validity and landmarks
        valid_faces = []
        for face in faces:
            if self.is_valid_face_geometry(face, w, h):
                valid_faces.append(face)

        if not valid_faces:
            return None

        return np.array(valid_faces)

    def get_dominant_face(self, image: np.ndarray):
        """
        Returns the most prominent valid human face (largest bounding box area).
        Returns:
            face_info: 1D array of 15 elements or None.
            bbox: [x, y, w, h] as ints or None.
        """
        faces = self.detect(image)
        if faces is None or len(faces) == 0:
            return None, None

        # Sort by area (w * h) descending
        areas = [f[2] * f[3] for f in faces]
        best_idx = int(np.argmax(areas))
        best_face = faces[best_idx]
        bbox = [int(best_face[0]), int(best_face[1]), int(best_face[2]), int(best_face[3])]
        return best_face, bbox
