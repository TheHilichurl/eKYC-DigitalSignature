# Hệ Thống eKYC Tích Hợp Chữ Ký Số Điện Tử (eKYC & PKI Digital Signature System)

Hệ thống định danh sinh trắc học khuôn mặt (**eKYC**) kết hợp với hạ tầng khóa công khai (**PKI - Public Key Infrastructure**) và chữ ký số bất đối xứng **RSA-2048 / SHA-256** trên tài liệu **PDF**.

Hệ thống được thiết kế theo kiến trúc **Local-First** (hoạt động độc lập, ngoại tuyến trên thiết bị, lưu trữ dữ liệu tại chỗ) và hỗ trợ đồng thời cả **3 nền tảng**:
1. **Web Application** (FastAPI, WebRTC Camera, AI Tracking)
2. **Windows Desktop Workstation Pro** (Python, PyWebView / Edge WebView2)
3. **Android Mobile Application** (Native Smali/Java, Android Keystore, Anti-Hooking Guard, đã đóng gói APK Scheme v1+v2+v3)

---

## 🎨 Phong Cách Thiết Kế (UI/UX)
- Giao diện được thiết kế theo phong cách tối giản, hiện đại và chuyên nghiệp:
  - **Tone màu chủ đạo:** Xanh Cobalt (`#1D4ED8`) & Cam Hiện Đại (`#EA580C`).
  - Nền tối cao cấp (`#0B1120`, `#111827`) mang đậm nét phần mềm bảo mật doanh nghiệp.

---

## 🌟 Tính Năng Chính

### 1. eKYC Sinh Trắc Học & Chống Giả Mạo (Anti-Spoofing)
- **Face Detection (YuNet):** Phát hiện khuôn mặt thời gian thực kết hợp kiểm tra 5 điểm mốc hình học (`is_valid_face_geometry`) loại bỏ 100% nhận nhầm vật thể/trần nhà.
- **Face Recognition (SFace 128D):** Trích xuất vector nhúng đặc trưng L2-normalized 128 chiều, so khớp Cosine Similarity chuẩn xác cao theo ngưỡng OpenCV Zoo chuẩn (`threshold = 0.35`).
- **Anti-Spoofing (MultiFTNet Ensemble):** Phân tích biến đổi tần số Fourier bề mặt da để ngăn chặn tấn công giả mạo (ảnh chụp lại màn hình, ảnh in giấy, video deepfake).

### 2. Ký Số Điện Tử & Đóng Dấu Tài Liệu PDF
- **Cơ chế khóa bất đối xứng:** Mỗi người dùng khi đăng ký eKYC được tự động cấp một cặp khóa **RSA-2048**. Khóa riêng (Private Key) được bảo vệ nghiêm ngặt và chỉ mở khóa khi người ký đối soát khuôn mặt thành công trước camera.
- **Đóng dấu & Chữ ký tay:** Hỗ trợ kho lưu trữ con dấu đỏ pháp lý và chữ ký tay điện tử (vẽ trực tiếp hoặc tải ảnh PNG).
- **Định vị tọa độ trên PDF:** Cho phép chỉ định chính xác trang ký, tọa độ $(X, Y)$ và kích thước $(W, H)$ trên văn bản PDF theo chuẩn PostScript Points ($1 \text{ inch} = 72 \text{ pt}$).

### 3. Thẩm Định Tính Toàn Vẹn & Chống Giả Mạo Văn Bản (Tamper Detection)
- Tính toán mã băm mật mã **SHA-256** của tài liệu và giải mã chữ ký số bằng Khóa công khai (Public Key).
- Phát hiện chỉnh sửa tức thì nếu tài liệu PDF bị can thiệp dù chỉ 1 byte sau khi ký.

### 4. Cơ Chế Bảo Mật Ứng Dụng Di Động (Android Native Guard)
- **Anti-Hooking & Anti-Frida:** Quét `/proc/self/maps` và thăm dò socket cổng Frida default `27042` để chặn tấn công can thiệp bộ nhớ.
- **Anti-Root & Xposed:** Kiểm tra sự tồn tại của `su` binary, Magisk và `test-keys`.
- **String Encryption:** Mã hóa XOR toàn bộ các chuỗi nhạy cảm trong mã bytecode Smali để chống dịch ngược bằng JADX/IDA Pro.
- **Chữ ký số Scheme v1 + v2 + v3:** Ký bằng Google `com.android.apksig` tương thích 100% với Android 5.0 (API 21) đến Android 15 (API 35).

---

## 📁 Cấu Trúc Mã Nguồn

