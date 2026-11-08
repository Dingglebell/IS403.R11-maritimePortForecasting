# Bàn giao Task 1 — Quỳnh Hân

## Các sản phẩm đã chuẩn bị

| Sản phẩm | Vị trí | Nội dung |
|---|---|---|
| Dữ liệu sạch | `data/ports_daily.csv` — lưu trên máy | 594.720 dòng, 210 mã cảng/terminal; giữ số 0 và lịch ngày đầy đủ |
| Từ điển dữ liệu | `data/data_dictionary.md` | Toàn bộ 29 cột gốc, 7 cột sạch, mã quốc gia, đơn vị, quy tắc xử lý và các cột chọn cảng |
| Danh sách cảng | `data/selected_ports.csv` — lưu trên máy | 210 mã đề xuất giữ; có cờ cho phương án 137 mã đạt ngưỡng 20% và nhóm hoạt động chỉ tính từ train |
| Tên cảng và nguồn | `data/ports_metadata.csv`, `data/source_manifest.csv` | Tên nguồn, hash, ngày kiểm tra và URL nguồn ổn định |
| Báo cáo kiểm tra | `results/data_audit.md` | Trùng lặp, lịch ngày, giá trị thiếu/sai, số 0, chuỗi số 0 dài, đối chiếu các cột tổng |
| Đánh giá số 0 | `docs/zero_handling.md`, `results/zero_validation.md` | Thiết kế, kết quả, ngoại lệ, kiểm tra độ ổn định và giới hạn |
| Phần viết bài | `docs/data_eda.md` | Phần Data and Exploratory Analysis bằng tiếng Anh, có bảng và hình |
| Biểu đồ | `results/figures/` | Lịch sử khối lượng, tần suất hoạt động, cargo–calls và so sánh xử lý số 0 |
| Python | `src/prepare_data.py`, `src/analyze_task1.py` | Làm sạch và tái tạo kiểm toán/đánh giá; không thay thế bộ mô hình chính của Task 2 |

## Kết luận sử dụng

Giữ số 0 là phương án đề xuất cho dữ liệu bàn giao. Trên cùng 75.390 mẫu validation năm 2025, hồi quy với dự báo không âm có MAE **41.100,62 tấn** khi giữ số 0; **41.699,90 tấn** khi bỏ mẫu train có tổng 7 ngày bằng 0; **60.426,61 tấn** khi thay số 0 trong lịch sử bằng trung bình các giá trị dương quá khứ. Hai phương án can thiệp làm MAE tăng lần lượt **1,46%** và **47,02%**. Có ngoại lệ theo quốc gia; không được viết rằng mọi cảng đều hưởng lợi hoặc mọi số 0 đều chính xác về mặt vật lý.

Không xóa các ngày số 0 trước khi tạo cửa sổ: khi đó 7 dòng có thể không còn là 7 ngày. Không dùng giá trị tương lai để thay số 0. Không đổi nhãn thực hoặc bỏ những tuần có tổng bằng 0 khỏi tập chấm điểm.

Ngưỡng 20% chỉ cải thiện MAE khoảng **0,027% trên cùng nhóm 137 cảng**, trong khi loại 73 mã. Bộ bàn giao đề xuất giữ 210 mã có dữ liệu train đầy đủ và ghi riêng phương án 20% để nhóm duyệt. Đây là lựa chọn có cân nhắc phạm vi quốc gia; không phải tuyên bố 210 mã cho MAE thấp nhất trên nhóm 137 mã.

## Chạy lại

Tại thư mục gốc repo, với Python 3.12.14:

```bash
python -m pip install -r requirements.txt
python src/prepare_data.py --input-dir data/raw/hdx_2026-10-18 --output data/ports_daily.csv
python -m unittest discover -s src -p 'test_*.py' -v
python src/analyze_task1.py --raw-dir data/raw/hdx_2026-10-18
```

Trên máy Hân có thể thay `python` bằng `.venv/Scripts/python.exe`. Dữ liệu phải là bản đã đóng băng, kèm `snapshot.json` gốc; file tải mới từ nguồn có thể đã đổi. Một lần chạy tái tạo bảng, hình, danh sách cảng và dự báo validation; bài viết diễn giải được biên tập riêng và cần cập nhật nếu đổi dữ liệu/quy tắc.

`experiment.json` là cấu hình dùng chung; `results/task1_run.json` là bản ghi chạy gọn (hash, phiên bản, hệ số). Hai file có mục đích riêng, không phải dữ liệu thừa. JSON nguồn nằm cùng bản raw để kiểm chứng xuất xứ và không đưa lên GitHub. Các bảng dự báo/khóa/loại mẫu lớn cũng chỉ lưu trên máy. GitHub hiển thị code, tài liệu, bảng kiểm tra nhỏ và hình cần cho bàn giao.

## Việc cần nhóm xác nhận khi nhận bàn giao

Phần triển khai và phân tích của Hân đã được chuẩn bị, nhưng **chưa được coi là nhóm đã duyệt**. Định/Hiếu cần xem lại cùng khóa chấm điểm, chấp thuận phạm vi cảng và giả định dữ liệu có sẵn đến ngày dự báo, rồi chốt quy tắc trước test. Không có dữ liệu thời điểm công bố lịch sử để khẳng định đây là mô phỏng vận hành thời gian thực. PR cần một thành viên khác review theo quy định repo; chưa tự merge.

Task 2 tiếp tục bộ đặc trưng và bốn baseline chính; Task 3 kiểm tra RF/HGB; Task 5 đánh giá test sau khi chốt. Những việc này không được ghi nhận là đã hoàn thành trong Task 1. Bộ test hiện có **17 kiểm tra đã chạy đạt**, bao gồm biên thời gian, không dùng tương lai, nhãn giữ nguyên và phân biệt thiếu với số 0.
