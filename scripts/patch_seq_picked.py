"""patch_seq_picked.py — sqm-picked.js 순번(#) 첫 컬럼 추가"""
import shutil, sys
from pathlib import Path
from datetime import datetime

TARGET = Path("/sessions/eloquent-amazing-ramanujan/mnt/SQM_v868_claan/frontend/js/sqm-picked.js")
ts = datetime.now().strftime("%Y%m%d_%H%M%S")
backup = TARGET.with_name(f"sqm-picked.js.bak_{ts}")
shutil.copy2(TARGET, backup)
print(f"[backup] {backup.name}")

src = TARGET.read_text(encoding="utf-8")
orig = src
changes = 0

# ── 1) _renderPickedLotTableOnly 헤더 ─────────────────────────────────
OLD1 = "      + '<th style=\"text-align:center\">LOT No</th>'"
NEW1 = "      + '<th style=\"color:var(--text-muted);text-align:center;width:32px\">#</th>'\n      + '<th style=\"text-align:center\">LOT No</th>'"
if OLD1 in src:
    src = src.replace(OLD1, NEW1, 1); changes += 1
    print("[ok1] sub-table 헤더 # 추가")
else:
    print("[WARN1] sub-table 헤더 앵커 없음")

# ── 2) _renderPickedLotTableOnly forEach → 인덱스 ─────────────────────
OLD2 = "    rows.forEach(function(r) {"
NEW2 = "    rows.forEach(function(r, _i) {"
if OLD2 in src:
    src = src.replace(OLD2, NEW2, 1); changes += 1
    print("[ok2] sub forEach 인덱스화")
else:
    print("[WARN2] sub forEach 앵커 없음")

# ── 3) sub-table 행 — 순번 td 삽입 (LOT td 앞) ───────────────────────
OLD3 = "togglePickedDetail(\\'' + lot + '\\')\">'  \n        + '<td class=\"mono-cell cell-left\""
NEW3 = "togglePickedDetail(\\'' + lot + '\\')\">'  \n        + '<td class=\"mono-cell\" style=\"color:var(--text-muted);text-align:center\">' + (_i+1) + '</td>'\n        + '<td class=\"mono-cell cell-left\""
if OLD3 in src:
    src = src.replace(OLD3, NEW3, 1); changes += 1
    print("[ok3] sub-table 행 순번 td 추가")
else:
    # 실제 확인된 패턴으로 재시도
    OLD3b = "togglePickedDetail(\\'' + lot + '\\')\">'\n        + '<td class=\"mono-cell cell-left\""
    NEW3b = "togglePickedDetail(\\'' + lot + '\\')\">'\n        + '<td class=\"mono-cell\" style=\"color:var(--text-muted);text-align:center\">' + (_i+1) + '</td>'\n        + '<td class=\"mono-cell cell-left\""
    if OLD3b in src:
        src = src.replace(OLD3b, NEW3b, 1); changes += 1
        print("[ok3b] sub-table 행 순번 td 추가")
    else:
        print("[WARN3] sub-table 행 앵커 없음")

# ── 4) 메인 테이블 헤더 — # 첫 컬럼 ──────────────────────────────────
OLD4 = "'  <thead><tr><th></th><th style=\"text-align:center\">LOT No</th>"
NEW4 = "'  <thead><tr><th style=\"color:var(--text-muted);text-align:center;width:32px\">#</th><th></th><th style=\"text-align:center\">LOT No</th>"
if OLD4 in src:
    src = src.replace(OLD4, NEW4, 1); changes += 1
    print("[ok4] 메인 헤더 # 추가")
else:
    print("[WARN4] 메인 헤더 앵커 없음")

# ── 5) 메인 rows.map 인덱스화 ─────────────────────────────────────────
OLD5 = "      if (tbody) tbody.innerHTML = rows.map(function(r){"
NEW5 = "      if (tbody) tbody.innerHTML = rows.map(function(r, _i){"
if OLD5 in src:
    src = src.replace(OLD5, NEW5, 1); changes += 1
    print("[ok5] 메인 rows.map 인덱스화")
else:
    print("[WARN5] 메인 rows.map 앵커 없음")

# ── 6) 메인 테이블 행 — expand icon 앞에 순번 td 삽입 ────────────────
OLD6 = "' +\n          '<td style=\"width:24px;text-align:center\"><span class=\"picked-expand-icon\">▶</span></td>' +"
NEW6 = "' +\n          '<td class=\"mono-cell\" style=\"color:var(--text-muted);text-align:center\">'+(_i+1)+'</td>' +\n          '<td style=\"width:24px;text-align:center\"><span class=\"picked-expand-icon\">▶</span></td>' +"
if OLD6 in src:
    src = src.replace(OLD6, NEW6, 1); changes += 1
    print("[ok6] 메인 행 순번 td 추가")
else:
    print("[WARN6] 메인 행 앵커 없음 — 확인:")
    idx = src.find("picked-expand-icon")
    if idx >= 0: print("  →", repr(src[max(0,idx-100):idx+60]))

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
