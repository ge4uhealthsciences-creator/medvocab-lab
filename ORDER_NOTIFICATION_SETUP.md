# GE4u — thiết lập và kiểm thử thông báo đơn hàng

Thông báo yêu cầu mua được gửi đến **ge4u.health.sciences@gmail.com**. Đây là thông báo về ý định mua, không phải bằng chứng khách đã chuyển khoản. Không thu tiền và không giao tài liệu tự động trước khi kiểm thử đầu-cuối.

## 1. Triển khai Google Apps Script Web App

1. Đăng nhập tài khoản Google quản lý GE4u và mở https://script.google.com/.
2. Mở dự án Apps Script đang được dùng bởi website. Nếu chưa có dự án, tạo dự án mới.
3. Sao chép nội dung hiện tại của `google-apps-script/Code.gs` trong repository vào dự án.
4. Lưu mã nguồn.
5. Mở **Project Settings → Script Properties**. Thiết lập `GE4U_ORDERS_SHEET_ID` bằng ID của Google Spreadsheet riêng tư dành cho đơn hàng.
6. Xác nhận spreadsheet có tab `Orders` với các cột bắt buộc được liệt kê trong `appendOrderToPrivateSheet_()`. Xác nhận tab `AutomationLog` có thể được tạo/ghi.
7. Chọn **Deploy → Manage deployments**. Chỉnh sửa deployment Web App đang dùng hoặc tạo deployment mới; chọn **Execute as: Me** và mức truy cập phù hợp để khách có thể gửi form công khai.
8. Cấp quyền Google yêu cầu và triển khai. Sao chép URL `/exec` đã triển khai.
9. Kiểm tra hai biểu mẫu trong `ge4u-dental-english.html` và `ge4u-products.html` dùng cùng URL `/exec`. Không thêm API key, mật khẩu, mã OTP hoặc thông tin thanh toán vào repository.

## 2. Kiểm thử bắt buộc trước khi mở bán

1. Mở URL `/exec` để kiểm tra chẩn đoán: người nhận email phải là `ge4u.health.sciences@gmail.com` và `GE4U_ORDERS_SHEET_ID configured` phải là `YES`.
2. Gửi một đơn thử bằng thông tin liên hệ do chủ tài khoản kiểm soát. Dùng email hợp lệ hoặc số điện thoại hợp lệ.
3. Xác nhận trang phản hồi có mã yêu cầu; kiểm tra hàng tương ứng trong tab `Orders`.
4. Kiểm tra email thông báo trong hộp thư đến và Spam.
5. Kiểm tra tab `AutomationLog` có các sự kiện lưu đơn và gửi email.
6. Thử dữ liệu không hợp lệ và xác nhận yêu cầu bị từ chối.
7. Lặp lại một lần từ biểu mẫu trang danh mục `ge4u-products.html`.
8. Ghi nhận kết quả thử. Chỉ coi bước thông báo là đạt khi các kiểm tra trên thành công.

## 3. Giới hạn hiện tại

- Apps Script không tự xác minh tiền chuyển khoản. Người bán phải kiểm tra giao dịch trong tài khoản ngân hàng trực tiếp.
- QR ngân hàng không tự gửi tín hiệu khi người mua quét mã.
- Chưa có bằng chứng giao tài liệu số tự động đã được tích hợp và kiểm thử. Không hứa giao tự động nếu chưa có luồng xác nhận thanh toán → cấp quyền tải tài liệu → xác nhận giao thành công.
- Trước khi mở bán, cần có chính sách quyền riêng tư và điều khoản xử lý thông tin khách hàng phù hợp.
- Việc cập nhật mã nguồn GitHub **không tự cập nhật bản Apps Script đã triển khai**. Chủ tài khoản cần triển khai phiên bản Web App mới, sau đó kiểm thử lại.
