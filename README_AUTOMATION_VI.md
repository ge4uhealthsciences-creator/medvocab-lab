# MedVocab Lab — hướng dẫn tự động hóa

## Hệ thống làm gì?
- Website học Medical English gồm flashcards, tìm kiếm từ vựng và quiz.
- Trang `daily-lessons.html` đọc dữ liệu từ `data/daily-lesson.json`.
- GitHub Actions tự chạy khi có commit lên `main`, khi chạy thủ công và theo lịch 06:00 giờ Việt Nam (23:00 UTC).
- Bài học hằng ngày lấy từ bộ bài mẫu có sẵn, không dùng API AI bên ngoài.

## Bật GitHub Pages
1. Mở **Settings → Pages** trong repository.
2. Chọn **GitHub Actions** làm nguồn triển khai nếu chưa chọn.
3. Mở **Actions → Daily lesson and deploy** rồi chọn **Run workflow** để chạy thử.
4. Chỉ xem là đã xuất bản khi workflow thành công và URL xuất hiện trong **Settings → Pages**.

## Lưu ý
- Không có bảo đảm doanh thu. Website hiện chưa tích hợp thanh toán, email giao hàng hay phân tích khách hàng.
- Nội dung y khoa do AI tạo cần được chuyên gia rà soát trước khi dùng làm tài liệu chính thức; không dùng để tư vấn cho bệnh nhân.
- GitHub Pages và Actions có giới hạn theo chính sách hiện hành của GitHub.
