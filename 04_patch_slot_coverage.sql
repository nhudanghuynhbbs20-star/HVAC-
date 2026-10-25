-- Bổ sung các cột còn thiếu trong bảng slot_coverage (phát hiện khi
-- chạy thử script Bước 4 với dữ liệu thật). Chạy 1 lần trong SQL Editor.

alter table slot_coverage add column if not exists head_gap_min   numeric;
alter table slot_coverage add column if not exists tail_gap_min   numeric;
alter table slot_coverage add column if not exists mid_gap_min    numeric;
alter table slot_coverage add column if not exists event_name     text;
alter table slot_coverage add column if not exists override_note  text;
alter table slot_coverage add column if not exists kpi_included   boolean;
