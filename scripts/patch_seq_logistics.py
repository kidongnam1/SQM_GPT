"""patch_seq_logistics.py — sqm-logistics.js 순번(#) 첫 컬럼 추가"""
import shutil, sys
from pathlib import Path
from datetime import datetime

TARGET = Path("/sessions/eloquent-amazing-ramanujan/mnt/SQM_v868_claan/frontend/js/sqm-logistics.js")
ts = datetime.now().strftime("%Y%m%d_%H%M%S")
backup = TARGET.with_name(f"sqm-logistics.js.bak_{ts}")
shutil.copy2(TARGET, backup)
print(f"[backup] {backup.name}")

src = TARGET.read_text(encoding="utf-8")
orig = src
changes = 0

# ══════════════════════════════════════════════════════════
#  MOVE 테이블
# ══════════════════════════════════════════════════════════

# 1) 헤더
OLD1 = "'<thead><tr><th>Date</th><th>LOT No</th><th>Type</th><th>Qty(MT)</th><th>From</th><th>To</th><th>By</th></tr></thead>'"
NEW1 = "'<thead><tr><th style=\"color:var(--text-muted);text-align:center;width:32px\">#</th><th>Date</th><th>LOT No</th><th>Type</th><th>Qty(MT)</th><th>From</th><th>To</th><th>By</th></tr></thead>'"
if OLD1 in src:
    src = src.replace(OLD1, NEW1, 1); changes += 1
    print("[ok1] move 헤더 # 추가")
else:
    print("[WARN1] move 헤더 앵커 없음")

# 2) rows.map 인덱스화
OLD2 = "      if (tbody) tbody.innerHTML = rows.map(function(r){\n        var qtyMT = r.qty_mt"
NEW2 = "      if (tbody) tbody.innerHTML = rows.map(function(r, _i){\n        var qtyMT = r.qty_mt"
if OLD2 in src:
    src = src.replace(OLD2, NEW2, 1); changes += 1
    print("[ok2] move rows.map 인덱스화")
else:
    print("[WARN2] move rows.map 앵커 없음")

# 3) 행 — Date td 앞 순번 td
OLD3 = "        return '<tr>' +\n          '<td class=\"mono-cell\">'+escapeHtml(r.movement_date||r.moved_at||r.date||'')+'</td>' +"
NEW3 = "        return '<tr>' +\n          '<td class=\"mono-cell\" style=\"color:var(--text-muted);text-align:center\">'+(_i+1)+'</td>' +\n          '<td class=\"mono-cell\">'+escapeHtml(r.movement_date||r.moved_at||r.date||'')+'</td>' +"
if OLD3 in src:
    src = src.replace(OLD3, NEW3, 1); changes += 1
    print("[ok3] move 행 순번 td 추가")
else:
    print("[WARN3] move 행 앵커 없음")

# ══════════════════════════════════════════════════════════
#  LOG 테이블
# ══════════════════════════════════════════════════════════

# 4) colgroup — # 컬럼 col 추가
OLD4 = "'<colgroup>',\n      '<col style=\"width:148px\">',"
NEW4 = "'<colgroup>',\n      '<col style=\"width:36px\">',\n      '<col style=\"width:148px\">',"
if OLD4 in src:
    src = src.replace(OLD4, NEW4, 1); changes += 1
    print("[ok4] log colgroup # col 추가")
else:
    print("[WARN4] log colgroup 앵커 없음")

# 5) log 헤더 — Time 앞에 # th 삽입
OLD5 = "'<th style=\"text-align:left;padding:5px 8px;white-space:nowrap\">Time</th>',"
NEW5 = "'<th style=\"color:var(--text-muted);text-align:center;padding:5px 8px;white-space:nowrap;width:36px\">#</th>',\n      '<th style=\"text-align:left;padding:5px 8px;white-space:nowrap\">Time</th>',"
if OLD5 in src:
    src = src.replace(OLD5, NEW5, 1); changes += 1
    print("[ok5] log 헤더 # 추가")
else:
    print("[WARN5] log 헤더 앵커 없음")

# 6) log rows.map 인덱스화
OLD6 = "      if (tbody) tbody.innerHTML = rows.map(function(r){\n        var rawDetail"
NEW6 = "      if (tbody) tbody.innerHTML = rows.map(function(r, _i){\n        var rawDetail"
if OLD6 in src:
    src = src.replace(OLD6, NEW6, 1); changes += 1
    print("[ok6] log rows.map 인덱스화")
else:
    print("[WARN6] log rows.map 앵커 없음")

# 7) log 행 — Time td 앞 순번 td 삽입
OLD7 = "        return '<tr style=\"font-size:12px\">' +\n          '<td class=\"mono-cell\" style=\"padding:4px 8px;white-space:nowrap;text-align:left;font-size:11px;color:var(--text-muted)\">'+escapeHtml(r.created_at||r.time||r.timestamp||'')+'</td>' +"
NEW7 = "        return '<tr style=\"font-size:12px\">' +\n          '<td class=\"mono-cell\" style=\"color:var(--text-muted);text-align:center;padding:4px 8px;font-size:11px\">'+(_i+1)+'</td>' +\n          '<td class=\"mono-cell\" style=\"padding:4px 8px;white-space:nowrap;text-align:left;font-size:11px;color:var(--text-muted)\">'+escapeHtml(r.created_at||r.time||r.timestamp||'')+'</td>' +"
if OLD7 in src:
    src = src.replace(OLD7, NEW7, 1); changes += 1
    print("[ok7] log 행 순번 td 추가")
else:
    print("[WARN7] log 행 앵커 없음")

print(f"\n[총 변경] {changes}곳")
TARGET.write_text(src, encoding="utf-8")
print(f"[done] {TARGET.name} 저장")
old_n = orig.count("\n"); new_n = src.count("\n")
print(f"[lines] {old_n} → {new_n} (diff {new_n-old_n:+d})")
tail = src[-200:]
if "})();" in tail or "}());" in tail:
    print("[ok] IIFE 닫힘 확인 ✅")
else:
    print("[WARN] IIFE 닫힘 미확인")
