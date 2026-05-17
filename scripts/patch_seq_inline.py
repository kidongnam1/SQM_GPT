"""patch_seq_inline.py — sqm-inline.js 순번(#) 첫 컬럼 추가 (7657줄 IIFE)
대상:
  1) _renderAllocLotTableOnly  헤더 + 행
  2) loadPickedPage            헤더 + 행
  3) loadReturnPage/renderReturnRows 헤더 + 행
  4) loadMovePage              헤더 + 행
  5) loadTonbagPage            헤더 + 행
"""
import shutil, sys
from pathlib import Path
from datetime import datetime

TARGET = Path("/sessions/eloquent-amazing-ramanujan/mnt/SQM_v868_claan/frontend/js/sqm-inline.js")
ts = datetime.now().strftime("%Y%m%d_%H%M%S")
backup = TARGET.with_name(f"sqm-inline.js.bak_{ts}")
shutil.copy2(TARGET, backup)
print(f"[backup] {backup.name}")

src = TARGET.read_text(encoding="utf-8")
orig = src
changes = 0

# ══════════════════════════════════════════════════════════
# 1) _renderAllocLotTableOnly
# ══════════════════════════════════════════════════════════

# 1a) 헤더 — checkbox th 뒤, LOT NO th 앞에 # th 삽입
OLD1a = "      + '<th style=\"width:32px\"></th>'\n      + '<th>LOT NO</th>"
NEW1a = "      + '<th style=\"width:32px\"></th>'\n      + '<th style=\"color:var(--text-muted);text-align:center;width:36px\">#</th>'\n      + '<th>LOT NO</th>"
if OLD1a in src:
    src = src.replace(OLD1a, NEW1a, 1); changes += 1
    print("[ok1a] alloc sub 헤더 # 추가")
else:
    print("[WARN1a] alloc sub 헤더 앵커 없음")

# 1b) forEach 인덱스화
OLD1b = "    rows.forEach(function(r) {\n      var lot = escapeHtml(r.lot_no || '');\n      var qtyMt = (r.total_mt"
NEW1b = "    rows.forEach(function(r, _i) {\n      var lot = escapeHtml(r.lot_no || '');\n      var qtyMt = (r.total_mt"
if OLD1b in src:
    src = src.replace(OLD1b, NEW1b, 1); changes += 1
    print("[ok1b] alloc sub forEach 인덱스화")
else:
    print("[WARN1b] alloc sub forEach 앵커 없음")

# 1c) 행 — checkbox td 뒤, LOT td 앞에 순번 td 삽입
OLD1c = "        + '<td style=\"text-align:center\"><input type=\"checkbox\" ' + checked + ' onclick=\"event.stopPropagation();window.allocToggleRow(\\\\\\'\" + lot + \"\\\\\\',this.checked)\"></td>'\n        + '<td class=\"mono-cell\" style=\"color:var(--accent);font-weight:600;cursor:pointer\""
NEW1c = "        + '<td style=\"text-align:center\"><input type=\"checkbox\" ' + checked + ' onclick=\"event.stopPropagation();window.allocToggleRow(\\\\\\'\" + lot + \"\\\\\\',this.checked)\"></td>'\n        + '<td class=\"mono-cell\" style=\"color:var(--text-muted);text-align:center\">' + (_i+1) + '</td>'\n        + '<td class=\"mono-cell\" style=\"color:var(--accent);font-weight:600;cursor:pointer\""
if OLD1c in src:
    src = src.replace(OLD1c, NEW1c, 1); changes += 1
    print("[ok1c] alloc sub 행 순번 td 추가")
else:
    print("[WARN1c] alloc sub 행 앵커 없음")

# ══════════════════════════════════════════════════════════
# 2) loadPickedPage (sqm-inline 버전)
# ══════════════════════════════════════════════════════════

# 2a) 헤더
OLD2a = "'  <thead><tr><th></th><th>LOT No</th><th>피킹No</th><th>고객사</th><th>톤백수</th><th>중량(kg)</th><th>Title Transfer Date</th></tr></thead>'"
NEW2a = "'  <thead><tr><th style=\"color:var(--text-muted);text-align:center;width:32px\">#</th><th></th><th>LOT No</th><th>피킹No</th><th>고객사</th><th>톤백수</th><th>중량(kg)</th><th>Title Transfer Date</th></tr></thead>'"
if OLD2a in src:
    src = src.replace(OLD2a, NEW2a, 1); changes += 1
    print("[ok2a] inline picked 헤더 # 추가")
