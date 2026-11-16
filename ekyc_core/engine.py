import cv2
import numpy as np
import os
from .detector import FaceDetector
from .liveness import LivenessDetector
from .recognizer import FaceRecognizer
from .database import IdentityDatabase

class EkycEngine:
    def __init__(self, models_dir="models", data_dir="data"):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        detector_path = os.path.join(base_dir, models_dir, "face_detection_yunet_2023mar.onnx")
        recognizer_path = os.path.join(base_dir, models_dir, "face_recognition_sface_2021dec.onnx")
        spoof_dir = os.path.join(base_dir, models_dir, "spoof_detection")
        db_path = os.path.join(base_dir, data_dir, "identities.json")
        avatar_dir = os.path.join(base_dir, data_dir, "avatars")

        self.detector = FaceDetector(detector_path)
        self.recognizer = FaceRecognizer(recognizer_path)
        self.liveness = LivenessDetector(spoof_dir)
        self.database = IdentityDatabase(db_path, avatar_dir)

    def scan_and_identify(
        self, 
        image: np.ndarray, 
        check_liveness: bool = True, 
        liveness_mode: str = "low", 
        recognition_threshold: float = 0.35
    ) -> dict:
        """
        Scans an image/video frame, performs face detection, liveness check, and 1:N face identification.
        """
        if image is None or image.size == 0:
            return {"success": False, "message": "Hình ảnh rỗng hoặc không hợp lệ"}

        faces = self.detector.detect(image)
        if faces is None or len(faces) == 0:
            return {
                "success": True,
                "faces_detected": 0,
                "results": [],
                "message": "Không tìm thấy khuôn mặt nào trong ảnh"
            }

        annotated_image = image.copy()
        results = []

        for face_info in faces:
            bbox = [int(face_info[0]), int(face_info[1]), int(face_info[2]), int(face_info[3])]
            det_score = float(face_info[-1])

            # 1. Anti-Spoofing / Liveness Check
            liveness_res = None
            is_real = True
            liveness_score = 1.0

            if check_liveness:
                liveness_res = self.liveness.check_liveness(image, bbox, sensitivity=liveness_mode)
                is_real = liveness_res["is_real"]
                liveness_score = liveness_res["score"]

            # 2. Face Alignment & Embedding Extraction
            aligned_face = self.recognizer.align_and_crop(image, face_info)
            embedding = self.recognizer.extract_features(aligned_face)

            # 3. 1:N Biometric Search
            person, match_score = self.database.search_best_match(
                embedding, self.recognizer, threshold=recognition_threshold
            )

            # Visual feedback rendering
            x, y, w, h = bbox
            if is_real:
                if person is not None:
                    # Real face & Known identity
                    color = (0, 200, 0)  # Green BGR
                    status_text = f"{person['name']} ({match_score*100:.1f}%)"
                    sub_text = f"MẶT THẬT (Liveness: {liveness_score*100:.1f}%)"
                else:
                    # Real face but Unknown
                    color = (255, 165, 0)  # Cyan/Orange BGR
                    status_text = f"MẶT THẬT - CHƯA ĐĂNG KÝ"
                    sub_text = f"Liveness: {liveness_score*100:.1f}%"
            else:
                # Suspected Spoof / Poor lighting
                if person is not None:
                    color = (0, 140, 255)  # Amber / Orange BGR
                    status_text = f"{person['name']} ({match_score*100:.1f}%)"
                    sub_text = f"NGHI VẤN GIẢ MẠO / THIẾU SÁNG"
                else:
                    color = (0, 0, 240)  # Red BGR
                    status_text = f"CẢNH BÁO GIẢ MẠO ({liveness_score*100:.1f}%)"
                    sub_text = "Spoofing Detected!"

            # Draw box & header
            cv2.rectangle(annotated_image, (x, y), (x + w, y + h), color, 2)
            cv2.rectangle(annotated_image, (x, max(0, y - 42)), (x + max(w, 240), y), color, -1)
            cv2.putText(annotated_image, status_text, (x + 5, max(15, y - 24)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.52, (255, 255, 255), 2)
            cv2.putText(annotated_image, sub_text, (x + 5, max(30, y - 6)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.42, (255, 255, 255), 1)

            # Draw 5 facial landmarks
            landmarks = [
                (int(face_info[4]), int(face_info[5])),  # Right eye
                (int(face_info[6]), int(face_info[7])),  # Left eye
                (int(face_info[8]), int(face_info[9])),  # Nose
                (int(face_info[10]), int(face_info[11])), # Right mouth
                (int(face_info[12]), int(face_info[13])), # Left mouth
            ]
            for lx, ly in landmarks:
                cv2.circle(annotated_image, (lx, ly), 3, (0, 255, 255), -1)

            calibrated_pct = self.database.calibrate_percentage(float(match_score))
            face_res = {
                "bbox": bbox,
                "detection_score": det_score,
                "liveness": {
                    "is_real": is_real,
                    "confidence": liveness_score,
                    "blur_score": liveness_res["blur_score"] if liveness_res else None,
                    "details": liveness_res
                },
                "identity": {
                    "matched": person is not None,
                    "person": person,
                    "match_score": float(match_score),
                    "match_percentage": calibrated_pct
                }
            }
            results.append(face_res)

        return {
            "success": True,
            "faces_detected": len(faces),
            "results": results,
            "annotated_image": annotated_image
        }

    def verify_user_face(
        self,
        image: np.ndarray,
        user_id: str,
        check_liveness: bool = True,
        liveness_mode: str = "low",
        threshold: float = 0.35
    ) -> dict:
        """
        Direct 1:1 Biometric Verification of a live face against a specific target user.
        Fast, robust, and specifically designed for eKYC signing gatekeepers.
        """
        if image is None or image.size == 0:
            return {"success": False, "matched": False, "message": "Hình ảnh rỗng hoặc không hợp lệ"}

        face_info, bbox = self.detector.get_dominant_face(image)
        if face_info is None:
            return {
                "success": False,
                "matched": False,
                "faces_detected": 0,
                "message": "Không tìm thấy khuôn mặt nào trước camera. Vui lòng nhìn thẳng vào webcam."
            }

        # 1. Liveness check
        liveness_res = None
        is_real = True
        liveness_score = 1.0
        if check_liveness:
            liveness_res = self.liveness.check_liveness(image, bbox, sensitivity=liveness_mode)
            is_real = liveness_res["is_real"]
            liveness_score = liveness_res["score"]

        # 2. Extract features
        aligned_face = self.recognizer.align_and_crop(image, face_info)
        embedding = self.recognizer.extract_features(aligned_face)

        # 3. 1:1 Verification
        matched, score, pct, user_info = self.database.verify_user(
            user_id, embedding, self.recognizer, threshold=threshold
        )

        # If not matched against target user_id, check best match for feedback
        alt_person, alt_score = self.database.search_best_match(embedding, self.recognizer, threshold=threshold)
        alt_pct = self.database.calibrate_percentage(alt_score)

        return {
            "success": True,
            "matched": matched,
            "faces_detected": 1,
            "bbox": bbox,
            "score": score,
            "percentage": pct,
            "user": user_info,
            "liveness": {
                "is_real": is_real,
                "score": liveness_score,
                "details": liveness_res
            },
            "alt_match": {
                "person": alt_person,
                "score": alt_score,
                "percentage": alt_pct
            }
        }

    def enroll_person(self, image: np.ndarray, name: str, id_card: str = "", department: str = "Staff", allow_lenient_liveness: bool = True) -> dict:
        """
        Enrolls a new person into the biometric database with strict quality & face checks.
        """
        if not name or len(name.strip()) < 2:
            return {"success": False, "message": "Vui lòng nhập họ và tên hợp lệ (ít nhất 2 ký tự)."}

        if image is None or image.size == 0:
            return {"success": False, "message": "Hình ảnh đăng ký không hợp lệ."}

        faces = self.detector.detect(image)
        if faces is None or len(faces) == 0:
            return {"success": False, "message": "Không phát hiện khuôn mặt rõ nét nào trong ảnh! Vui lòng nhìn thẳng vào camera ở nơi đủ sáng."}

        if len(faces) > 1:
            return {"success": False, "message": f"Phát hiện {len(faces)} khuôn mặt trong khung hình. Vui lòng chỉ có 1 người khi đăng ký danh tính!"}

        face_info = faces[0]
        bbox = [int(face_info[0]), int(face_info[1]), int(face_info[2]), int(face_info[3])]

        if bbox[2] < 40 or bbox[3] < 40:
            return {"success": False, "message": "Khuôn mặt quá nhỏ hoặc quá xa camera. Vui lòng đưa mặt lại gần hơn."}

        # Liveness check on enrollment photo
        mode = "low" if allow_lenient_liveness else "medium"
        liveness_res = self.liveness.check_liveness(image, bbox, sensitivity=mode)
        if not liveness_res["is_real"] and not allow_lenient_liveness:
            return {
                "success": False,
                "message": f"Ảnh đăng ký không vượt qua kiểm tra chống giả mạo (Độ tin cậy: {liveness_res['score']*100:.1f}%)"
            }

        aligned_face = self.recognizer.align_and_crop(image, face_info)
        embedding = self.recognizer.extract_features(aligned_face)

        # Save cropped avatar
        safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '_')).rstrip().replace(' ', '_').lower()
        if not safe_name:
            safe_name = "user"
        avatar_filename = f"avatar_{safe_name}_{int(np.random.randint(1000, 9999))}.jpg"
        avatar_path = os.path.join(self.database.avatar_dir, avatar_filename)
        cv2.imwrite(avatar_path, aligned_face)

        user_info = self.database.register(
            name=name,
            embedding=embedding,
            id_card=id_card,
            department=department,
            avatar_filename=avatar_filename
        )

        return {
            "success": True,
            "message": f"Đăng ký thành công danh tính: {user_info['name']}",
            "user": user_info
        }

    def verify_id_card_and_selfie(self, id_card_img: np.ndarray, selfie_img: np.ndarray, threshold: float = 0.35, liveness_mode: str = "low") -> dict:
        """
        1:1 eKYC verification: Compare ID card portrait with live selfie.
        """
        id_face_info, id_bbox = self.detector.get_dominant_face(id_card_img)
        if id_face_info is None:
            return {"success": False, "message": "Không tìm thấy ảnh chân dung trên thẻ CCCD/CMND"}

        selfie_face_info, selfie_bbox = self.detector.get_dominant_face(selfie_img)
        if selfie_face_info is None:
            return {"success": False, "message": "Không tìm thấy khuôn mặt trong ảnh selfie chụp thực tế"}

        # Check liveness on selfie
        liveness_res = self.liveness.check_liveness(selfie_img, selfie_bbox, sensitivity=liveness_mode)

        # Extract features from both faces
        id_aligned = self.recognizer.align_and_crop(id_card_img, id_face_info)
        id_feat = self.recognizer.extract_features(id_aligned)

        selfie_aligned = self.recognizer.align_and_crop(selfie_img, selfie_face_info)
        selfie_feat = self.recognizer.extract_features(selfie_aligned)

        similarity = self.recognizer.compute_similarity(id_feat, selfie_feat)
        verified = bool(similarity >= threshold)
        match_percentage = round(max(0.0, min(100.0, (similarity + 0.2) / 1.2 * 100)), 2)

        return {
            "success": True,
            "is_spoof": not liveness_res["is_real"],
            "verified": verified,
            "similarity": float(similarity),
            "match_percentage": match_percentage,
            "threshold": threshold,
            "liveness_confidence": float(liveness_res["score"]),
            "message": "Xác thực danh tính TRÙNG KHỚP thành công!" if verified else "Khuôn mặt selfie KHÔNG TRÙNG KHỚP với thẻ CCCD!"
        }
