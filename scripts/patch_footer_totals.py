# -*- coding: utf-8 -*-
"""
patch_footer_totals.py
======================
sqm-listview.js -- LOT / tonbag list modal footer totals bar

Changes:
  1. Add _renderLotFooter(foot, rows)
  2. Add _renderTonbagFooter(foot, rows)
  3. LOT load -> call _renderLotFooter
  4. LOT filter oninput -> update footer
  5. Tonbag load -> call _renderTonbagFooter
  6. Tonbag filter oninput -> update footer
"""

import shutil, pathlib, datetime, sys

SRC = pathlib.Path(__file__).parent.parent / 'frontend' / 'js' / 'sqm-listview.js'
BAK = SRC.with_suffix('.js.bak_footertotals_' + datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))

shutil.copy2(SRC, BAK)
print('[backup] ' + BAK.name)

txt = SRC.read_text(encoding='utf-8')

# ===========================================================================
# PATCH 1: Insert footer render functions before _applyFilter
# ===========================================================================
FOOTER_FUNCS = (
    "\n"
    "  /* -- LOT footer totals bar ---------------------------------------- */\n"
    "  function _renderLotFooter(foot, rows) {\n"
    "    var totalNet = 0, totalCur = 0, totalTonbag = 0;\n"
    "    rows.forEach(function(r) {\n"
    "      totalNet    += Number(r.net_weight     || 0);\n"
    "      totalCur    += Number(r.current_weight || 0);\n"
    "      totalTonbag += Number(r.tonbag_count   || 0);\n"
    "    });\n"
    "    var s = 'display:inline-block;padding:2px 14px;margin-right:8px;'\n"
    "          + 'background:rgba(79,195,247,0.13);border-radius:6px;'\n"
    "          + 'font-size:12px;color:var(--accent,#4fc3f7);font-weight:700;';\n"
    "    var hint = 'font-size:11px;color:var(--text-muted);margin-left:6px;';\n"
    "    foot.innerHTML =\n"
    "        '<span style=\"' + s + '\">📦 LOT ' + rows.length.toLocaleString('ko-KR') + ' 건</span>'\n"
    "      + '<span style=\"' + s + '\">⚖ 순중량 ' + totalNet.toLocaleString('ko-KR', {maximumFractionDigits:2}) + ' kg</span>'\n"
    "      + '<span style=\"' + s + '\">📊 현재 ' + totalCur.toLocaleString('ko-KR', {maximumFractionDigits:2}) + ' kg</span>'\n"
    "      + '<span style=\"' + s + '\">🎒 톤백 ' + totalTonbag.toLocaleString('ko-KR') + ' 개</span>'\n"
    "      + '<span style=\"' + hint + '\">※ 행 클릭 → 톤백 상세 보기 · 엑셀 다운로드는 우상단 버튼</span>';\n"
    "  }\n"
    "\n"
    "  /* -- Tonbag footer totals bar ------------------------------------- */\n"
    "  function _renderTonbagFooter(foot, rows) {\n"
    "    var totalWeight = 0;\n"
    "    rows.forEach(function(r) {\n"
    "      totalWeight += Number(r.weight_kg || 0);\n"
    "    });\n"
    "    var s = 'display:inline-block;padding:2px 14px;margin-right:8px;'\n"
    "          + 'background:rgba(79,195,247,0.13);border-radius:6px;'\n"
    "          + 'font-size:12px;color:var(--accent,#4fc3f7);font-weight:700;';\n"
    "    var hint = 'font-size:11px;color:var(--text-muted);margin-left:6px;';\n"
    "    foot.innerHTML =\n"
    "        '<span style=\"' + s + '\">🎒 톤백 ' + rows.length.toLocaleString('ko-KR') + ' 건</span>'\n"
    "      + '<span style=\"' + s + '\">⚖ 총 중량 ' + totalWeight.toLocaleString('ko-KR', {maximumFractionDigits:2}) + ' kg</span>'\n"
    "      + '<span style=\"' + hint + '\">※ 엑셀 다운로드는 우상단 버튼 사용</span>';\n"
    "  }\n"
    "\n"
)

ANCHOR1 = "  function _applyFilter(rows, q) {"
if ANCHOR1 not in txt:
    print('[ERROR] _applyFilter anchor not found')
    sys.exit(1)
