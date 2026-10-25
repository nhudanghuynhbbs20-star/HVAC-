-- ============================================================
-- SBMS B8 - Schema cho Supabase, khớp với các mart hiện có
-- của pipeline (dim_room.csv, dim_ac_unit.csv, run_params.csv,
-- ooh_segment.csv, slot_coverage.csv, event_day_run.csv).
--
-- Cách dùng: vào Supabase > SQL Editor > New query > dán hết
-- nội dung file này > Run.
-- ============================================================

-- 1) Danh sách phòng
create table if not exists dim_room (
  room_id        text primary key,     -- ví dụ '109.B08'
  kind            text,                 -- 'Phòng học' / 'Phòng chức năng' ...
  kind_source     text,
  has_schedule    boolean,
  has_ac_data     boolean
);

-- 2) Máy lạnh gắn với từng phòng (1 phòng có thể nhiều máy)
create table if not exists dim_ac_unit (
  id        bigint generated always as identity primary key,
  room_id   text references dim_room(room_id),
  unit_id   text
);

-- 3) Cấu hình mỗi lần pipeline chạy (giờ hành chính, dung sai...)
create table if not exists run_params (
  run_id                  text primary key,   -- ví dụ '20261021_142453'
  building_suffix         text,
  soft_start_min          integer,
  bridge_gap_min          integer,
  tol_min                 integer,
  func_start              text,
  func_end                text,
  func_weekdays           text,
  cutoff                  text,
  short_seg_min           numeric,
  room_alias              jsonb,
  night_from              text,
  night_to                text,
  night_min_overlap_min   numeric,
  chain_gap_s             numeric,
  room_hours              jsonb
);

-- 4) Các phiên máy chạy NGOÀI khung giờ cho phép (dữ liệu chính cho mục "sau 17h")
create table if not exists ooh_segment (
  id              bigint generated always as identity primary key,
  run_week        text not null,       -- 'T41', 'T42', ...
  seg_id          text,
  date            date not null,
  room_id         text references dim_room(room_id),
  kind            text,
  start_ts        timestamp,
  end_ts          timestamp,
  minutes         numeric,
  hours           numeric,
  units_on        integer,
  machine_hours   numeric,
  position        text,
  rule_id         text,
  cause           text,
  cause_group     text,
  explained       boolean,
  unique (run_week, seg_id)
);
create index if not exists idx_ooh_date on ooh_segment(date);
create index if not exists idx_ooh_room on ooh_segment(room_id);

-- 5) Mức độ phủ lịch của từng ca học theo AAO (dữ liệu chính cho mục "có lịch, AC không chạy")
create table if not exists slot_coverage (
  id              bigint generated always as identity primary key,
  run_week        text not null,
  slot_id         text,
  date            date not null,
  room_id         text references dim_room(room_id),
  start_ts        timestamp,
  end_ts          timestamp,
  course_name     text,
  lecturer        text,
  students        integer,
  slot_min        numeric,
  covered_min     numeric,
  coverage_pct    numeric,
  is_event_day    boolean,
  first_on        timestamp,
  last_off        timestamp,
  unique (run_week, slot_id)
);
create index if not exists idx_sc_date on slot_coverage(date);
create index if not exists idx_sc_room on slot_coverage(room_id);

-- 6) Các ngày có sự kiện đặc biệt (khai giảng, thi...) làm lệch lịch AAO
create table if not exists event_day_run (
  id              bigint generated always as identity primary key,
  date            date not null,
  event_name      text,
  room_id         text references dim_room(room_id),
  first_on        timestamp,
  last_off        timestamp,
  room_hours      numeric,
  machine_hours   numeric
);
