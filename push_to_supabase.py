# ============================================================
# Bước 4: Đẩy dữ liệu từ pipeline (các file trong t41run/, t42run/...)
# vào Supabase.
#
# Cách dùng:
#   1. Cài thư viện cần thiết (chạy 1 lần):
#        pip install supabase python-dotenv pandas
#   2. Đặt file này cùng cấp với các thư mục t41run/, t42run/...
#      (giống cấu trúc hiện tại của bạn).
#   3. Tạo file ".env" (copy từ .env.example, điền URL + service_role
#      key thật của bạn vào, xem hướng dẫn trong .env.example).
#   4. Chạy:  python3 push_to_supabase.py
#
# Mỗi lần chạy cho 1 tuần: dữ liệu CŨ của đúng tuần đó trong 3 bảng
# ooh_segment / slot_coverage / event_day_run sẽ bị XÓA rồi NẠP LẠI
# mới hoàn toàn (không bị nhân đôi nếu chạy lại nhiều lần). Các bảng
# danh mục (dim_room, dim_ac_unit, run_params) được ghi đè theo khóa
# chính, cũng không bị nhân đôi.
# ============================================================

import os
import json
import numpy as np
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

# Luôn tìm file .env nằm CÙNG THƯ MỤC với file script này, không phụ
# thuộc vào việc bạn đang chạy lệnh từ thư mục nào (tránh lỗi không
# tìm thấy .env khi chạy bằng "python supabase/push_to_supabase.py"
# từ thư mục cha).
load_dotenv(Path(__file__).resolve().parent / ".env")
SUPABASE_URL = (os.environ.get("SUPABASE_URL") or "").strip().rstrip("/")
SUPABASE_SERVICE_KEY = (os.environ.get("SUPABASE_SERVICE_KEY") or "").strip()

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    raise SystemExit(
        "Chưa thấy SUPABASE_URL / SUPABASE_SERVICE_KEY.\n"
        "Kiểm tra lại: file '.env' có nằm đúng trong thư mục 'supabase/' (cùng chỗ với file này) không?"
    )

# In ra vài ký tự đầu/cuối + độ dài để bạn tự kiểm tra có đúng dạng
# "https://xxxx.supabase.co" hay không, KHÔNG in toàn bộ giá trị thật.
print(f"SUPABASE_URL đọc được: '{SUPABASE_URL[:16]}...{SUPABASE_URL[-15:]}' (dài {len(SUPABASE_URL)} ký tự)")
print(f"SUPABASE_SERVICE_KEY đọc được: dài {len(SUPABASE_SERVICE_KEY)} ký tự")

if "dán" in SUPABASE_SERVICE_KEY.lower():
    raise SystemExit(
        "SUPABASE_SERVICE_KEY có vẻ vẫn còn giữ chữ mẫu, chưa được thay bằng key thật. "
        "Mở lại file .env trong thư mục supabase/ để sửa."
    )

import re
if not re.fullmatch(r"https://[a-z0-9]+\.supabase\.co", SUPABASE_URL):
    raise SystemExit(
        "SUPABASE_URL sai định dạng. URL đúng CHỈ có dạng 'https://<mã-project>.supabase.co', "
        "không có dấu '/' hay chữ gì thêm ở cuối, không phải link lấy từ thanh địa chỉ trình duyệt.\n"
        "Cách lấy đúng: vào Supabase > Project Settings (icon bánh răng) > API > mục 'Project URL', "
        "bấm nút Copy NGAY CẠNH ô đó (đừng tự bôi đen/copy từ nơi khác), dán đè lại toàn bộ giá trị cũ trong .env."
    )

sb = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# Sửa danh sách này mỗi khi có tuần mới (giống cách làm trong export_t41t42/build.py)
ROOT = Path(__file__).resolve().parent.parent
WEEKS = [("T41", ROOT / "t41run"), ("T42", ROOT / "t42run")]

CHUNK = 500  # gửi tối đa 500 dòng mỗi lần, tránh payload quá lớn


