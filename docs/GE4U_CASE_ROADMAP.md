# GE4u English Ward – lộ trình bổ sung ca bệnh mỗi ngày

Mục tiêu: phủ đủ 115 clinical presentations của MCC (Canada), sau đó mỗi presentation có 2–3 ca (≈ 200 ca). Mỗi ca đều có câu hỏi hội chẩn (kiến thức nền).
Bản đồ hiện trạng: `docs/GE4U_MCC_CURRICULUM_MAP.md` và `data/curriculum/mcc-map.json`.

## Mỗi ngày (tác vụ tự động 10:17)
1. **5 ca mới** theo thứ tự bên dưới (ô đầu tiên có trạng thái `todo`).
   - Đúng định dạng CASES: có `tp` (điểm hướng dẫn), `src` (link đã đọc) và `hc` (2–3 câu hội chẩn kiến thức nền).
2. **Thêm hội chẩn cho 5 ca cũ** chưa có `hc`.
3. **Đối chiếu nguồn cho mọi con số và khuyến cáo:**
   - **Quốc tế:** WHO, CDC, NICE, ESC/AHA, GINA, ADA, StatPearls.
   - **Tiếng Việt:** Bộ Y tế (QĐ/hướng dẫn chẩn đoán điều trị), MSD Manual bản tiếng Việt, bệnh viện lớn.
   - Không xác minh được thì bỏ chi tiết đó.
   - Hai nguồn khác nhau thì ghi rõ trong `tp`.
4. **Kiểm thử:** dùng trình duyệt headless chơi từng ca mới đến màn hình kết quả, không được có lỗi.
5. **Mở Pull Request** `cases-YYYY-MM-DD`.
   - Không tự merge.
   - Owner/giảng viên trả lời "duyệt" hoặc merge trên GitHub thì nội dung mới lên web.
6. **Cập nhật** bảng dưới (`todo` → `pr`), `mcc-map.json` và `GE4U_MCC_CURRICULUM_MAP.md`.

## Thứ tự (MCC presentation → ca dự kiến)
| Ngày | Nhóm | Ca dự kiến (MCC #) | Trạng thái |
|---|---|---|---|
| 1 | Tâm thần | Trầm cảm (59) · Rối loạn lo âu / cơn hoảng sợ (69) · Ý tưởng tự sát – đánh giá nguy cơ (105) · Loạn thần cấp (86) · Cai rượu (103) | done |
| 2 | Sản phụ khoa | Tư vấn tránh thai (17) · Rong kinh (56) · Dọa sinh non (82) · Khí hư – viêm âm đạo (113) · Mãn kinh (57) | done |
| 3 | Thận – điện giải | Tổn thương thận cấp (89) · Hạ natri máu (99) · Tăng kali máu (79) · Protein niệu / hội chứng thận hư (84) · Tăng canxi máu (12) | todo |
| 4 | Tim mạch – hô hấp | Ngừng tim – hồi sinh tim phổi (13) · Ngất (106) · Tiếng thổi tim (62) · Ho ra máu (7) · Tràn dịch màng phổi (76) | todo |
| 5 | Nhi 1 | Sơ sinh suy hô hấp (64) · Chậm phát triển (21) · Chậm tăng trưởng (31) · Trẻ đi khập khiễng (20) · Thấp lùn (101) | todo |
| 6 | Nhi 2 | Lác / nhược thị (102) · ALTE / đột tử sơ sinh (104) · Khó khăn học tập – tăng động giảm chú ý (5) · Dậy thì sớm/muộn (93) · Tư vấn di truyền (36) | todo |
| 7 | Tiết niệu – nam khoa | Xoắn tinh hoàn (91) · Khối bìu (90) · Rối loạn cương (48) · Tiểu không tự chủ (47) · Nhiễm khuẩn lây qua đường tình dục (94) | todo |
| 8 | Huyết học – ung bướu | Hạch to (54) · Bạch cầu bất thường (120) · Khối u vú (10) · Khối cơ xương (53) · Khối vùng chậu (72) | todo |
| 9 | Tai mắt – da | Đau tai – viêm tai giữa (28) · Ù tai (108) · Nhìn đôi (23) · Ngứa (85) · Rụng tóc / bệnh móng (38) | todo |
| 10 | Khác 1 | Người bệnh hấp hối – chăm sóc giảm nhẹ (25) · Vô sinh (46) · Sa sinh dục (83) · Sàng lọc ung thư cổ tử cung (70) · Bụng chướng – cổ trướng (1) | todo |
| 11 | Khác 2 | Rối loạn nhân cách (75) · Mất ngủ (98) · Rậm lông (43) · Rối loạn lipid máu (51) · (dự phòng) | todo |
| 12+ | Vòng 2 | Mỗi presentation thêm ca thứ 2–3, khác mức độ/bối cảnh (cấp cứu, tuyến cơ sở, tái khám) | todo |
