"""
patch_avail_ui.py — sqm-inventory.js Available 페이지 선택 취소 UI 복원
  A) _availViewMode + _availModeBtn 헬퍼 함수 추가 (loadAvailablePage 앞)
  B) 모드별 정렬 로직 추가 (rows 획득 직후)
  C) 툴바에 모드 버튼 + 선택 취소 버튼 추가
  D) 테이블 헤더에 마스터 체크박스 <th> 추가
  E) 샘플 행에 빈 <td> (체크박스 열 자리) 추가
  F) 메인 행에 avail-cb 체크박스 <td> 추가
  G) tfoot colspan 6 → 7 (컬럼 수 증가)
"""
import shutil, sys
from pathlib import Path
from datetime import datetime

TARGET = Path("/sessions/eloquent-amazing-ramanujan/mnt/SQM_v868_claan/frontend/js/sqm-inventory.js")
ts = datetime.now().strftime("%Y%m%d_%H%M%S")
backup = TARGET.with_name(f"sqm-inventory.js.bak_avail_{ts}")
shutil.copy2(TARGET, backup)
print(f"[backup] {backup.name}")

src = TARGET.read_text(encoding="utf-8")
orig = src
changes = 0

# ══════════════════════════════════════════════════════════
# A) _availViewMode + _availModeBtn 헬퍼 삽입 (loadAvailablePage 함수 직전)
# ══════════════════════════════════════════════════════════
OLDA = "  function loadAvailablePage() {"
NEWA = (
    "  window._availViewMode = window._availViewMode || 'lot';\n"
    "  function _availModeBtn(val, label) {\n"
    "    var cur = window._availViewMode || 'lot';\n"
    "    var active = val === cur\n"
    "      ? 'background:var(--accent,#3b82f6);color:#fff;border-color:var(--accent,#3b82f6);'\n"
    "      : 'background:var(--surface,#1e293b);color:var(--text-muted);border-color:var(--border,#334155);';\n"
    "    return '<button class=\"btn\" style=\"font-size:12px;padding:4px 10px;' + active + '\" '\n"
    "      + 'onclick=\"window._availViewMode=\\'' + val + '\\';window.loadAvailablePage()\">' + label + '</button>';\n"
    "  }\n"
    "\n"
    "  function loadAvailablePage() {"
)
if OLDA in src:
    src = src.replace(OLDA, NEWA, 1); changes += 1
    print("[okA] _availViewMode + _availModeBtn 헬퍼 추가")
else:
    print("[WARNA] loadAvailablePage 앵커 없음")

# ══════════════════════════════════════════════════════════
# B) 모드별 정렬 로직 — rows 확인 후, sumBal 계산 직전
# ══════════════════════════════════════════════════════════
OLDB = (
    "      var sumBal = 0, sumNet = 0, sumIni = 0, sumOb = 0;\n"
    "      rows.forEach(function(r) {\n"
    "        if (r.balance      != null && !isNaN(Number(r.balance)))      sumBal += Number(r.balance);"
)
NEWB = (
    "      var mode = window._availViewMode || 'lot';\n"
    "      if (mode === 'container') rows = rows.slice().sort(function(a,b){ return (a.container||'').localeCompare(b.container||''); });\n"
    "      else if (mode === 'date') rows = rows.slice().sort(function(a,b){ return (a.arrival_date||a.inbound_date||'').localeCompare(b.arrival_date||b.inbound_date||''); });\n"
    "      var sumBal = 0, sumNet = 0, sumIni = 0, sumOb = 0;\n"
    "      rows.forEach(function(r) {\n"
    "        if (r.balance      != null && !isNaN(Number(r.balance)))      sumBal += Number(r.balance);"
)
if OLDB in src:
    src = src.replace(OLDB, NEWB, 1); changes += 1
    print("[okB] 모드 정렬 로직 추가")
else:
    print("[WARNB] sumBal 앵커 없음")

# ══════════════════════════════════════════════════════════
# C) 툴바 — 새로고침 버튼 뒤에 선택 취소 버튼 + 모드 버튼 추가
# ══════════════════════════════════════════════════════════
OLDC = (
    "        + '<button class=\"btn btn-ghost\" style=\"font-size:12px;margin-left:auto\" onclick=\"window.loadAvailablePage()\">🔄 새로고침</button>'\n"
    "        + '</div>'"
)
NEWC = (
    "        + '<button class=\"btn btn-ghost\" style=\"font-size:12px;margin-left:auto\" onclick=\"window.loadAvailablePage()\">🔄 새로고침</button>'\n"
    "        + '<button class=\"btn\" style=\"font-size:12px;padding:4px 10px;background:rgba(245,158,11,0.15);color:#f59e0b;border:1px solid #f59e0b55\" onclick=\"window.availCancelSelected()\">↩️ 선택 취소(→PENDING)</button>'\n"
    "        + '<div style=\"display:flex;gap:4px\">' + _availModeBtn('lot','LOT별') + _availModeBtn('container','컨테이너별') + _availModeBtn('date','입고일별') + '</div>'\n"
    "        + '</div>'"
)
if OLDC in src:
    src = src.replace(OLDC, NEWC, 1); changes += 1
    print("[okC] 툴바 선택취소 + 모드 버튼 추가")