def df_to_records(df: pd.DataFrame) -> list[dict]:
    """Chuyển DataFrame thành list dict sạch để gửi lên Supabase:
    NaN -> None, Timestamp -> chuỗi, số numpy -> số Python thường."""
    df = df.copy()
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            df[col] = df[col].dt.strftime("%Y-%m-%d %H:%M:%S")
    df = df.astype(object).where(pd.notnull(df), None)

    def cast(v):
        if isinstance(v, (np.integer,)):
            return int(v)
        if isinstance(v, (np.floating,)):
            return float(v) if not np.isnan(v) else None
        if isinstance(v, (np.bool_,)):
            return bool(v)
        return v

    return [{k: cast(v) for k, v in r.items()} for r in df.to_dict("records")]


def push_in_chunks(table: str, records: list[dict], mode: str = "upsert", on_conflict=None):
    for i in range(0, len(records), CHUNK):
        batch = records[i : i + CHUNK]
        if mode == "upsert":
            sb.table(table).upsert(batch, on_conflict=on_conflict).execute()
        else:
            sb.table(table).insert(batch).execute()
    print(f"  -> {table}: đã đẩy {len(records)} dòng")


# ---------------- 1) dim_room, dim_ac_unit, run_params (ghi đè theo khóa chính) ----------------
all_room = []
all_unit = []
for wk, root in WEEKS:
    all_room.append(pd.read_csv(root / "marts/dim_room.csv"))
    all_unit.append(pd.read_csv(root / "marts/dim_ac_unit.csv"))

dim_room = pd.concat(all_room, ignore_index=True).drop_duplicates(subset=["room_id"])
print("Đang đẩy dim_room...")
push_in_chunks("dim_room", df_to_records(dim_room), mode="upsert", on_conflict="room_id")

dim_unit = pd.concat(all_unit, ignore_index=True).drop_duplicates(subset=["room_id", "unit_id"])
print("Đang đẩy dim_ac_unit (nạp lại toàn bộ)...")
sb.table("dim_ac_unit").delete().neq("id", -1).execute()  # xóa hết rồi nạp lại mới (bảng danh mục nhỏ)
push_in_chunks("dim_ac_unit", df_to_records(dim_unit), mode="insert")

for wk, root in WEEKS:
    rp = pd.read_csv(root / "marts/run_params.csv")
    for col in ["room_alias", "room_hours"]:
        if col in rp.columns:
            rp[col] = rp[col].apply(lambda s: json.loads(s) if isinstance(s, str) else s)
    print(f"Đang đẩy run_params ({wk})...")
    push_in_chunks("run_params", df_to_records(rp), mode="upsert", on_conflict="run_id")

# ---------------- 2) ooh_segment, slot_coverage, event_day_run (xóa theo tuần rồi nạp lại) ----------------
for wk, root in WEEKS:
    print(f"\n== Tuần {wk} ==")

    ooh = pd.read_csv(root / "marts/ooh_segment.csv", parse_dates=["start_ts", "end_ts"])
    ooh["run_week"] = wk
    sb.table("ooh_segment").delete().eq("run_week", wk).execute()
    push_in_chunks("ooh_segment", df_to_records(ooh), mode="insert")

    sc = pd.read_csv(root / "marts/slot_coverage.csv", parse_dates=["start_ts", "end_ts", "first_on", "last_off"])
    sc["run_week"] = wk
    sb.table("slot_coverage").delete().eq("run_week", wk).execute()
    push_in_chunks("slot_coverage", df_to_records(sc), mode="insert")

    ev_path = root / "marts/event_day_run.csv"
    ev = None
    if ev_path.exists() and ev_path.stat().st_size > 0:
        try:
            ev = pd.read_csv(ev_path, parse_dates=["first_on", "last_off"])
        except pd.errors.EmptyDataError:
            ev = None
    if ev is not None and len(ev) > 0:
        ev["run_week"] = wk
        sb.table("event_day_run").delete().eq("run_week", wk).execute()
        push_in_chunks("event_day_run", df_to_records(ev), mode="insert")
    else:
        # Tuần này không có ngày sự kiện nào (ví dụ không có khai giảng/thi) - vẫn cần xóa
        # dữ liệu cũ của tuần này (nếu có từ lần chạy trước) để không bị sót dữ liệu sai.
        sb.table("event_day_run").delete().eq("run_week", wk).execute()
        print("  -> event_day_run: tuần này không có ngày sự kiện nào, bỏ qua")

print("\nXong. Vào Supabase > Table Editor để kiểm tra lại số dòng từng bảng.")
