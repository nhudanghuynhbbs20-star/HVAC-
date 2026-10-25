-- Bổ sung nhỏ trước khi chạy script Bước 4: thêm cột run_week vào
-- event_day_run để script biết xóa/nạp lại đúng dữ liệu của từng
-- tuần (tránh bị nhân đôi khi chạy lại). Chạy 1 lần trong SQL Editor.

alter table event_day_run add column if not exists run_week text;
