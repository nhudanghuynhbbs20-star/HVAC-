-- ============================================================
-- Bước 3: Khóa quyền truy cập (Row Level Security - RLS)
--
-- Chỉ bật RLS, KHÔNG thêm policy nào. Kết quả: mọi truy cập đi
-- qua API công khai (anon key) bị từ chối hoàn toàn. Bạn (chủ
-- project) và người được invite vào Organization vẫn xem/sửa
-- bình thường qua Table Editor / SQL Editor - đó là kênh riêng,
-- không bị RLS chi phối.
--
-- KHÔNG cần viết thêm policy "allow all" (ví dụ using (true)) để
-- "sửa" cảnh báo Unrestricted - làm vậy là mở lại toàn quyền công
-- khai, mất hết tác dụng của bước này.
-- ============================================================

alter table dim_room       enable row level security;
alter table dim_ac_unit    enable row level security;
alter table run_params     enable row level security;
alter table ooh_segment    enable row level security;
alter table slot_coverage  enable row level security;
alter table event_day_run  enable row level security;