else:
    print("[WARN2a] inline picked 헤더 앵커 없음")

# 2b) rows.map 인덱스화 (inline picked 버전 — var lot = escapeHtml(r.lot_no||''))
OLD2b = "      if (tbody) tbody.innerHTML = rows.map(function(r){\n        var lot = escapeHtml(r.lot_no||'');\n        return '<tr class=\"picked-summary-row\" data-lot=\"'+lot+'\""
NEW2b = "      if (tbody) tbody.innerHTML = rows.map(function(r, _i){\n        var lot = escapeHtml(r.lot_no||'');\n        return '<tr class=\"picked-summary-row\" data-lot=\"'+lot+'\""
if OLD2b in src:
    src = src.replace(OLD2b, NEW2b, 1); changes += 1
    print("[ok2b] inline picked rows.map 인덱스화")
else:
    print("[WARN2b] inline picked rows.map 앵커 없음")

# 2c) 행 — expand icon td 앞에 순번 td
OLD2c = "          '<td style=\"width:24px;text-align:center\"><span class=\"picked-expand-icon\">▶</span></td>' +\n          '<td class=\"mono-cell\" style=\"color:var(--accent);font-weight:600\">'+lot+'</td>' +\n          '<td class=\"mono-cell\">'+escapeHtml(r.picking_no||'')+'</td>' +\n          '<td>'+escapeHtml(r.customer||r.picked_to||'')+'</td>' +\n          '<td class=\"mono-cell\" style=\"text-align:right\">'+(r.tonbag_count||0)+'</td>' +\n          '<td class=\"mono-cell\" style=\"text-align:right\">'+(r.total_kg!=null?fmtN(r.total_kg):'-')+'</td>' +\n          '<td class=\"mono-cell\">'+escapeHtml(r.picking_date||'')+'</td>' +"
NEW2c = "          '<td class=\"mono-cell\" style=\"color:var(--text-muted);text-align:center\">'+(_i+1)+'</td>' +\n          '<td style=\"width:24px;text-align:center\"><span class=\"picked-expand-icon\">▶</span></td>' +\n          '<td class=\"mono-cell\" style=\"color:var(--accent);font-weight:600\">'+lot+'</td>' +\n          '<td class=\"mono-cell\">'+escapeHtml(r.picking_no||'')+'</td>' +\n          '<td>'+escapeHtml(r.customer||r.picked_to||'')+'</td>' +\n          '<td class=\"mono-cell\" style=\"text-align:right\">'+(r.tonbag_count||0)+'</td>' +\n          '<td class=\"mono-cell\" style=\"text-align:right\">'+(r.total_kg!=null?fmtN(r.total_kg):'-')+'</td>' +\n          '<td class=\"mono-cell\">'+escapeHtml(r.picking_date||'')+'</td>' +"
if OLD2c in src:
    src = src.replace(OLD2c, NEW2c, 1); changes += 1
    print("[ok2c] inline picked 행 순번 td 추가")
else:
    print("[WARN2c] inline picked 행 앵커 없음")

# ══════════════════════════════════════════════════════════
# 3) loadReturnPage / renderReturnRows
# ══════════════════════════════════════════════════════════

# 3a) 헤더
OLD3a = "'<thead><tr><th>LOT</th><th>Product</th><th>Qty</th><th>Date</th><th>Reason</th></tr></thead>'"
NEW3a = "'<thead><tr><th style=\"color:var(--text-muted);text-align:center;width:32px\">#</th><th>LOT</th><th>Product</th><th>Qty</th><th>Date</th><th>Reason</th></tr></thead>'"
if OLD3a in src:
    src = src.replace(OLD3a, NEW3a, 1); changes += 1
    print("[ok3a] return 헤더 # 추가")
else:
    print("[WARN3a] return 헤더 앵커 없음")

# 3b) renderReturnRows map 인덱스화
OLD3b = "    if (tbody) tbody.innerHTML = rows.map(function(r){\n      return '<tr><td>'+escapeHtml(r.lot||'')"
NEW3b = "    if (tbody) tbody.innerHTML = rows.map(function(r, _i){\n      return '<tr><td class=\"mono-cell\" style=\"color:var(--text-muted);text-align:center\">'+(_i+1)+'</td><td>'+escapeHtml(r.lot||'')"
if OLD3b in src:
    src = src.replace(OLD3b, NEW3b, 1); changes += 1
    print("[ok3b] return 행 순번 td 추가")
else:
    print("[WARN3b] return 행 앵커 없음")

