# Bước 3 — Fit four baselines (Hiếu)

Ngày kiểm tra: 10/11/2026. Phạm vi: baseline và validation; chưa chốt quy tắc chung ở bước 4.

## Phần Định đã bàn giao

`src/features.py` đã có code tạo đặc trưng và chia train/validation. Định cũng đã đưa vào `src/baselines.py`, pipeline và bảng kết quả validation. Vì vậy bước 3 tiếp tục kiểm tra và tái lập code hiện có, không cần viết lại bốn mô hình.

Hiếu đã cung cấp thư mục `task2_step2/`, gồm `learning_table.csv`, dữ liệu 35 ngày tính tay và các báo cáo bàn giao. Hash bảng học khớp bản ghi của Định: `d54d3cbe252556c79f10a17cb376b376b9918f72c546d0980471c1ef16f58c5a`. Thư mục này được loại khỏi Git theo quy tắc dữ liệu lớn của repo.

## Định nghĩa đã kiểm tra trong code

| Mô hình | Đầu vào / công thức |
|---|---|
| Seasonal naïve | Dự báo bằng `cargo_7d`, không có hệ số cần huấn luyện |
| Linear univariate | Intercept + `cargo_7d` |
| Linear multivariate | Intercept + `cargo_7d`, `calls_7d`, `cargo_mean_28d` |
| Polynomial degree 2 | Intercept + `cargo_7d` + bình phương của nó |

Ba hồi quy dùng OLS gộp các cảng, fit hệ số và chuẩn hóa chỉ trên train. Bậc 2 dùng biến đã chuẩn hóa rồi bình phương để ổn định số học. Các mô hình dự báo cùng các khóa cảng/ngày và cùng nhãn tổng hàng hóa 7 ngày tới. Không fit trên nhãn validation.

Baseline runner đã được bổ sung kiểm tra ngày dự báo không sớm hơn lịch sử 28 ngày và phải ở đầu ngày. Khi chạy CLI riêng, runner ghi `results/baseline_run.json`: hash bảng học, cấu hình, code và các file đầu ra, số mẫu, phiên bản thư viện, quy tắc clipping. Bản ghi này chỉ được tạo khi thật sự chạy; không dùng nó để thay thế bản ghi pipeline cũ.

## Kết quả chạy lại trên bảng học Định bàn giao

Ngày 10/11/2026 đã chạy lại cả bốn baseline bằng bảng học thật: 453.180 mẫu train, 75.390 mẫu validation mỗi mô hình và 210 cảng. Kết quả khớp lần chạy trước với sai số tương đối cho phép 1e-12. Bản ghi mới nằm ở `results/baseline_run.json`, bằng chứng đối chiếu ở `results/baseline_review.json`, hệ số và chuẩn hóa ở `results/baseline_fits.json`.

| Mô hình | MAE gốc (tấn) | MAE chặn dưới 0 (tấn) |
|---|---:|---:|
| Seasonal naïve | 51.627,80 | 51.627,80 |
| Linear univariate | 51.926,57 | 51.926,57 |
| Linear multivariate | 41.212,07 | 41.100,62 |
| Polynomial degree 2 | 52.369,56 | 52.369,56 |

Multivariate có MAE thấp nhất trong bảng validation đã lưu. Bản gốc có 14.846/75.390 dự báo âm; chặn tại 0 giảm MAE khoảng 111,45 tấn. Hai hồi quy còn lại không vượt naïve về MAE. Không suy ra kết luận test từ bảng này.

## Tái lập phần của Hiếu

Từ thư mục gốc repo, dùng Python với các phiên bản trong `requirements.txt`:

```bash
python -m unittest discover -s src -p 'test_task2.py' -v
python src/baselines.py --table task2_step2/learning_table.csv
```

Nếu chỉ nhận clean panel, chạy pipeline có kiểm tra hash snapshot:

```bash
python src/run_task2.py --panel data/da_xu_ly/ports_daily.csv
```

Lệnh baseline riêng xuất dự báo gốc, dự báo không âm, `validation_predictions.csv`, `baseline_metrics.csv`, `baseline_fits.json`, `baseline_validation.md` và `baseline_run.json`. Khi cấu hình clipping là null, file dự báo làm việc giữ bản gốc; cả hai biến thể vẫn được xuất để thảo luận.

## Kiểm chứng ngày 10/11 và việc còn lại

- 13 kiểm thử Task 2 chạy đạt trên dữ liệu tổng hợp, gồm ví dụ tính tay, khôi phục hàm hồi quy đã biết, cùng khóa đánh giá, không dùng nhãn validation để fit, xuất CSV và kiểm tra hash đầu ra, MAE/RMSE/WAPE tính lại độc lập và hai biến thể clipping.
- 7 kiểm thử làm sạch dữ liệu chạy đạt. Bộ test Task 1 chưa chạy được trong môi trường này vì thiếu `matplotlib`; không ghi nhận toàn bộ suite đạt.
- Đã tái lập dự báo thật, đối chiếu cùng khóa/nhãn cho cả bốn mô hình, tính lại MAE/RMSE/WAPE từ CSV dự báo và kiểm tra bản không âm bằng max(dự báo gốc, 0). Các thiết kế hồi quy đều đủ hạng: 2, 4 và 3.
- Đã tính lại trực tiếp ví dụ Hải Phòng từ 35 ngày được cung cấp, theo ngày lịch: cargo 7 ngày = 332.293 tấn, calls = 148, mean 28 ngày = 49.044,892857 tấn/ngày, target = 365.344 tấn. Bốn số khớp learning table; hash khóa validation khớp Task 1. Chưa tái dựng toàn bộ đặc trưng từ clean panel vì thư mục bàn giao chỉ chứa bảng học và mẫu 35 ngày.
- Chưa có xác nhận của Định về phần review chéo. Các kiểm tra trên là kiểm chứng bằng code, không tự ghi nhận phê duyệt cá nhân của Hiếu hay Định.
- Cùng Định chốt tập cảng và clipping ở bước 4, rồi cập nhật cấu hình và chạy lại. Tài liệu review này không thay cho quyết định chung.
