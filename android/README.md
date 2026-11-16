# eKYC Digital Signature Mobile - Android Edition

Ứng dụng ký số điện tử tích hợp eKYC dành riêng cho hệ điều hành Android, được đóng gói dưới định dạng tệp cài đặt `.apk`.

## 1. Thông tin tệp APK
- **Tên tệp cài đặt**: `android/eKYC_DigitalSignature.apk`
- **Package Name**: `com.ekyc.digitalsignature`
- **Target SDK**: Android 14 (API 34) | **Min SDK**: Android 8.0 (API 26)
- **Kiểu ký số APK**: `SHA256withRSA` (2048-bit RSA Release Keystore)
- **Thời hạn chứng thư số**: Đến năm 2054

## 2. Thiết kế giao diện (UI/UX)
- Giao diện được tối ưu hóa cho màn hình cảm ứng điện thoại thông minh (Responsive Touch UI).
- Tone màu chủ đạo chuyên nghiệp, tối giản:
  - **Cobalt Blue**: `#1D4ED8`
  - **Deep Slate Background**: `#0B1120` & `#0F172A`
  - **Modern Orange Accent**: `#EA580C`
  - **Emerald Success**: `#10B981`

## 3. Các lớp bảo mật chuyên sâu (Security Architecture)

### a. Cơ chế mã hóa bất đối xứng (Asymmetric Encryption - RSA PKI)
- Cấp cặp khóa RSA-2048 bit riêng cho từng định danh (User Identity).
- Khóa bí mật (Private Key) được lưu giữ trong vùng nhớ an toàn trên thiết bị và chỉ được kích hoạt khi vượt qua bước kiểm tra sinh trắc học eKYC (Face Match & Anti-spoofing).
- Quá trình ký số:
  1. Tài liệu PDF được băm với thuật toán `SHA-256`.
  2. Băm được mã hóa bằng Private Key thông qua thuật toán `SHA256withRSA` (hoặc RSA-PSS).
  3. Bất kỳ ai sở hữu Khóa công khai (Public Key) đều có thể giải mã và xác thực tính toàn vẹn.
  4. Nếu PDF bị thay đổi dù chỉ 1 byte, mã băm sẽ khác và chữ ký số sẽ lập tức báo lỗi xâm phạm (Tamper Alert).

### b. Chống dịch ngược & Che giấu mã nguồn (Anti-Reverse Engineering)
- **Mã hóa chuỗi động (String Obfuscation via XOR)**: Toàn bộ các chuỗi nhạy cảm liên quan đến đường dẫn hệ thống (`/proc/self/maps`, `/system/bin/su`, `/system/xbin/su`), cổng socket (`127.0.0.1`), công cụ dịch ngược (`frida`, `xposed`, `test-keys`) đều được lưu dưới dạng mảng byte đã mã hóa XOR (Key `0x5A`) và giải mã tại thời gian chạy (Runtime Decryption). Khi mở bằng JADX hoặc Ghidra, việc quét chuỗi ký tự thông thường sẽ không tìm thấy bất kỳ chuỗi nhạy cảm nào.
- **Khóa toàn vẹn chữ ký APK (Signature Pinning)**: Ứng dụng tự kiểm tra dấu vân tay chứng chỉ ký số của chính nó; nếu kẻ tấn công decompile APK bằng apktool, sửa đổi mã và ký lại bằng keystore khác, ứng dụng sẽ phát hiện chữ ký bị sai lệch và lập tức tự khóa.

### c. Chống can thiệp bộ nhớ & Hooking (Anti-Hooking / Anti-Frida Protection)
- **Quét bản đồ bộ nhớ tiến trình (`/proc/self/maps`)**: Ứng dụng liên tục kiểm tra các thư viện động tiêm vào bộ nhớ. Nếu phát hiện sự hiện diện của `frida-agent.so`, `frida-gadget`, `libgum`, `xposed`, hoặc `substrate`, hệ thống sẽ từ chối thực thi các hàm ký số nhạy cảm.
- **Quét cổng dịch vụ Frida (Frida Port Scanner)**: Kiểm tra trạng thái cổng TCP mặc định của Frida Server (`27042`). Nếu cổng đang mở (nghĩa là frida-server đang chạy ngầm trên thiết bị), hàm ký số lập tức chặn giao dịch.
- **Chống gắn trình gỡ lỗi (Anti-Debugging)**: Kiểm tra `Debug.isDebuggerConnected()` và cờ `TracerPid` để ngăn chặn việc attach gdb/lldb vào tiến trình.
- **Kiểm tra môi trường Root (Anti-Root)**: Kiểm tra sự tồn tại của `su` binary tại các phân vùng hệ thống (`/system/bin`, `/system/xbin`, `/sbin`) và cờ `test-keys` của các bản ROM tùy biến không an toàn.

## 4. Cách build lại hoặc kiểm tra APK
- **Tự động build & ký số**: Chạy file `android/build_apk.bat`.
- **Kiểm tra dịch ngược bằng JADX**:
  ```cmd
  C:\Tools\JADX\bin\jadx.bat -d android\jadx_output android\eKYC_DigitalSignature.apk
  ```
- **Cài đặt vào điện thoại hoặc máy ảo Android qua ADB**:
  ```cmd
  C:\Tools\platform-tools\adb.exe install -r android\eKYC_DigitalSignature.apk
  ```