else:
    print("[WARNC] 툴바 새로고침 앵커 없음")

# ══════════════════════════════════════════════════════════
# D) 테이블 헤더 — 마스터 체크박스 <th> 삽입 (# 앞)
# ══════════════════════════════════════════════════════════
OLDD = (
    "        + '<div style=\"overflow-x:auto\"><table class=\"data-table\"><thead><tr>'\n"
    "        + '<th>#</th><th style=\"text-align:left !important\">LOT</th>"
)
NEWD = (
    "        + '<div style=\"overflow-x:auto\"><table class=\"data-table\"><thead><tr>'\n"
    "        + '<th style=\"width:32px;text-align:center\"><input type=\"checkbox\" onclick=\"window.availToggleAll(this)\"></th>'\n"
    "        + '<th>#</th><th style=\"text-align:left !important\">LOT</th>"
)
if OLDD in src:
    src = src.replace(OLDD, NEWD, 1); changes += 1
    print("[okD] 헤더 마스터 체크박스 추가")
else:
    print("[WARND] 헤더 앵커 없음")

# ══════════════════════════════════════════════════════════
# E) 샘플 행 — 첫 <td> 앞에 빈 체크박스 열 <td> 추가
# ══════════════════════════════════════════════════════════
OLDE = (
    "            '<tr style=\"background:rgba(234,179,8,0.08);border-left:3px solid #eab308\">' +\n"
    "            '<td class=\"mono-cell\" style=\"color:#eab308;text-align:center;padding:6px 10px\">\\u{1F52C}</td>' +"
)
NEWE = (
    "            '<tr style=\"background:rgba(234,179,8,0.08);border-left:3px solid #eab308\">' +\n"
    "            '<td></td>' +\n"
    "            '<td class=\"mono-cell\" style=\"color:#eab308;text-align:center;padding:6px 10px\">\\u{1F52C}</td>' +"
)
if OLDE in src:
    src = src.replace(OLDE, NEWE, 1); changes += 1
    print("[okE] 샘플 행 빈 td 추가")
else:
    print("[WARNE] 샘플 행 앵커 없음 — 확인:")
    idx = src.find("1F52C")
    if idx >= 0: print("  →", repr(src[max(0,idx-80):idx+60]))

# ══════════════════════════════════════════════════════════
# F) 메인 행 — avail-cb 체크박스 <td> 삽입 (# td 앞)
# ══════════════════════════════════════════════════════════
OLDF = (
    "          + '<td class=\"mono-cell\" style=\"color:var(--text-muted)\">' + (i+1) + '</td>'\n"
    "          + '<td class=\"mono-cell cell-left\" style=\"color:var(--accent);font-weight:600;padding:6px 10px\">' + lotKey + '</td>'"
)
NEWF = (
    "          + '<td style=\"text-align:center\"><input class=\"avail-cb\" type=\"checkbox\" data-lot=\"' + lotKey + '\" onclick=\"event.stopPropagation()\"></td>'\n"
    "          + '<td class=\"mono-cell\" style=\"color:var(--text-muted)\">' + (i+1) + '</td>'\n"
    "          + '<td class=\"mono-cell cell-left\" style=\"color:var(--accent);font-weight:600;padding:6px 10px\">' + lotKey + '</td>'"
)
if OLDF in src:
    src = src.replace(OLDF, NEWF, 1); changes += 1
    print("[okF] 메인 행 avail-cb 체크박스 td 추가")
else:
    print("[WARNF] 메인 행 앵커 없음")

# ══════════════════════════════════════════════════════════
# G) tfoot colspan 6 → 7 (체크박스 열 추가로 컬럼 수 증가)
# ══════════════════════════════════════════════════════════
OLDG = "      html += '<td colspan=\"6\" style=\"text-align:right;padding:8px 10px\">합계 (' + rows.length + ' LOT)</td>';"
NEWG = "      html += '<td colspan=\"7\" style=\"text-align:right;padding:8px 10px\">합계 (' + rows.length + ' LOT)</td>';"
if OLDG in src:
    src = src.replace(OLDG, NEWG, 1); changes += 1
    print("[okG] tfoot colspan 6→7 수정")
else:
    print("[WARNG] tfoot colspan 앵커 없음")

# ── 결과 ──────────────────────────────────────────────────
print(f"\n[총 변경] {changes}곳 (목표 7)")
if changes == 0:
    print("[ERROR] 변경 없음 — 원본 유지")
    sys.exit(1)

TARGET.write_text(src, encoding="utf-8")
print(f"[done] {TARGET.name} 저장")
old_n = orig.count("\n"); new_n = src.count("\n")
print(f"[lines] {old_n} → {new_n} (diff {new_n-old_n:+d})")
tail = src[-200:]
if "})();" in tail or "}());" in tail:
    print("[ok] IIFE 닫힘 확인 ✅")
else:
    print("[WARN] IIFE 닫힘 미확인")
    print(repr(tail[-100:]))
