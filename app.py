import base64
import cv2
import numpy as np
import os
import uuid
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional

from ekyc_core.engine import EkycEngine
from ekyc_core.crypto_pki import CryptoPKI
from ekyc_core.db_pki import PkiDatabase
from ekyc_core.pdf_signer import PdfSignerEngine

app = FastAPI(title="eKYC Digital Signature & Biometric System", version="2.0.0")

# Initialize Engines & Databases
engine = EkycEngine()
pki_db = PkiDatabase("data/ekyc_pki.db")

# Synchronize biometric DB and PKI DB on startup
for _uid, _info in engine.database.identities.items():
    if not pki_db.get_user(_uid):
        _priv, _pub = CryptoPKI.generate_key_pair(2048)
        pki_db.add_user(
            _uid, _info["name"], _info.get("id_card", ""), _info.get("department", "Chung"),
            [], _info.get("avatar_file", ""), _pub, _priv
        )

# Directories
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
AVATAR_DIR = os.path.join(os.path.dirname(__file__), "data", "avatars")
ASSETS_DIR = os.path.join(os.path.dirname(__file__), "data", "assets")
SAMPLES_DIR = os.path.join(os.path.dirname(__file__), "data", "samples")
SIGNED_DOCS_DIR = os.path.join(os.path.dirname(__file__), "data", "signed_docs")

os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(AVATAR_DIR, exist_ok=True)
os.makedirs(ASSETS_DIR, exist_ok=True)
os.makedirs(SAMPLES_DIR, exist_ok=True)
os.makedirs(SIGNED_DOCS_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/avatars", StaticFiles(directory=AVATAR_DIR), name="avatars")
app.mount("/assets", StaticFiles(directory=ASSETS_DIR), name="assets")
app.mount("/signed_docs", StaticFiles(directory=SIGNED_DOCS_DIR), name="signed_docs")

def decode_image_base64(b64_string: str) -> np.ndarray:
    if "," in b64_string:
        b64_string = b64_string.split(",")[1]
    img_bytes = base64.b64decode(b64_string)
    nparr = np.frombuffer(img_bytes, np.uint8)
    return cv2.imdecode(nparr, cv2.IMREAD_COLOR)

def encode_image_base64(image: np.ndarray) -> str:
    success, buffer = cv2.imencode(".jpg", image, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
    if not success:
        return ""
    b64_str = base64.b64encode(buffer).decode("utf-8")
    return f"data:image/jpeg;base64,{b64_str}"

# Models
class LiveScanRequest(BaseModel):
    image_base64: str
    target_user_id: Optional[str] = None

class ScanRequest(BaseModel):
    image_base64: str
    check_liveness: Optional[bool] = True
    liveness_mode: Optional[str] = "low"
    threshold: Optional[float] = 0.35

class EnrollRequest(BaseModel):
    image_base64: str
    name: str
    id_card: Optional[str] = ""
    department: Optional[str] = "Chung"
    allow_lenient_liveness: Optional[bool] = True

class SignDocumentRequest(BaseModel):
    user_id: str
    asset_id: str
    face_image_base64: str  # eKYC live selfie to authorize signature
    pdf_base64: Optional[str] = None  # If none, use default sample contract
    page_number: Optional[int] = 1
    pos_x: Optional[float] = 380.0
    pos_y: Optional[float] = 420.0
    width: Optional[float] = 140.0
    height: Optional[float] = 70.0

class VerifyDocumentRequest(BaseModel):
    pdf_base64: str

# Endpoints
@app.get("/")
def read_root():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))

@app.post("/api/scan_live")
def api_scan_live(req: LiveScanRequest):
    """
    Lightweight, ultra-fast endpoint for real-time webcam tracking box & face recognition feedback.
    """
    try:
        img = decode_image_base64(req.image_base64)
        if img is None:
            return {"success": False, "faces_detected": 0}

        face_info, bbox = engine.detector.get_dominant_face(img)
        if face_info is None:
            return {"success": True, "faces_detected": 0, "message": "Không phát hiện khuôn mặt"}

        h, w = img.shape[:2]

        if req.target_user_id:
            aligned_face = engine.recognizer.align_and_crop(img, face_info)
            embedding = engine.recognizer.extract_features(aligned_face)
            matched, score, pct, user_info = engine.database.verify_user(
                req.target_user_id, embedding, engine.recognizer, threshold=0.35
            )
            return {
                "success": True,
                "faces_detected": 1,
                "bbox": bbox,
                "image_width": w,
                "image_height": h,
                "matched": matched,
                "match_score": float(score),
                "match_percentage": pct,
                "user_name": user_info.get("name") if user_info else "",
                "status": "MATCHED" if matched else "MISMATCH"
            }
        else:
            aligned_face = engine.recognizer.align_and_crop(img, face_info)
            embedding = engine.recognizer.extract_features(aligned_face)
            person, score = engine.database.search_best_match(embedding, engine.recognizer, threshold=0.35)
            pct = engine.database.calibrate_percentage(score)
            return {
                "success": True,
                "faces_detected": 1,
                "bbox": bbox,
                "image_width": w,
                "image_height": h,
                "matched": person is not None,
                "match_score": float(score),
                "match_percentage": pct,
                "user_name": person.get("name") if person else "Chưa đăng ký",
                "status": "MATCHED" if person else "UNKNOWN"
            }
    except Exception as e:
        return {"success": False, "faces_detected": 0, "error": str(e)}