# ══════════════════════════════════════════════════════════
# 4) loadMovePage (sqm-inline 버전)
# ══════════════════════════════════════════════════════════

# 4a) 헤더
OLD4a = "'<thead><tr><th>Date</th><th>LOT No</th><th>Type</th><th>Qty(MT)</th><th>From</th><th>To</th><th>By</th></tr></thead>'"
NEW4a = "'<thead><tr><th style=\"color:var(--text-muted);text-align:center;width:32px\">#</th><th>Date</th><th>LOT No</th><th>Type</th><th>Qty(MT)</th><th>From</th><th>To</th><th>By</th></tr></thead>'"
if OLD4a in src:
    src = src.replace(OLD4a, NEW4a, 1); changes += 1
    print("[ok4a] inline move 헤더 # 추가")
else:
    print("[WARN4a] inline move 헤더 앵커 없음")

# 4b) rows.map 인덱스화 (inline move 버전 — var qtyMT)
OLD4b = "      if (tbody) tbody.innerHTML = rows.map(function(r){\n        var qtyMT = r.qty_mt != null ? fmtN(r.qty_mt)"
NEW4b = "      if (tbody) tbody.innerHTML = rows.map(function(r, _i){\n        var qtyMT = r.qty_mt != null ? fmtN(r.qty_mt)"
if OLD4b in src:
    src = src.replace(OLD4b, NEW4b, 1); changes += 1
    print("[ok4b] inline move rows.map 인덱스화")
else:
    print("[WARN4b] inline move rows.map 앵커 없음")

# 4c) 행 — Date td 앞 순번 td
OLD4c = "        return '<tr>' +\n          '<td class=\"mono-cell\">'+escapeHtml(r.movement_date||r.moved_at||r.date||'')+'</td>' +\n          '<td class=\"mono-cell\" style=\"color:var(--accent)\">"
NEW4c = "        return '<tr>' +\n          '<td class=\"mono-cell\" style=\"color:var(--text-muted);text-align:center\">'+(_i+1)+'</td>' +\n          '<td class=\"mono-cell\">'+escapeHtml(r.movement_date||r.moved_at||r.date||'')+'</td>' +\n          '<td class=\"mono-cell\" style=\"color:var(--accent)\">"
if OLD4c in src:
    src = src.replace(OLD4c, NEW4c, 1); changes += 1
    print("[ok4c] inline move 행 순번 td 추가")
else:
    print("[WARN4c] inline move 행 앵커 없음")

# ══════════════════════════════════════════════════════════
# 5) loadTonbagPage (sqm-inline 버전)
# ══════════════════════════════════════════════════════════

# 5a) 헤더
OLD5a = "'<thead><tr><th>Tonbag ID</th><th>LOT</th><th>Product</th><th>Status</th><th>Weight(MT)</th><th>Location</th><th>Container</th><th></th></tr></thead>'"
NEW5a = "'<thead><tr><th style=\"color:var(--text-muted);text-align:center;width:32px\">#</th><th>Tonbag ID</th><th>LOT</th><th>Product</th><th>Status</th><th>Weight(MT)</th><th>Location</th><th>Container</th><th></th></tr></thead>'"
if OLD5a in src:
    src = src.replace(OLD5a, NEW5a, 1); changes += 1
    print("[ok5a] inline tonbag 헤더 # 추가")
else:
    print("[WARN5a] inline tonbag 헤더 앵커 없음")

# 5b) rows.map 인덱스화 (inline tonbag 버전)
OLD5b = "      if (tbody) tbody.innerHTML=rows.map(function(r){\n        return '<tr>' +\n          '<td class=\"mono-cell\">'+escapeHtml(r.sub_lt||r.tonbag_id||'-')+'</td>' +"
NEW5b = "      if (tbody) tbody.innerHTML=rows.map(function(r, _i){\n        return '<tr>' +\n          '<td class=\"mono-cell\" style=\"color:var(--text-muted);text-align:center\">'+(_i+1)+'</td>' +\n          '<td class=\"mono-cell\">'+escapeHtml(r.sub_lt||r.tonbag_id||'-')+'</td>' +"
if OLD5b in src:
    src = src.replace(OLD5b, NEW5b, 1); changes += 1
    print("[ok5b] inline tonbag 행 순번 td 추가")
else:
    print("[WARN5b] inline tonbag 행 앵커 없음")

print(f"\n[총 변경] {changes}곳")
if src == orig:
    print("[ERROR] 변경 없음")
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
