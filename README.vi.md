# Olist E-commerce Analytics

[English](README.md) · [Tiếng Việt](README.vi.md)

Phân tích doanh thu, giao hàng và mua lại từ dữ liệu Olist. Python xử lý dữ liệu; SQL Server lưu mô hình quan hệ; Next.js và Power BI trình bày kết quả.

![Báo cáo giao hàng với bộ lọc tháng, bang và nhóm hàng](assets/delivery-preview.png)

Ảnh chụp báo cáo Next.js đang chạy. Phạm vi trong ảnh là các đơn đã giao được quan sát đến **31/08/2018**.

## Kết quả giao hàng và mua lại

- **96.411** đơn đã giao trước ngày chốt; **6.475 / 96.411 đơn (6,72%)** giao trễ.
- Review trung bình **2,27/5** ở nhóm giao trễ (**6.306** đơn có review), so với **4,29/5** ở nhóm đúng hẹn (**88.818** đơn).
- Mua lại trong 90 ngày: **1.418 / 70.002 khách (2,03%)** sau đơn đầu đúng hẹn; **101 / 5.696 khách (1,77%)** sau đơn đầu giao trễ.
- Loại **17.595** khách mới vì chưa có đủ 90 ngày theo dõi.

Khoảng tin cậy của hai tỷ lệ mua lại chồng lấp nhau. Đây là liên hệ mô tả, chưa chứng minh giao trễ làm thay đổi hành vi khách hàng. [Case study](reports/delivery_case_study.md) giải thích phương pháp; [file kết quả](reports/delivery_findings.json) lưu số đếm và mẫu số.

## Các phần đã làm

- Làm sạch chín CSV liên quan; kiểm tra khóa, quan hệ và phép gộp theo đơn để tránh nhân số liệu khi join.
- Bảng staging/core, view, truy vấn KPI và kiểm tra chất lượng trên SQL Server.
- Trang tổng quan doanh thu và báo cáo `/delivery`: lọc tháng/bang/nhóm hàng, hiển thị số mẫu review, xuất CSV theo bộ lọc.
- [Project Power BI hai trang](powerbi/README.md), gồm model TMDL, Power Query và 19 measures DAX. [Kiểm tra DAX trong Desktop](reports/powerbi_validation.json) đã khớp Python về tổng, cohort, bộ lọc RJ và ngưỡng mẫu nhỏ. Bản lưu là `.pbip`, chưa có bản xuất `.pbix`.
- [Notebook EDA](notebooks/01_olist_eda.ipynb) và các biểu đồ từ dữ liệu đã xử lý.

![Pipeline Python với các đầu ra SQL, web và Power BI riêng](assets/pipeline-overview.svg)

## Tổng quan doanh thu: phạm vi khác

Trang overview dùng trạng thái cuối của toàn bộ dữ liệu, thay vì chỉ các lần giao đã quan sát trước 31/08. Phạm vi này có **96.478** đơn đã giao, **R$15,42 triệu** GMV theo giá trị thanh toán, gồm phí vận chuyển. GMV tháng 1–8 tăng **143,3%** từ 2017 sang 2018 khi so cùng kỳ.

Tỷ lệ giao trễ đã sửa là **6.534 / 96.470 đơn có đủ ngày (6,77%)**; tám đơn đã giao thiếu ngày giao thực tế. Dùng **6,72%** cho snapshot trong ảnh và **6,77%** cho overview toàn bộ dữ liệu.

Giao trễ được tính theo ngày lịch. Cách so timestamp trước đây tính nhầm **1.292 đơn giao trong đúng ngày hẹn** là trễ. Tỷ lệ cũ **8,11%** và phép so mua lại không cố định thời gian theo dõi đã được thay thế. Cohort hiện tại dùng cùng cửa sổ 90 ngày cho cả hai nhóm.

## Biểu đồ

![Điểm review theo tình trạng giao hàng](assets/delivery_review.png)

![Mua lại trong 90 ngày kèm khoảng tin cậy](assets/first_order_delivery_retention.png)

## Chạy trên máy

Đặt chín CSV nguồn được liệt kê ở [data/README.md](data/README.md) vào `data/raw/`. Dữ liệu gốc không được đưa lên Git.

```sh
python -m venv .venv
# Kích hoạt .venv theo shell đang dùng, sau đó:
python -m pip install -r requirements.txt
python src/run_pipeline.py
python -m unittest discover -s tests -v
cd dashboard
npm ci
npm run dev
```

Mở `http://localhost:3000` để xem overview và `/delivery` để lọc báo cáo giao hàng. Pipeline cũng xuất hai CSV dùng cho Power BI. Trên máy khác, chạy `python powerbi/configure.py` từ thư mục gốc rồi mở `.pbip` và Refresh trong Desktop. Dashboard web chạy độc lập với Desktop.

Trong `dashboard/`, `npm test` kiểm tra công thức metric; `npm run validate` chạy lint, type-check và build. CI chạy tests Python, kiểm tra dashboard và PBIR.

## SQL và tài liệu

[sql/README.md](sql/README.md) ghi thứ tự chạy, gồm `07_delivery_retention.sql`. Nạp lại dữ liệu đã sửa trước khi chạy. Truy vấn giao hàng/mua lại mới vẫn cần một lần đối chiếu trực tiếp trên SQL Server; kết quả DAX trong Desktop được ghi riêng.

- [Mô hình dữ liệu](reports/data_model.md)
- [Ghi chú xử lý](reports/processing_notes.md)
- [Trạng thái kiểm tra SQL](reports/sql_kpi_results.md)
- [Dữ liệu cho dashboard](dashboard/README.md)

Dữ liệu kết thúc năm 2018, không có chi tiết đơn vị vận chuyển. Kết quả không phản ánh hiệu suất hiện tại hay chứng minh tác động nhân quả. Mã nguồn: [MIT](LICENSE); dữ liệu theo điều khoản của nguồn gốc.
