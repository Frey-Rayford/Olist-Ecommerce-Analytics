# Power BI: delivery and repeat purchase

Bộ import dùng cùng dữ liệu với trang `/delivery` của dashboard. Chưa có file `.pbix`; tạo báo cáo trong Power BI Desktop theo các bước dưới đây.

## Tạo dữ liệu

Sau khi chạy pipeline gốc:

```sh
python -m src.delivery_analysis
```

Hai file xuất vào `powerbi/data/`:

- `fact_orders.csv`: một dòng mỗi đơn đã giao và được quan sát trước ngày chốt.
- `customer_cohorts.csv`: một dòng mỗi khách, lấy thông tin từ đơn đã giao đầu tiên trong lịch sử hiện có.

Thư mục này không được đưa lên Git. Có thể chạy lại từ CSV Olist gốc.

## Import

Trong Power BI Desktop, tạo parameter text `DataFolder`, trỏ tới đường dẫn tuyệt đối của `powerbi/data` trên máy. Tạo hai Blank Query, dán nội dung từ `fact_orders.pq` và `customer_cohorts.pq`, đặt tên query tương ứng với tên file.

Thêm các calculated table và measures trong `measures.dax`. Tạo quan hệ một-nhiều, lọc một chiều từ ba bảng dimension:

- `DimMonth[month]` tới `purchase_month` của cả hai bảng fact.
- `DimState[state]` tới `customer_state` của cả hai bảng fact.
- `DimCategory[category]` tới `primary_category` của cả hai bảng fact.

Không nối trực tiếp hai bảng fact bằng mã khách. Bộ lọc tháng trên bảng cohort là tháng của **đơn đầu tiên**, không phải tháng mua lại.

## Bố cục báo cáo

Trang Delivery: slicer tháng, bang, nhóm hàng; KPI tỷ lệ giao trễ và điểm review; biểu đồ số đơn trễ theo bang; bảng kèm mẫu số và số đơn có review. Dùng tỷ lệ dạng phần trăm và review hai chữ số thập phân.

Trang Repeat purchase: so sánh tỷ lệ mua lại 90 ngày theo trạng thái đơn đầu tiên. Hiển thị số khách đủ thời gian theo dõi và số khách mới bị loại. Thêm chú thích đây là liên hệ mô tả, chưa phải tác động nhân quả.

## Kiểm tra trước khi dùng số trên CV

Đối chiếu tổng đơn, số đơn trễ và số khách đủ theo dõi với `reports/delivery_findings.json`. So cùng thời điểm chốt và cùng bộ lọc. Không lấy tỷ lệ trên toàn bộ khách làm tỷ lệ mua lại 90 ngày vì khách mới chưa có đủ thời gian quan sát.
