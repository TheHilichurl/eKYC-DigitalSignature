import argparse
import cv2
import os
import sys
from ekyc_core.engine import EkycEngine

def main():
    parser = argparse.ArgumentParser(description="eKYC Face Scanning & Identification CLI Demo")
    parser.add_argument("--scan", type=str, help="Đường dẫn ảnh cần quét mặt & nhận diện")
    parser.add_argument("--enroll", type=str, help="Đường dẫn ảnh để đăng ký danh tính mới")
    parser.add_argument("--name", type=str, help="Tên người cần đăng ký (kèm --enroll)")
    parser.add_argument("--idcard", type=str, default="", help="Số CCCD/CMND (kèm --enroll)")
    parser.add_argument("--liveness", type=str, default="low", choices=["low", "medium", "high", "off"], help="Độ nhạy chống giả mạo (low = thân thiện webcam, medium = tiêu chuẩn, high = nghiêm ngặt, off = tắt)")
    parser.add_argument("--list", action="store_true", help="Liệt kê danh sách hồ sơ sinh trắc học đã đăng ký")
    parser.add_argument("--webcam", action="store_true", help="Chạy quét trực tiếp bằng Webcam với cửa sổ hiển thị OpenCV")
    args = parser.parse_args()

    engine = EkycEngine()

    if args.list:
        people = engine.database.list_all()
        print("\n================== CƠ SỞ DỮ LIỆU SINH TRẮC HỌC ==================")
        print(f"Tổng số hồ sơ: {len(people)}")
        for idx, p in enumerate(people, 1):
            print(f"[{idx}] ID: {p['id']} | Tên: {p['name']} | CCCD: {p.get('id_card', 'N/A')} | Tạo lúc: {p.get('created_at', 'N/A')}")
        print("=================================================================\n")
        return

    if args.enroll:
        if not args.name:
            print("[LỖI] Vui lòng cung cấp --name khi sử dụng --enroll")
            return
        img = cv2.imread(args.enroll)
        if img is None:
            print(f"[LỖI] Không thể đọc ảnh từ: {args.enroll}")
            return
        res = engine.enroll_person(img, name=args.name, id_card=args.idcard, allow_lenient_liveness=(args.liveness in ["low", "off"]))
        if res["success"]:
            print(f"[THÀNH CÔNG] {res['message']} (User ID: {res['user']['id']})")
        else:
            print(f"[THẤT BẠI] {res['message']}")
        return

    if args.scan:
        img = cv2.imread(args.scan)
        if img is None:
            print(f"[LỖI] Không thể đọc ảnh từ: {args.scan}")
            return
        print(f"\n[*] Đang quét khuôn mặt từ file: {args.scan} (Chế độ Liveness: {args.liveness})...")
        res = engine.scan_and_identify(img, check_liveness=(args.liveness != "off"), liveness_mode=args.liveness)
        print(f"[+] Số khuôn mặt phát hiện: {res['faces_detected']}")
        for idx, face in enumerate(res["results"], 1):
            live = face["liveness"]
            ident = face["identity"]
            print(f"\n--- Khuôn Mặt #{idx} ---")
            print(f"  Vị trí (bbox): {face['bbox']}")
            print(f"  Liveness (Mặt thật?): {'ĐÚNG (Mặt thật)' if live['is_real'] else 'SAI (NGHI VẤN GIẢ MẠO / ÁNH SÁNG KÉM!)'}")
            print(f"  Độ tin cậy: {live['confidence']*100:.2f}%")
            if live.get("details") and live["details"].get("raw_scores"):
                raw = live["details"]["raw_scores"]
                print(f"  Phân bố xác suất: Mặt thật={raw['real_1']*100:.1f}%, Ảnh in={raw['fake_0']*100:.1f}%, Màn hình={raw['fake_2']*100:.1f}%")

            if ident["matched"]:
                person = ident["person"]
                status_str = "HỢP LỆ" if live["is_real"] else "CẢNH BÁO ÁNH SÁNG/MÀN HÌNH"
                print(f"  Nhận diện: TRÙNG KHỚP DANH TÍNH [{status_str}]")
                print(f"    - Họ và tên: {person['name']}")
                print(f"    - Số CCCD: {person.get('id_card', 'Chưa có')}")
                print(f"    - Độ tương đồng sinh trắc học: {ident['match_percentage']}%")
            else:
                print(f"  Nhận diện: NGƯỜI LẠ (Chưa có trong CSDL)")
                print(f"    - Độ trùng khớp cao nhất: {ident['match_percentage']}%")

        output_path = "output_scan_result.jpg"
        cv2.imwrite(output_path, res["annotated_image"])
        print(f"\n[+] Đã lưu ảnh kết quả trực quan hóa tại: {output_path}")
        return

    if args.webcam:
        print(f"\n[*] Đang khởi động Webcam (Chế độ Liveness: {args.liveness})... Nhấn phím 'q' trên cửa sổ video để thoát.")
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("[LỖI] Không thể mở webcam trên thiết bị này.")
            return

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            res = engine.scan_and_identify(frame, check_liveness=(args.liveness != "off"), liveness_mode=args.liveness)
            disp_frame = res.get("annotated_image", frame)

            cv2.imshow("eKYC Biometric Live Scanner (Nhan Q de thoat)", disp_frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()
        return

    parser.print_help()

if __name__ == "__main__":
    main()
