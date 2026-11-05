# Power BI: delivery and repeat purchase

Báo cáo đã có hai trang **Delivery** và **Repeat purchase**, bộ lọc, mô hình TMDL và 19 measures. Mở [Olist/Olist.pbip](Olist/Olist.pbip) trong Power BI Desktop để chỉnh sửa. Bản lưu là project `.pbip`; chưa có file `.pbix`. Không cần cài Power BI để chạy dashboard web.

Model đã chạy DAX trực tiếp trong Desktop và khớp với Python về tổng đơn, review, cohort, Wilson interval, bộ lọc RJ và ngưỡng mẫu nhỏ. Kết quả ở [powerbi_validation.json](../reports/powerbi_validation.json).

Trên máy khác, chạy pipeline rồi `python powerbi/configure.py` từ thư mục gốc để đặt parameter DataFolder. Mở project và Refresh. Cache dữ liệu và thiết lập cá nhân của Desktop được loại khỏi Git.

Các đường xu hướng chỉ hiển thị tháng có ít nhất 200 đơn có ngày hoặc 200 khách đủ theo dõi. KPI tổng vẫn tính trên toàn bộ mẫu đang lọc. Hai nhóm mua lại chỉ thể hiện liên hệ mô tả, không chứng minh tác động nhân quả.

## Tạo dữ liệu

Sau khi chạy pipeline gốc:

```sh
python -m src.delivery_analysis
```

Hai file xuất vào `powerbi/data/`:

- `fact_orders.csv`: một dòng mỗi đơn đã giao và được quan sát trước ngày chốt.
- `customer_cohorts.csv`: một dòng mỗi khách, lấy thông tin từ đơn đã giao đầu tiên trong lịch sử hiện có.

Thư mục này không được đưa lên Git. Có thể chạy lại từ CSV Olist gốc.

## Import thủ công (tham khảo)

Trong Power BI Desktop, tạo parameter text `DataFolder`, trỏ tới đường dẫn tuyệt đối của `powerbi/data` trên máy. Tạo hai Blank Query, dán nội dung từ `fact_orders.pq` và `customer_cohorts.pq`, đặt tên query tương ứng với tên file.

Thêm các calculated table và measures trong `measures.dax`. Tạo quan hệ một-nhiều, lọc một chiều từ ba bảng dimension:

- `DimMonth[month]` tới `purchase_month` của cả hai bảng fact.
- `DimState[state]` tới `customer_state` của cả hai bảng fact.
- `DimCategory[category]` tới `primary_category` của cả hai bảng fact.

Không nối trực tiếp hai bảng fact bằng mã khách. Bộ lọc tháng trên bảng cohort là tháng của **đơn đầu tiên**, không phải tháng mua lại.

## Bố cục báo cáo

Trang Delivery: slicer tháng, bang, nhóm hàng; KPI tỷ lệ giao trễ và điểm review; biểu đồ số đơn trễ theo bang; bảng kèm mẫu số và số đơn có review. Dùng tỷ lệ dạng phần trăm và review hai chữ số thập phân.

Trang Repeat purchase: so sánh tỷ lệ mua lại 90 ngày theo trạng thái đơn đầu tiên. Hiển thị số khách đủ thời gian theo dõi và số khách mới bị loại. Thêm chú thích đây là liên hệ mô tả, chưa phải tác động nhân quả.

## Kiểm tra lại

Đối chiếu tổng đơn, số đơn trễ và số khách đủ theo dõi với `reports/delivery_findings.json`. So cùng thời điểm chốt và cùng bộ lọc. Không lấy tỷ lệ trên toàn bộ khách làm tỷ lệ mua lại 90 ngày vì khách mới chưa có đủ thời gian quan sát.

Khi có report Olist đang mở trong Desktop, có thể chạy `./powerbi/validate_model.ps1 -Port <port>` trên Windows để đối chiếu DAX với findings của Python. Các test Python kiểm tra field của visual có trong model, kích thước visual và chiều lọc của các quan hệ. CI kiểm tra PBIR; DAX engine trong Desktop được kiểm tra riêng.