@app.post("/api/scan")
def api_scan(req: ScanRequest):
    try:
        img = decode_image_base64(req.image_base64)
        if img is None:
            raise HTTPException(status_code=400, detail="Không thể giải mã hình ảnh")

        res = engine.scan_and_identify(
            img, 
            check_liveness=req.check_liveness,
            liveness_mode=req.liveness_mode,
            recognition_threshold=req.threshold
        )

        annotated_b64 = ""
        if "annotated_image" in res and res["annotated_image"] is not None:
            annotated_b64 = encode_image_base64(res["annotated_image"])
            del res["annotated_image"]

        res["annotated_image_base64"] = annotated_b64
        return res
    except Exception as e:
        return {"success": False, "message": str(e)}

@app.post("/api/check_face")
def api_check_face(req: LiveScanRequest):
    """Pre-checks image quality & valid single face before enrollment."""
    try:
        img = decode_image_base64(req.image_base64)
        if img is None:
            return {"success": False, "message": "Không thể đọc tệp ảnh."}
        faces = engine.detector.detect(img)
        if faces is None or len(faces) == 0:
            return {"success": False, "faces_detected": 0, "message": "Không tìm thấy khuôn mặt hợp lệ trong ảnh!"}
        if len(faces) > 1:
            return {"success": False, "faces_detected": len(faces), "message": f"Phát hiện {len(faces)} khuôn mặt. Cần chụp riêng 1 người!"}
        
        face_info = faces[0]
        bbox = [int(face_info[0]), int(face_info[1]), int(face_info[2]), int(face_info[3])]
        if bbox[2] < 40 or bbox[3] < 40:
            return {"success": False, "faces_detected": 1, "message": "Khuôn mặt quá nhỏ. Hãy đưa lại gần camera."}

        aligned_face = engine.recognizer.align_and_crop(img, face_info)
        cropped_b64 = encode_image_base64(aligned_face)
        return {
            "success": True,
            "faces_detected": 1,
            "score": float(face_info[-1]),
            "cropped_face_base64": cropped_b64,
            "message": "Khuôn mặt hợp lệ, độ nét đạt chuẩn sinh trắc học!"
        }
    except Exception as e:
        return {"success": False, "message": str(e)}

@app.post("/api/enroll")
def api_enroll(req: EnrollRequest):
    try:
        img = decode_image_base64(req.image_base64)
        if img is None:
            raise HTTPException(status_code=400, detail="Không thể giải mã hình ảnh")

        res = engine.enroll_person(
            image=img,
            name=req.name,
            id_card=req.id_card,
            department=req.department,
            allow_lenient_liveness=req.allow_lenient_liveness
        )

        if res["success"] and "user" in res:
            user_info = res["user"]
            existing_pki = pki_db.get_user(user_info["id"])
            if existing_pki:
                priv_pem = existing_pki["private_key_pem"]
                pub_pem = existing_pki["public_key_pem"]
            else:
                priv_pem, pub_pem = CryptoPKI.generate_key_pair(2048)

            pki_db.add_user(
                user_id=user_info["id"],
                name=user_info["name"],
                id_card=user_info["id_card"],
                department=user_info["department"],
                embedding=[],
                avatar_path=user_info.get("avatar_file", ""),
                public_key_pem=pub_pem,
                private_key_pem=priv_pem
            )

        return res
    except Exception as e:
        return {"success": False, "message": str(e)}

@app.get("/api/identities")
def api_list_identities():
    return {"success": True, "identities": engine.database.list_all()}

@app.delete("/api/identities/{user_id}")
def api_delete_identity(user_id: str):
    deleted_bio = engine.database.delete(user_id)
    deleted_pki = pki_db.delete_user(user_id)
    deleted = deleted_bio or deleted_pki
    return {"success": deleted, "message": "Đã xóa danh tính & khóa RSA thành công" if deleted else "Không tìm thấy danh tính"}

