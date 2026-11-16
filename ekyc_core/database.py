import json
import os
import uuid
import numpy as np
from datetime import datetime

class IdentityDatabase:
    def __init__(self, db_path="data/identities.json", avatar_dir="data/avatars"):
        if not os.path.isabs(db_path):
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            db_path = os.path.join(base_dir, db_path)
            avatar_dir = os.path.join(base_dir, avatar_dir)

        self.db_path = db_path
        self.avatar_dir = avatar_dir
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        os.makedirs(self.avatar_dir, exist_ok=True)

        self.identities = {}
        self.load()

    @staticmethod
    def to_public_dict(user_info: dict) -> dict:
        if not user_info:
            return None
        return {
            "id": user_info["id"],
            "name": user_info["name"],
            "id_card": user_info.get("id_card", ""),
            "department": user_info.get("department", ""),
            "created_at": user_info.get("created_at", ""),
            "avatar_file": user_info.get("avatar_file", "")
        }

    def load(self):
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.identities = {}
                    for user_id, user_info in data.items():
                        user_info["embedding_np"] = np.array(user_info["embedding"], dtype=np.float32).reshape(1, -1)
                        self.identities[user_id] = user_info
            except Exception as e:
                print(f"Error loading identity database: {e}")
                self.identities = {}
        else:
            self.identities = {}

    def save(self):
        serializable = {}
        for user_id, user_info in self.identities.items():
            serializable[user_id] = {
                "id": user_info["id"],
                "name": user_info["name"],
                "id_card": user_info.get("id_card", ""),
                "department": user_info.get("department", "Default"),
                "created_at": user_info.get("created_at", ""),
                "avatar_file": user_info.get("avatar_file", ""),
                "embedding": user_info["embedding"]
            }
        with open(self.db_path, "w", encoding="utf-8") as f:
            json.dump(serializable, f, ensure_ascii=False, indent=2)

    def register(self, name: str, embedding: np.ndarray, id_card: str = "", department: str = "General", avatar_filename: str = "") -> dict:
        name = name.strip()
        id_card = (id_card or "").strip()
        department = (department or "Chung").strip()

        # Check if user with same id_card already exists to avoid chaotic duplicates
        existing_id = None
        if id_card:
            for uid, info in self.identities.items():
                if info.get("id_card", "").strip() == id_card:
                    existing_id = uid
                    break

        user_id = existing_id if existing_id else str(uuid.uuid4())[:8]

        # Delete old avatar file if replacing
        if existing_id and self.identities[existing_id].get("avatar_file"):
            old_avatar = os.path.join(self.avatar_dir, self.identities[existing_id]["avatar_file"])
            if os.path.exists(old_avatar):
                try:
                    os.remove(old_avatar)
                except Exception:
                    pass

        emb_list = embedding.flatten().tolist()
        emb_np = np.array(emb_list, dtype=np.float32).reshape(1, -1)

        user_info = {
            "id": user_id,
            "name": name,
            "id_card": id_card,
            "department": department,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "avatar_file": avatar_filename,
            "embedding": emb_list,
            "embedding_np": emb_np
        }

        self.identities[user_id] = user_info
        self.save()
        return self.to_public_dict(user_info)

    @staticmethod
    def calibrate_percentage(cosine_score: float) -> float:
        """
        Calibrates SFace cosine similarity into an intuitive match percentage (0% to 100%)
        consistent with OpenCV SFace official threshold (0.363 -> ~75% threshold):
          score <= 0.0:   0%
          0.0 - 0.25:     0% - 45%   (Distinct / Different person / Noise)
          0.25 - 0.35:    45% - 69%  (Low similarity / Rejected)
          0.35 - 0.50:    75% - 88%  (Verified match)
          >= 0.50:        88% - 99.9% (High confidence match)
        """
        if cosine_score <= 0.0:
            return 0.0
        elif cosine_score < 0.25:
            return round((cosine_score / 0.25) * 45.0, 1)
        elif cosine_score < 0.35:
            return round(45.0 + ((cosine_score - 0.25) / 0.10) * 24.0, 1)
        elif cosine_score < 0.50:
            return round(75.0 + ((cosine_score - 0.35) / 0.15) * 13.0, 1)
        else:
            pct = 88.0 + ((cosine_score - 0.50) / 0.30) * 11.9
            return round(min(99.9, pct), 1)

    def verify_user(self, user_id: str, query_feat: np.ndarray, recognizer, threshold=0.35):
        """
        Strict 1:1 biometric verification against ONLY the targeted user_id.
        Never falls back to matching other users in the database.
        """
        target = self.identities.get(user_id)
        if not target:
            return False, 0.0, 0.0, None

        score = recognizer.compute_similarity(query_feat, target["embedding_np"])
        matched = bool(score >= threshold)
        pct = self.calibrate_percentage(score)
        return matched, float(score), pct, self.to_public_dict(target)

    def search_best_match(self, query_feat: np.ndarray, recognizer, threshold=0.35):
        """
        Performs 1:N biometric search against all registered identities using strict threshold.
        """
        if not self.identities:
            return None, 0.0

        best_person = None
        best_score = -1.0

        for user_id, user_info in self.identities.items():
            cand_feat = user_info["embedding_np"]
            score = recognizer.compute_similarity(query_feat, cand_feat)
            if score > best_score:
                best_score = score
                best_person = user_info

        if best_score >= threshold and best_person is not None:
            return self.to_public_dict(best_person), float(best_score)
        else:
            return None, float(best_score)

    def list_all(self):
        result = []
        for user_id, info in self.identities.items():
            result.append(self.to_public_dict(info))
        return result

    def delete(self, user_id: str) -> bool:
        if user_id in self.identities:
            avatar_file = self.identities[user_id].get("avatar_file", "")
            if avatar_file:
                av_path = os.path.join(self.avatar_dir, avatar_file)
                if os.path.exists(av_path):
                    try:
                        os.remove(av_path)
                    except Exception:
                        pass
            del self.identities[user_id]
            self.save()
            return True
        return False
