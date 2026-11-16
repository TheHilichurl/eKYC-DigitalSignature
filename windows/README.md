# eKYC Digital Signature System - Windows Desktop Pro

Ứng dụng ký số văn bản PDF tích hợp định danh sinh trắc học khuôn mặt eKYC trên nền tảng Windows Desktop.

## 1. Công nghệ & Kiến trúc
- **Frontend / Window Wrapper**: Microsoft Edge WebView2 (thông qua `pywebview`), hỗ trợ tăng tốc phần cứng (DirectX), WebRTC camera trực tiếp với độ trễ thấp và HTML5 Canvas.
- **Tone màu thiết kế**: Minimalist & Professional (Cobalt Blue `#1D4ED8`, Deep Slate `#0B1120`, Amber/Orange `#EA580C`).
- **eKYC Biometrics Engine**:
  - Face Detection: YuNet ONNX (trích xuất 5 điểm mốc khuôn mặt, bounding box siêu nhanh).
  - Face Recognition: SFace ONNX (trích xuất vector đặc trưng 128 chiều, so khớp Cosine Similarity).
  - Liveness / Anti-Spoofing: Passive Fourier Texture Analysis (MultiFTNet) với 4 mức nhạy tùy chỉnh (Low/Medium/High/Off).
- **Mã hóa bất đối xứng & Ký số PDF**:
  - RSA-2048 PKI: Cặp khóa bí mật (Private Key) và công khai (Public Key).
  - Băm SHA-256 kèm đệm PSS (Probabilistic Signature Scheme - RFC 8017).
  - Đóng dấu con dấu tròn / chữ ký điện tử ảnh PNG tại đúng vị trí $(x, y, w, h)$ trên trang PDF chỉ định.
  - Chống giả mạo (Anti-Tampering): Tự động phát hiện nếu tài liệu bị thay đổi dù chỉ 1 byte.
- **Cơ sở dữ liệu cục bộ**: SQLite (`data/ekyc_pki.db`) lưu trữ chữ ký, con dấu, khóa công khai/bí mật được mã hóa và nhật ký kiểm toán (Audit Trail).

## 2. Cách khởi động ứng dụng
1. Nhấp đúp chuột vào file `run_windows.bat`.
2. Hoặc mở PowerShell/CMD tại thư mục `windows/` và chạy:
   ```cmd
   python main_desktop.py
   ```
3. Cửa sổ ứng dụng máy tính Windows sẽ xuất hiện với đầy đủ tính năng:
   - Ký số văn bản PDF kèm xác thực khuôn mặt eKYC.
   - Thư viện quản lý con dấu & chữ ký tay.
   - Kiểm tra tính toàn vẹn và chữ ký số tài liệu PDF.
   - Đăng ký danh tính mới và cấp cặp khóa RSA tự động.
   - Lịch sử nhật ký kiểm toán (Audit Trail) chống chối bỏ (Non-repudiation).

