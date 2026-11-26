# Bàn giao Task 5 — Quỳnh Hân

## Phạm vi theo leader

Yêu cầu tại `docs/Task 5_Han_Dinh_Hieu.md` và mục “Task 5 handoff to Hân and Hiếu” trong `results/README.md`: Định phụ trách kiểm tra căn chỉnh/điểm số, Hiếu phụ trách hình so sánh, Hân phân tích quốc gia, nhóm hoạt động và ý nghĩa vận hành. Bản này bổ sung phần Hân trên đúng nhánh `task5-validation-evaluation`, commit `92dd5e4`, của [PR #8](https://github.com/Dingglebell/IS403.R11-maritimePortForecasting/pull/8). Các hình được chuẩn bị để Hiếu có bản cụ thể cùng review, không ghi nhận Hiếu đã duyệt.

## File cần đọc

| File | Mục đích |
|---|---|
| `docs/results_discussion.md` | Phần Results, Discussion and Operational Implications bằng tiếng Anh để ghép bài |
| `results/task5_han/tables.md` | Các bảng số liệu được tạo tự động từ kết quả Định |
| `results/task5_han/country_activity.csv` | MAE/RMSE/WAPE/bias, số mẫu và thay đổi so với naïve theo quốc gia và nhóm |
| `results/task5_han/zero_positive.csv` | So sánh riêng tuần tổng hàng bằng 0 và tuần có hàng |
| `results/task5_han/per_port.csv`, `port_summary.csv` | Kết quả từng cảng, trung vị/phân vị 90%, số cảng tốt hơn naïve và WAPE không xác định |
| `results/task5_han/country_error_contributions.csv` | Tỷ trọng tổng sai số tuyệt đối theo quốc gia; không phải tỷ trọng hàng hóa thực |
| `results/task5_han/weekly_phases.csv` | Cả bảy cách lấy mỗi ngày thứ bảy |
| `results/task5_han/*.png` | Bốn hình: tổng thể, quốc gia, nhóm hoạt động và actual/predicted tại các cảng sai số lớn |
| `results/task5_han/case_windows.csv`, `largest_errors.csv` | Các giá trị tạo hình và các cửa sổ sai số lớn, có ngày/ID để kiểm tra |
| `results/task5_han/verification.json` | Hash đầu vào và xác nhận tái tính tất cả nhóm điểm số |
| `src/report_task5_han.py` | Tạo bảng/hình và kiểm chứng kết quả; không fit hoặc tune mô hình |

Các bảng tổng, cấu hình và code Định được giữ nguyên. Dự báo đầy đủ và dữ liệu lớn nằm trong `results/task5_test/han_reproduction/` và `data/`, không đưa lên Git theo quy định repo.

## Kết luận chính để trình bày

- Trên 56.490 mẫu giống nhau, hồi quy đa biến có MAE **41.760,63 tấn/7 ngày**, giảm **19,27%** so với naïve; thấp nhất về MAE và RMSE trong sáu mô hình chính.
- RF/HGB giảm MAE nhưng RMSE cao hơn naïve. Không được kết luận chúng tốt hơn trên mọi khía cạnh.
- HGB tốt nhất về MAE ở nhóm hoạt động thấp/trung bình và tuần không có hàng; hồi quy đa biến tốt nhất ở nhóm hoạt động cao và tuần có hàng.
- Hồi quy đa biến cải thiện MAE so với naïve ở cả 10 quốc gia; HGB vẫn có MAE thấp nhất trong 6 quốc gia. Các bảng country giữ nguyên mẫu trong từng quốc gia.
- WAPE lớn tại Timor-Leste cần đọc cùng khối lượng nhỏ và MAE theo tấn; Singapore có MAE lớn nhưng WAPE thấp. WAPE không xác định khi tổng actual bằng 0.
- Hồi quy đa biến dẫn đầu cả 7 pha tuần. Không cộng các tổng 7 ngày liên tiếp thành khối lượng tuần độc lập.
- Chỉ nêu khả năng hỗ trợ lập kế hoạch nhân sự, thiết bị và bãi. Không suy ra công suất, tắc nghẽn hay tiền tiết kiệm nếu thiếu dữ liệu năng suất, tồn bãi, thời gian lưu và chi phí.

## Tái tạo

Môi trường đã kiểm tra: Python 3.12.14; các gói trong `requirements.txt`, cộng `scikit-learn==1.9.1` như freeze. Dùng bản dữ liệu sạch có SHA256 `f8c402ed90ad70d851b0cf82e4c57d1d810cc3faa3bac958efd4bf68dd96d9b6`. Bản Hân tìm lại ở Desktop khớp hash này.

```bash
python -m pip install -r requirements.txt scikit-learn==1.9.1
git archive --format=zip -o data/task34-handoff.zip 3670f89b97730b8eb12ae05050b12a0ce3d10b0e src/models.py results/model_config.json
python -m zipfile -e data/task34-handoff.zip data/task34-handoff
python src/features.py --panel data/da_xu_ly/ports_daily.csv --results-dir data/task2_reproduction
python src/run_task5_test.py --model-handoff data/task34-handoff --out-dir results/task5_test/han_reproduction
python src/report_task5_han.py --predictions results/task5_test/han_reproduction/test_predictions.csv --reference results/task5_test/han_reproduction/test_reference.csv
python -m unittest discover -s src -p 'test_*.py' -v
```

Nếu đã có bản chạy, dùng chính file dự báo/reference của bản đó ở bước tạo báo cáo; runner yêu cầu thư mục đầu ra mới để tránh ghi đè lần chạy cũ. Tái tạo dự báo chỉ dùng cấu hình đã đóng băng, không thử tham số mới theo test. Nếu có sai khác xuất CSV ở mức dấu phẩy động, script kiểm tra đủ khóa và tất cả metrics với `rtol=1e-8, atol=1e-6`; cả hash gốc và hash bản tái tạo đều được ghi, không giả vờ giống từng byte.

## Phần cần nhóm review

Hân đã chuẩn bị phần viết, bảng hỗ trợ và hình có thể tái tạo. Định review cách diễn giải điểm số và giới hạn; Hiếu review hình/caption và chọn cách đưa vào slide. Không coi bản phân tích nhóm trên test là quy tắc mới để đổi mô hình theo quốc gia/cảng. SARIMA vẫn là so sánh validation riêng 67 cảng, không ghép vào bảng test 210 cảng.

PR của Hân mở vào `main` theo quy định repo và phụ thuộc PR #8 của Định, còn mở tại thời điểm chuẩn bị. Vì nhánh Hân kế thừa bộ đánh giá này, diff vào `main` cũng chứa phần Định cho tới khi PR #8 được merge. Commit riêng của Hân chỉ bổ sung báo cáo, bảng/hình, script kiểm chứng, test và liên kết hướng dẫn; không sửa cấu hình hay điểm số đã chốt. Không tự merge hoặc sửa nhánh của leader. Cần thành viên khác review trước merge theo quy định repo; chưa ghi nhận ai đã phê duyệt.

## Kiểm tra đã thực hiện

- Tái tạo 677.880 dự báo của 12 biến thể trên cùng 56.490 mẫu mỗi biến thể.
- Căn chỉnh đầy đủ khóa/ngày/actual và đối chiếu cả 2.796 dòng metrics với kết quả đã chốt.
- Tính lại độc lập bằng tổng tích lũy từ panel sạch: nhãn 7 ngày và cả ba đặc trưng khớp trên toàn bộ 56.490 mẫu test.
- Chạy thành công 44 tests (40 tests của bộ đánh giá hiện có và 4 tests kiểm tra báo cáo).
- Kiểm tra trực quan cả bốn hình, đơn vị và caption; dữ liệu lớn vẫn được Git bỏ qua.