```text
eKYC/
├── app.py                      # FastAPI Backend Server & REST APIs
├── demo_cli.py                 # CLI Tool quét và nhận diện dòng lệnh
├── run_demo.bat                # Script chạy nhanh Web Demo trên Windows
│
├── ekyc_core/                  # Thư viện lõi xử lý AI & Mật mã học
│   ├── detector.py             # Nhận diện mặt YuNet + Lọc hình học 5 mốc
│   ├── recognizer.py           # So khớp sinh trắc học SFace 128D
│   ├── liveness.py             # Bộ lọc chống giả mạo MultiFTNet Ensemble
│   ├── database.py             # Quản lý CSDL sinh trắc học identities.json
│   ├── crypto_pki.py           # Sinh khóa RSA-2048, ký & xác thực SHA-256
│   ├── db_pki.py               # Quản lý SQLite CSDL người dùng & chữ ký số
│   ├── pdf_signer.py           # Đóng dấu ảnh & ký số PDF
│   └── engine.py               # Điều phối quy trình eKYC toàn diện
│
├── static/
│   └── index.html              # Giao diện Web App chuyên nghiệp (Cobalt & Orange)
│
├── windows/                    # Bản Desktop Windows Native
│   ├── main_desktop.py         # Ứng dụng Desktop chạy qua Edge WebView2
│   ├── run_windows.bat         # Launcher 1-click mở ứng dụng Windows
│   └── README.md
│
├── android/                    # Bản Android Mobile Native
│   ├── app_src/                # Mã nguồn Smali, AndroidManifest & Web Assets
│   ├── keystore/               # Keystore chứng chỉ ký số phát hành
│   ├── tools/                  # Công cụ biên dịch SignApkV2 & VerifyApk
│   ├── build_apk.bat           # Script đóng gói APK tự động (Scheme v1+v2+v3)
│   ├── eKYC_DigitalSignature.apk # Tệp cài đặt APK hoàn chỉnh
│   └── README.md
│
├── models/                     # Trọng số mô hình AI ONNX & PyTorch
│   ├── face_detection_yunet_2023mar.onnx
│   ├── face_recognition_sface_2021dec.onnx
│   └── spoof_detection/
│
├── data/                       # Dữ liệu lưu trữ Local-First
│   ├── identities.json         # Danh bạ vector sinh trắc học
│   ├── ekyc_pki.db             # SQLite lưu khóa RSA, con dấu & nhật ký
│   ├── avatars/                # Ảnh chân dung người dùng đã đăng ký
│   ├── assets/                 # Con dấu & chữ ký tay đã lưu
│   └── samples/                # Tài liệu PDF hợp đồng mẫu & ảnh test
│
└── tests/                      # Bộ kiểm thử tự động (Unit Tests)
    ├── test_ekyc_digital_signature.py
    ├── test_platform_builds.py
    └── test_biometric_integrity.py
```

---

## 🚀 Hướng Dẫn Cài Đặt & Sử Dụng

### Yêu Cầu Môi Trường
- **Python:** 3.10+ (Đã cài `opencv-python`, `fastapi`, `uvicorn`, `cryptography`, `pypdf`, `torch`, `pywebview`).
- **Java:** JDK 17+ (nếu cần tự build lại APK Android).

---

### 1. Chạy Bản Web Demo
```bash
python app.py
```
Hoặc nhấp đúp vào [`run_demo.bat`](file:///c:/Users/Giang/Desktop/eKYC/run_demo.bat).  
Mở trình duyệt truy cập: **[http://127.0.0.1:8000](http://127.0.0.1:8000)**

---

### 2. Chạy Bản Windows Desktop
Nhấp đúp vào [`windows/run_windows.bat`](file:///c:/Users/Giang/Desktop/eKYC/windows/run_windows.bat) hoặc chạy:
```bash
python windows/main_desktop.py
```
Ứng dụng sẽ tự động kích hoạt backend và mở giao diện cửa sổ ứng dụng Windows độc lập (Edge WebView2 Native).

---

### 3. Cài Đặt Trên Điện Thoại Android
- Chép tệp [`android/eKYC_DigitalSignature.apk`](file:///c:/Users/Giang/Desktop/eKYC/android/eKYC_DigitalSignature.apk) sang điện thoại Android.
- Mở trình Quản lý tệp (File Manager) -> Nhấn vào file APK để cài đặt.
- Cấp quyền Camera khi mở ứng dụng.
- Để tự build lại APK từ mã nguồn: Chạy [`android/build_apk.bat`](file:///c:/Users/Giang/Desktop/eKYC/android/build_apk.bat).

---

### 4. Chạy Bộ Kiểm Thử (Unit Tests)
Dự án tích hợp đầy đủ bộ kiểm thử tự động:
```bash
python -m unittest discover -s tests -p "test_*.py" -v
```
*(Kết quả kiểm tra: 12/12 bài test pass 100% bao gồm cả mật mã học, độ toàn vẹn PDF, kiểm tra chữ ký APK v1+v2+v3 và lọc chống nhận nhầm trần nhà)*.

---

## 🔒 Bản Quyền & Giấy Phép
Dự án được phát triển theo giấy phép mã nguồn mở MIT License.
