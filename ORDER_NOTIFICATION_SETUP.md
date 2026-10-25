# GE4u — bật thông báo đơn hàng qua email

Thông báo sẽ được gửi đến **trungminhle.lmt@gmail.com** khi khách gửi biểu mẫu đặt mua.
Đây là thông báo về ý định mua, không phải bằng chứng khách đã chuyển khoản.

## Thiết lập miễn phí (cần chủ tài khoản thực hiện một lần)

1. Đăng nhập tài khoản Google của bạn và mở https://script.google.com/
2. Chọn **New project**.
3. Xoá mã mẫu, sau đó sao chép toàn bộ nội dung tệp `google-apps-script/Code.gs` trong repository này vào trình soạn thảo.
4. Bấm **Save**.
5. Chọn **Deploy → New deployment**.
6. Nhấn biểu tượng bánh răng và chọn **Web app**.
7. **Execute as:** Me.
8. **Who has access:** Anyone. Điều này cho phép khách gửi biểu mẫu công khai; không đưa thông tin nhạy cảm vào mã.
9. Bấm **Deploy**, chấp thuận quyền gửi email khi Google yêu cầu, rồi sao chép URL kết thúc bằng `/exec`.
10. Mở tệp `ge4u-dental-english.html` trong repository. Tìm `const ORDER_ENDPOINT = "";` và dán URL /exec vào giữa dấu ngoặc kép.
11. Commit thay đổi để GitHub Pages triển khai lại website.

## Kiểm thử

- Gửi một yêu cầu thử bằng thông tin liên hệ của chính bạn.
- Xác nhận email đến `trungminhle.lmt@gmail.com`, kiểm tra cả Spam.
- Sau kiểm thử, không công khai thông tin cá nhân của người mua trong các log hoặc repository.

## Giới hạn

- Apps Script gửi email thông báo khi có biểu mẫu mới; cần chủ tài khoản cấp quyền và triển khai web app.
- QR ngân hàng không tự gửi tín hiệu khi người mua quét mã.
- Không tự xác minh giao dịch ngân hàng, không xác nhận tiền đã về và không giao file tự động.
- Trước khi bật form công khai, kiểm tra quy trình xử lý thông tin khách và thêm chính sách riêng tư/điều khoản bán hàng phù hợp.