txt = txt.replace(ANCHOR1, FOOTER_FUNCS + ANCHOR1, 1)
print('[PATCH 1] Footer render functions inserted')

# ===========================================================================
# PATCH 2: LOT load -> replace foot.textContent with _renderLotFooter call
# ===========================================================================
OLD2 = ("          foot.textContent = '※ 행 클릭 → 톤백 상세"
        " 보기  ·  엑셀 다운로드는 우상단"
        " 버튼  ·  전체 ' + rows.length + ' LOT';")
NEW2 = "          _renderLotFooter(foot, rows);"
if OLD2 not in txt:
    # fallback: find by unique substring
    import re
    m = re.search(r"          foot\.textContent = '.*LOT';", txt)
    if m:
        txt = txt[:m.start()] + NEW2 + txt[m.end():]
        print('[PATCH 2] LOT foot replaced (regex fallback)')
    else:
        print('[ERROR] LOT foot.textContent anchor not found')
        sys.exit(1)
else:
    txt = txt.replace(OLD2, NEW2, 1)
    print('[PATCH 2] LOT foot replaced')

# ===========================================================================
# PATCH 3: LOT filter oninput -> update footer after render
# ===========================================================================
OLD3 = "      _renderTable(LOT_COLS, _applyFilter(allRows, this.value), body, _onLotRowClick);"
NEW3 = (
    "      var _lotFiltered = _applyFilter(allRows, this.value);\n"
    "      _renderTable(LOT_COLS, _lotFiltered, body, _onLotRowClick);\n"
    "      _renderLotFooter(foot, _lotFiltered);"
)
if OLD3 not in txt:
    print('[ERROR] LOT filter oninput anchor not found')
    sys.exit(1)
txt = txt.replace(OLD3, NEW3, 1)
print('[PATCH 3] LOT filter footer update added')

# ===========================================================================
# PATCH 4: Tonbag load -> replace foot.textContent with _renderTonbagFooter
# ===========================================================================
OLD4 = ("          foot.textContent = '※ 엑셀 다운로드는"
        " 우상단 버튼 사용 · 전체 ' + rows.length + ' 톤백';")
NEW4 = "          _renderTonbagFooter(foot, rows);"
if OLD4 not in txt:
    import re
    m = re.search(r"          foot\.textContent = '.*톤백';", txt)
    if m:
        txt = txt[:m.start()] + NEW4 + txt[m.end():]
        print('[PATCH 4] Tonbag foot replaced (regex fallback)')
    else:
        print('[ERROR] Tonbag foot.textContent anchor not found')
        sys.exit(1)
else:
    txt = txt.replace(OLD4, NEW4, 1)
    print('[PATCH 4] Tonbag foot replaced')

# ===========================================================================
# PATCH 5: Tonbag filter oninput -> update footer after render
# ===========================================================================
OLD5 = "      _renderTable(TONBAG_COLS, _applyFilter(allRows, this.value), body);"
NEW5 = (
    "      var _tbFiltered = _applyFilter(allRows, this.value);\n"
    "      _renderTable(TONBAG_COLS, _tbFiltered, body);\n"
    "      _renderTonbagFooter(foot, _tbFiltered);"
)
if OLD5 not in txt:
    print('[ERROR] Tonbag filter oninput anchor not found')
    sys.exit(1)
txt = txt.replace(OLD5, NEW5, 1)
print('[PATCH 5] Tonbag filter footer update added')

# ===========================================================================
# Validate & Save
# ===========================================================================
assert '_renderLotFooter'    in txt, 'FAIL: _renderLotFooter missing'
assert '_renderTonbagFooter' in txt, 'FAIL: _renderTonbagFooter missing'
assert "rows.length + ' LOT'"  not in txt, 'FAIL: old LOT foot text still present'

SRC.write_text(txt, encoding='utf-8')
lines_after = len(txt.splitlines())
print('[saved] ' + SRC.name + '  (' + str(lines_after) + ' lines)')
print()
print('DONE! Summary:')
print('  LOT list  -> count, net_weight, current_weight, tonbag_count totals')
print('  Tonbag    -> count, weight_kg total')
print('  Filter    -> totals update in real-time')
print('  Footer    -> always visible (fixed, no scroll)')