@app.delete("/api/assets/{asset_id}")
def api_delete_asset(asset_id: str):
    deleted = pki_db.delete_asset(asset_id)
    return {"success": deleted, "message": "Đã xóa con dấu/chữ ký" if deleted else "Không tìm thấy tài sản"}

# Assets (Stamps & Signatures) Management
@app.get("/api/assets")
def api_list_assets():
    assets = pki_db.list_user_assets()
    return {"success": True, "assets": assets}

@app.post("/api/assets/create")
def api_create_asset(
    user_id: str = Form(...),
    asset_type: str = Form(...), # 'stamp' or 'signature'
    title: str = Form(...),
    image_base64: str = Form(...)
):
    try:
        if "," in image_base64:
            image_base64 = image_base64.split(",")[1]
        img_bytes = base64.b64decode(image_base64)
        asset_id = str(uuid.uuid4())[:8]
        filename = f"{asset_type}_{asset_id}.png"
        filepath = os.path.join(ASSETS_DIR, filename)
        with open(filepath, "wb") as f:
            f.write(img_bytes)

        pki_db.add_asset(asset_id, user_id, asset_type, title, f"/assets/{filename}")
        return {"success": True, "message": f"Đã lưu trữ {title} thành công!", "asset_id": asset_id}
    except Exception as e:
        return {"success": False, "message": str(e)}

# PDF Signing with eKYC Gatekeeper
@app.post("/api/documents/sign")
def api_sign_document(req: SignDocumentRequest):
    try:
        # 1. Biometric eKYC Verification Gatekeeper (1:1 Direct Verification)
        live_face_img = decode_image_base64(req.face_image_base64)
        if live_face_img is None:
            return {"success": False, "message": "Không đọc được hình ảnh khuôn mặt eKYC"}

        ver_res = engine.verify_user_face(live_face_img, req.user_id, check_liveness=True, liveness_mode="low", threshold=0.35)
        if not ver_res["success"] or ver_res["faces_detected"] == 0:
            return {"success": False, "message": "eKYC Thất bại: Không phát hiện khuôn mặt người ký trước camera"}

        if not ver_res["matched"]:
            alt = ver_res.get("alt_match", {})
            alt_p = alt.get("person")
            if alt_p:
                hint = f"Hệ thống phát hiện bạn là '{alt_p['name']}' ({alt.get('percentage')}%), không phải người ký đã chọn."
            else:
                hint = f"Độ khớp sinh trắc học chỉ đạt {ver_res.get('percentage')}% (yêu cầu >= 75%)."
            return {
                "success": False,
                "message": f"Từ chối ký số: Khuôn mặt người trước camera không khớp với chủ sở hữu chữ ký/con dấu đã chọn. {hint}"
            }

        matched_user = ver_res.get("user") or {}

        # 2. Retrieve User PKI Keys & Asset
        user_pki = pki_db.get_user(req.user_id)
        if not user_pki:
            # Fallback create keypair if registered before
            priv_pem, pub_pem = CryptoPKI.generate_key_pair(2048)
            pki_db.add_user(
                user_id=matched_user["id"],
                name=matched_user["name"],
                id_card=matched_user.get("id_card", ""),
                department=matched_user.get("department", ""),
                embedding=[],
                avatar_path=matched_user.get("avatar_file", ""),
                public_key_pem=pub_pem,
                private_key_pem=priv_pem
            )
            user_pki = pki_db.get_user(req.user_id)

        # Retrieve Asset Image
        assets = [a for a in pki_db.list_user_assets(req.user_id) if a["id"] == req.asset_id]
        if not assets:
            # Fallback default sample stamp/signature
            stamp_path = os.path.join(SAMPLES_DIR, "sample_stamp.png")
        else:
            stamp_rel = assets[0]["image_path"].replace("/assets/", "")
            stamp_path = os.path.join(ASSETS_DIR, stamp_rel)

        # 3. Source PDF
        doc_id = str(uuid.uuid4())[:8]
        if req.pdf_base64:
            if "," in req.pdf_base64:
                req.pdf_base64 = req.pdf_base64.split(",")[1]
            input_pdf_bytes = base64.b64decode(req.pdf_base64)
            input_pdf_path = os.path.join(SIGNED_DOCS_DIR, f"temp_input_{doc_id}.pdf")
            with open(input_pdf_path, "wb") as f:
                f.write(input_pdf_bytes)
        else:
            input_pdf_path = os.path.join(SAMPLES_DIR, "sample_contract.pdf")

        output_pdf_filename = f"signed_doc_{matched_user['name'].replace(' ', '_').lower()}_{doc_id}.pdf"
        output_pdf_path = os.path.join(SIGNED_DOCS_DIR, output_pdf_filename)

        # 4. Stamp & Sign PDF
        sign_res = PdfSignerEngine.stamp_and_sign_pdf(
            input_pdf_path=input_pdf_path,
            output_pdf_path=output_pdf_path,
            stamp_image_path=stamp_path,
            page_num=req.page_number or 1,
            x_pt=req.pos_x,
            y_pt=req.pos_y,
            width_pt=req.width,
            height_pt=req.height,
            signer_name=matched_user["name"],
            private_pem=user_pki["private_key_pem"],
            public_pem=user_pki["public_key_pem"],
            id_card=matched_user.get("id_card", ""),
            audit_note=f"Xác thực sinh trắc học eKYC thành công lúc {sign_res if False else ''}"
        )

        pki_db.record_signed_document(
            doc_id=sign_res["doc_id"],
            user_id=req.user_id,
            doc_name=output_pdf_filename,
            orig_path=input_pdf_path,
            signed_path=f"/signed_docs/{output_pdf_filename}",
            orig_sha=sign_res["original_sha256"],
            signed_sha=sign_res["signed_sha256"],
            sig_hex=sign_res["crypto_signature_hex"],
            page=req.page_number or 1,
            x=req.pos_x,
            y=req.pos_y,
            w=req.width,
            h=req.height
        )

        with open(output_pdf_path, "rb") as f_out:
            signed_pdf_b64 = "data:application/pdf;base64," + base64.b64encode(f_out.read()).decode("utf-8")

        return {
            "success": True,
            "message": f"Ký số thành công tài liệu cho {matched_user['name']}!",
            "doc_id": sign_res["doc_id"],
            "download_url": f"/signed_docs/{output_pdf_filename}",
            "signed_sha256": sign_res["signed_sha256"],
            "crypto_signature_hex": sign_res["crypto_signature_hex"][:32] + "...",
            "signer": matched_user,
            "signed_pdf_base64": signed_pdf_b64
        }
    except Exception as e:
        return {"success": False, "message": str(e)}

