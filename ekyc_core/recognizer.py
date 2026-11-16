import cv2
import numpy as np
import os

class FaceRecognizer:
    def __init__(self, model_path="models/face_recognition_sface_2021dec.onnx", cosine_threshold=0.35):
        if not os.path.isabs(model_path):
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            model_path = os.path.join(base_dir, model_path)

        if not os.path.exists(model_path):
            raise FileNotFoundError(f"SFace model not found at: {model_path}")

        self.model_path = model_path
        self.cosine_threshold = cosine_threshold
        self.recognizer = cv2.FaceRecognizerSF.create(self.model_path, "")

    def align_and_crop(self, image: np.ndarray, face_info: np.ndarray) -> np.ndarray:
        """Aligns and crops the face using facial landmarks."""
        return self.recognizer.alignCrop(image, face_info)

    def extract_features(self, aligned_face: np.ndarray) -> np.ndarray:
        """
        Extracts a 128-dimensional L2-normalized feature embedding vector.
        """
        return self.recognizer.feature(aligned_face)

    def extract_from_face(self, image: np.ndarray, face_info: np.ndarray) -> np.ndarray:
        """Combines alignment and feature extraction."""
        aligned = self.align_and_crop(image, face_info)
        features = self.extract_features(aligned)
        return features

    def compute_similarity(self, feat1: np.ndarray, feat2: np.ndarray) -> float:
        """
        Computes cosine similarity between two 128D feature embeddings.
        Returns score roughly between -1.0 and 1.0 (typical match >= 0.363).
        """
        score = self.recognizer.match(feat1, feat2, cv2.FaceRecognizerSF_FR_COSINE)
        return float(score)

    def is_match(self, feat1: np.ndarray, feat2: np.ndarray, threshold=None) -> tuple:
        """
        Checks if two embeddings represent the same identity.
        Returns: (is_matched: bool, similarity_score: float)
        """
        th = self.cosine_threshold if threshold is None else threshold
        score = self.compute_similarity(feat1, feat2)
        return (score >= th), score

