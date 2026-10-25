# MedVocab Lab — hướng dẫn tự động hóa

## Hệ thống làm gì?
- Website học Medical English gồm flashcards, tìm kiếm từ vựng và quiz.
- Trang `daily-lessons.html` đọc dữ liệu từ `data/daily-lesson.json`.
- GitHub Actions tự chạy khi có commit lên `main`, khi chạy thủ công và theo lịch 06:00 giờ Việt Nam (23:00 UTC).
- Chưa có API key thì hệ thống dùng bài mẫu có sẵn, không phát sinh phí API.
- Nếu thêm secret `OPENAI_API_KEY`, chương trình thử tạo bài bằng OpenAI API; khi lỗi sẽ quay về bài mẫu. API có thể tính phí riêng.

## Bật GitHub Pages
1. Mở **Settings → Pages** trong repository.
2. Chọn **GitHub Actions** làm nguồn triển khai nếu chưa chọn.
3. Mở **Actions → Daily lesson and deploy** rồi chọn **Run workflow** để chạy thử.
4. Chỉ xem là đã xuất bản khi workflow thành công và URL xuất hiện trong **Settings → Pages**.

## Bật tạo bài bằng AI (không bắt buộc)
1. Tạo API key trên OpenAI Platform và kiểm tra billing/hạn mức.
2. Trong repository, mở **Settings → Secrets and variables → Actions → New repository secret**.
3. Đặt tên secret là `OPENAI_API_KEY`. Không ghi khóa vào mã nguồn, README, issue hoặc nội dung công khai.
4. Chạy workflow thủ công và xem log. Nếu API lỗi, bài mẫu sẽ được dùng thay thế.

## Lưu ý
- Không có bảo đảm doanh thu. Website hiện chưa tích hợp thanh toán, email giao hàng hay phân tích khách hàng.
- Nội dung y khoa do AI tạo cần được chuyên gia rà soát trước khi dùng làm tài liệu chính thức; không dùng để tư vấn cho bệnh nhân.
- GitHub Pages và Actions có giới hạn theo chính sách hiện hành của GitHub.