@app.post("/api/documents/verify")
def api_verify_document(req: VerifyDocumentRequest):
    try:
        if "," in req.pdf_base64:
            req.pdf_base64 = req.pdf_base64.split(",")[1]
        pdf_bytes = base64.b64decode(req.pdf_base64)
        temp_verify_path = os.path.join(SIGNED_DOCS_DIR, f"temp_verify_{uuid.uuid4().hex[:8]}.pdf")
        with open(temp_verify_path, "wb") as f:
            f.write(pdf_bytes)

        # Check in DB by SHA-256
        sha256_hash = CryptoPKI.calculate_sha256(pdf_bytes)
        signed_docs = pki_db.list_signed_documents()
        matched_doc = next((d for d in signed_docs if d["signed_sha256"] == sha256_hash), None)

        manifest = None
        if matched_doc:
            manifest = {
                "crypto_signature_hex": matched_doc["crypto_signature_hex"],
                "public_key_pem": matched_doc["public_key_pem"],
                "signed_sha256": matched_doc["signed_sha256"],
                "signer_name": matched_doc["signer_name"],
                "id_card": matched_doc["id_card"],
                "signed_at": matched_doc["signed_at"]
            }

        res = PdfSignerEngine.verify_signed_pdf(temp_verify_path, manifest_data=manifest)
        if os.path.exists(temp_verify_path):
            os.remove(temp_verify_path)

        return res
    except Exception as e:
        return {"valid": False, "message": str(e)}

@app.get("/api/documents")
def api_list_signed_documents():
    return {"success": True, "documents": pki_db.list_signed_documents()}

@app.get("/api/samples")
def api_list_samples():
    samples = []
    if os.path.exists(SAMPLES_DIR):
        for f in os.listdir(SAMPLES_DIR):
            if f.lower().endswith((".jpg", ".jpeg", ".png")):
                is_fake = "fake" in f.lower()
                name_clean = f.replace("-", " ").replace(".jpg", "").replace(".png", "").title()
                samples.append({
                    "filename": f,
                    "title": name_clean,
                    "is_fake": is_fake,
                    "url": f"/api/sample/{f}"
                })
    return {"success": True, "samples": samples}

@app.get("/api/sample/{filename}")
def api_get_sample(filename: str):
    file_path = os.path.join(SAMPLES_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File không tồn tại")
    return FileResponse(file_path)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=False)
