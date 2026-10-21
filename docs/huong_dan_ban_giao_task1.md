# Hướng dẫn bàn giao Task 1 cho Quỳnh Hân

## Đã chuẩn bị

- `data/ports_daily.csv`: dữ liệu sạch đủ 594.720 dòng, 210 cảng/đầu mối. Giữ số 0 thật, không tự thay dữ liệu thiếu bằng 0.
- `data/selected_ports.csv`: danh sách **137 cảng ứng viên**, chọn bằng dữ liệu train 2019–2024, kèm nhóm hoạt động. Có đủ 10 quốc gia ven biển; Lào nằm ngoài bài toán cảng theo repo.
- `results/data_audit.md`: báo cáo kiểm tra dữ liệu, ngày có lượng hàng bằng 0, các chuỗi 0 kéo dài và ba biểu đồ.
- `docs/data_eda.md`: phần Data and Exploratory Analysis bằng tiếng Anh để ghép vào bài báo.
- `results/eligibility_validation.md`: so sánh hai phương án chọn cảng trên cùng 49.183 mẫu validation, kèm số liệu và giới hạn diễn giải.

Các mốc đã ghi theo xác nhận của Hân rằng Định và Hiếu cùng đồng ý: train từ 01/01/2019 đến 31/12/2024; validation cả năm 2025; test từ 01/01 đến 02/10/2026. Đồng ý mốc thời gian không được ghi thành đồng ý mọi quy tắc chọn cảng.

## Cách hiểu danh sách 137 cảng

Đây là phương án ứng viên theo gợi ý của repo: có dữ liệu hàng hóa đầy đủ trong train và ít nhất 20% ngày train có hàng, tức ít nhất 439/2.192 ngày. Không lấy tỷ lệ của cả giai đoạn 2019–2026 để chọn. Có 23 cảng hoạt động thấp, 47 trung bình và 67 cao; ranh giới nhóm là 1/3 và 2/3 số ngày train có hàng.

73 cảng còn lại vẫn nằm trong dữ liệu sạch và có lý do loại khỏi phương án này trong `results/port_selection_audit.csv`. `results/country_retention.csv` ghi từng nước giữ lại bao nhiêu cảng. Không xóa các ngày có lượng hàng bằng 0 ở 137 cảng được giữ.

Phép so sánh validation dùng một mô hình tuyến tính cố định theo protocol: phương án 20% có MAE thấp hơn khoảng **0,0143%**, trong khi RMSE nhỉnh hơn. Vì chênh lệch rất nhỏ, không viết rằng 20% đã được chứng minh tốt hơn rõ rệt. Chưa dùng năm 2026 để chấm hay chọn phương án.

## Việc cần bàn giao cho Định và Hiếu

Gửi báo cáo và cấu hình qua kênh làm việc của nhóm để hai bạn đối chiếu kết quả, tập mẫu chấm và cách xử lý thời điểm dữ liệu được công bố. Sau đó ghi nhận quyết định thật của nhóm về quy tắc chọn cảng rồi mới khóa quy tắc (`frozen: true`). Repo yêu cầu bước phối hợp này; hiện hồ sơ ghi đúng là **chờ rà soát chung**, không ghi giả rằng đã nghiệm thu hoàn toàn Task 1.

Có thể dùng nội dung sau để gửi nhóm:

> Hân đã chuẩn bị dữ liệu sạch, EDA và danh sách ứng viên theo mốc train 2019–2024, validation 2025, test 01/01–02/10/2026 mà nhóm đã thống nhất. Ngưỡng 20% trên train giữ 137/210 cảng, đủ 10 quốc gia. Đã so sánh với phương án chỉ yêu cầu đủ dữ liệu trên cùng 49.183 mẫu validation; MAE chênh rất ít và RMSE chưa cùng chiều. Nhờ Định và Hiếu đối chiếu báo cáo `results/eligibility_validation.md`, tập mẫu và quy tắc trước khi nhóm chốt danh sách cuối cùng cho Task 2.

Đây là nội dung soạn sẵn; chưa có tin nhắn nào được gửi tự động cho người khác.

## Lưu ý khi đưa lên repo

Làm việc trong thư mục `task1-han`, trên nhánh `task1-han`. Dữ liệu thô, dữ liệu sạch, bảng dự báo lớn và các bảng chi tiết đang được repo bỏ qua; không đưa chúng vào Git. Bàn giao file dữ liệu qua kênh được nhóm dùng, giữ nguyên nguồn và mã kiểm tra. Chỉ đưa mã nguồn, tài liệu và các bảng/biểu đồ nhỏ đã rà soát vào PR; cần một thành viên khác review trước khi merge vào `main`.

Phần EDA để ghép bài báo viết bằng tiếng Anh theo Task 1. Tài liệu hướng dẫn nội bộ này viết bằng tiếng Việt để Hân tiện theo dõi.
