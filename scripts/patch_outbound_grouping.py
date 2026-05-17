# -*- coding: utf-8 -*-
"""
patch_outbound_grouping.py
============================
Purpose: Outbound 탭에 LOT별/고객사별/출고일별 그룹화 모드 추가
Why    : 사용자 요청 — Pending/Available처럼 그룹화 선택 가능하게
Method : Pending 패턴(_pendingViewMode + _renderPendingGroupRows) 차용
         Outbound 전용 변수 _outboundViewMode + 그룹화 함수 신규
Target : frontend/js/sqm-logistics.js (loadOutboundPage 함수)
Rule   : CLAUDE.md Rule 5 — Python 스크립트만 (IIFE 보존)
Author : Ruby — 2026-05-16
멱등성  : patch 문자열이 이미 들어있으면 SKIP
"""
import sys
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
TARGET = ROOT / "frontend" / "js" / "sqm-logistics.js"


# -----------------------------------------------------------------------------
# (1) 헬퍼 함수 + 모드 상태 — loadOutboundPage() 직전에 삽입
# -----------------------------------------------------------------------------
HELPER_ANCHOR = "  function loadOutboundPage() {"

HELPER_PATCH = """  // v868 fix (2026-05-16): Outbound 그룹화 모드 (LOT / 고객사 / 출고일)
  window._outboundViewMode = window._outboundViewMode || 'lot';

  function _outboundModeBtn(val, label, cur) {
    var act = val === cur
      ? 'background:var(--accent,#3b82f6);color:#fff;border-color:var(--accent,#3b82f6);'
      : 'background:var(--surface,#1e293b);color:var(--text-muted);border-color:var(--border,#334155);';
    return '<button class="btn" style="font-size:12px;padding:4px 10px;' + act + '" '
      + 'onclick="window._outboundViewMode=\\'' + val + '\\';window.loadOutboundPage()">' + label + '</button>';
  }

  function _renderOutboundLotTableOnly(rows, baseIdx) {
    // 그룹 내부 — 헤더 포함된 컴팩트 테이블 (LOT/판매주문/고객사/톤백/중량/출고일)
    var html = '<table class="data-table" style="margin:0;font-size:12px"><thead><tr>'
      + '<th>#</th><th>LOT No</th><th style="width:32px">⋯</th><th>판매주문No</th><th>고객사</th>'
      + '<th>톤백수</th><th>중량(kg)</th><th>출고일</th>'
      + '</tr></thead><tbody>';
    rows.forEach(function(r, i) {
      var lot = escapeHtml(r.lot_no || '');
      html += '<tr class="outbound-summary-row" data-lot="' + lot + '" style="cursor:pointer" '
        + 'onclick="window.toggleOutboundDetail(\\'' + lot + '\\')">'
        + '<td class="mono-cell" style="color:var(--text-muted)">' + ((baseIdx||0) + i + 1) + '</td>'
        + '<td class="mono-cell" style="color:var(--accent);font-weight:600">' + lot + '</td>'
        + '<td style="text-align:center;padding:3px 4px;width:32px">'
        + '<button class="btn btn-ghost btn-xs" data-lot="' + lot + '" '
        + 'onclick="event.stopPropagation();window.showOutboundActionMenu(this)" '
        + 'style="font-size:15px;padding:0 4px;letter-spacing:1px" title="추가기능">⋯</button></td>'
        + '<td class="mono-cell">' + escapeHtml(r.sales_order_no || '-') + '</td>'
        + '<td>' + escapeHtml(r.customer || '-') + '</td>'
        + '<td class="mono-cell" style="text-align:right">' + (r.tonbag_count || 0) + '</td>'
        + '<td class="mono-cell" style="text-align:right">' + (r.total_kg != null ? fmtN(r.total_kg) : '-') + '</td>'
        + '<td class="mono-cell">' + escapeHtml(r.sold_date || '-') + '</td>'
        + '</tr>';
    });
    return html + '</tbody></table>';
  }

  function _renderOutboundGroup(rows, keyFn, labelPrefix, prefixId) {
    var groups = {};
    rows.forEach(function(r) {
      var k = keyFn(r) || '(미지정)';
      if (!groups[k]) groups[k] = [];
      groups[k].push(r);
    });
    var keys = Object.keys(groups).sort(function(a, b) {
      if (a.indexOf('미지정') >= 0) return 1;
      if (b.indexOf('미지정') >= 0) return -1;
      // 출고일은 최신 우선
      if (prefixId === 'od') return b.localeCompare(a);
      return a.localeCompare(b);
    });
    var html = '';
    keys.forEach(function(k, idx) {
      var lots = groups[k];
      var sumTonbag = 0, sumKg = 0;
      lots.forEach(function(r) {
        if (r.tonbag_count != null) sumTonbag += Number(r.tonbag_count) || 0;
        if (r.total_kg != null) sumKg += Number(r.total_kg) || 0;
      });
      var groupId = 'ogrp-' + prefixId + '-' + idx;
      html += '<div style="margin-bottom:12px;border:1px solid var(--border,#334155);border-radius:8px;overflow:hidden">'
        + '<div style="display:flex;align-items:center;gap:10px;padding:10px 14px;background:var(--surface,#1e293b);cursor:pointer;flex-wrap:wrap" '
        + 'onclick="(function(){var t=document.getElementById(\\'' + groupId + '\\');if(t)t.style.display=t.style.display===\\'none\\'?\\'block\\':\\'none\\';})()">'
        + '<strong style="color:#4caf50;font-family:monospace">' + escapeHtml(labelPrefix + k) + '</strong>'
        + '<span style="font-size:12px;color:var(--text-muted)">' + lots.length + ' LOT</span>'
        + '<span style="font-size:12px;color:var(--text-muted)">톤백 ' + sumTonbag + '개</span>'
        + '<span style="font-size:12px;color:var(--text-muted)">중량 ' + fmtN(sumKg) + ' kg</span>'
        + '</div>'
        + '<div id="' + groupId + '" style="display:block">'
        + _renderOutboundLotTableOnly(lots, 0)
        + '</div>'
        + '</div>';
    });
    return html;
  }

  function loadOutboundPage() {"""


# -----------------------------------------------------------------------------
# (2) 헤더 — 모드 토글 버튼 3개 삽입
#     원본:  '<div style="margin-left:auto;display:flex;gap:8px;align-items:center">',
#     패치:  같은 라인 + 그 앞에 그룹 토글 버튼들
# -----------------------------------------------------------------------------
HEADER_ANCHOR = (
    "      '<div style=\"display:flex;align-items:center;gap:8px;flex-wrap:wrap;padding:8px 0 12px\">',\n"
    "      '  <h2 style=\"margin:0\">📤 출고 완료 (Sold / Outbound)</h2>',\n"
    "      '  <div style=\"margin-left:auto;display:flex;gap:8px;align-items:center\">',\n"
    "      '    <button class=\"btn btn-primary\" onclick=\"window.showOutboundPickingModal()\" style=\"font-weight:600\">📋 Picking List 업로드</button>',\n"
    "      '    <button class=\"btn\" onclick=\"window.allocRevertStep(\\'SOLD\\')\" style=\"font-size:12px\" title=\"SOLD 상태를 PICKED로 되돌립니다\">↩ SOLD &rarr; PICKED</button>',\n"
    "      '    <button class=\"btn btn-secondary\" onclick=\"renderPage(\\'outbound\\')\">🔁 새로고침</button>',\n"
    "      '  </div>',\n"
    "      '</div>',"
)

HEADER_PATCH_LINES = [
    "      '<div style=\"display:flex;align-items:center;gap:8px;flex-wrap:wrap;padding:8px 0 12px\">',",
    "      '  <h2 style=\"margin:0\">📤 출고 완료 (Sold / Outbound)</h2>',",
    # 모드 토글 (v868 fix 2026-05-16)
    "      '  <div style=\"display:flex;gap:4px;margin-left:12px\">' + ",
    "         _outboundModeBtn('lot', 'LOT별', _outMode) + ",
    "         _outboundModeBtn('customer', '고객사별', _outMode) + ",
    "         _outboundModeBtn('date', '출고일별', _outMode) + ",
    "      '  </div>',",
    "      '  <div style=\"margin-left:auto;display:flex;gap:8px;align-items:center\">',",
    "      '    <button class=\"btn btn-primary\" onclick=\"window.showOutboundPickingModal()\" style=\"font-weight:600\">📋 Picking List 업로드</button>',",
    "      '    <button class=\"btn\" onclick=\"window.allocRevertStep(\\'SOLD\\')\" style=\"font-size:12px\" title=\"SOLD 상태를 PICKED로 되돌립니다\">↩ SOLD &rarr; PICKED</button>',",
    "      '    <button class=\"btn btn-secondary\" onclick=\"renderPage(\\'outbound\\')\">🔁 새로고침</button>',",
    "      '  </div>',",
    "      '</div>',",
]
HEADER_PATCH = "\n".join(HEADER_PATCH_LINES)


# -----------------------------------------------------------------------------
# (3) loadOutboundPage 본문 시작부 — _outMode 로컬 변수 선언 (헤더 내 .join 식에서 참조)
#     원본:  var route = window.getCurrentRoute();
#            var c = document.getElementById('page-container');
#            if (!c) return;
#            c.innerHTML = [
#     패치:  if (!c) return; 다음에 _outMode 선언 후 c.innerHTML = [...] 호출
# -----------------------------------------------------------------------------
MODE_VAR_ANCHOR = (
    "  function loadOutboundPage() {\n"
    "    var route = window.getCurrentRoute();\n"
    "    var c = document.getElementById('page-container');\n"
    "    if (!c) return;\n"
    "    c.innerHTML = ["
)

MODE_VAR_PATCH = (
    "  function loadOutboundPage() {\n"
    "    var route = window.getCurrentRoute();\n"
    "    var c = document.getElementById('page-container');\n"
    "    if (!c) return;\n"
    "    // v868 fix (2026-05-16): 그룹화 모드 — 헤더 토글 버튼이 참조\n"
    "    var _outMode = window._outboundViewMode || 'lot';\n"
    "    c.innerHTML = ["
)


# -----------------------------------------------------------------------------
# (4) 데이터 렌더 분기 — apiGet then() 콜백 내부
#     원본 (tbody 채우기 직전 if (!rows.length) 블록 다음):
#       var tbody = document.getElementById('outbound-tbody');
#       if (tbody) tbody.innerHTML = rows.map(...).join('');
#       document.getElementById('outbound-table').style.display = '';
#     패치: 그룹 모드면 page-container 안에 그룹 HTML 주입 후 return
# -----------------------------------------------------------------------------
RENDER_ANCHOR = (
    "      if (!rows.length) {\n"
    "        document.getElementById('outbound-empty').style.display = 'block';\n"
    "        return;\n"
    "      }\n"
    "      var tbody = document.getElementById('outbound-tbody');"
)

RENDER_PATCH = (
    "      if (!rows.length) {\n"
    "        document.getElementById('outbound-empty').style.display = 'block';\n"
    "        return;\n"
    "      }\n"
    "      // v868 fix (2026-05-16): 그룹 모드 분기 — 고객사별/출고일별\n"
    "      if (_outMode === 'customer' || _outMode === 'date') {\n"
    "        var tbl = document.getElementById('outbound-table');\n"
    "        if (tbl) tbl.style.display = 'none';\n"
    "        var groupHtml;\n"
    "        if (_outMode === 'customer') {\n"
    "          groupHtml = _renderOutboundGroup(rows, function(r){ return r.customer || ''; }, '고객사: ', 'oc');\n"
    "        } else {\n"
    "          groupHtml = _renderOutboundGroup(rows, function(r){ return (r.sold_date || '').slice(0,10); }, '출고일: ', 'od');\n"
    "        }\n"
    "        var sec = c.querySelector('section[data-page=\"outbound\"]');\n"
    "        var holder = document.createElement('div');\n"
    "        holder.id = 'outbound-group-wrap';\n"
    "        holder.style.padding = '4px 0 16px';\n"
    "        holder.innerHTML = groupHtml;\n"
    "        var existing = document.getElementById('outbound-group-wrap');\n"
    "        if (existing) existing.remove();\n"
    "        if (sec) sec.appendChild(holder); else c.appendChild(holder);\n"
    "        dbgLog('📤','outbound-page','mode=' + _outMode + ' groups rendered','#4caf50');\n"
    "        return;\n"
    "      }\n"
    "      var tbody = document.getElementById('outbound-tbody');"
)


# -----------------------------------------------------------------------------
PATCHES = [
    ("(H) 헬퍼 + 모드 변수", HELPER_ANCHOR, HELPER_PATCH),
    ("(M) 헤더 모드 토글",   HEADER_ANCHOR, HEADER_PATCH),
    ("(V) _outMode 변수",    MODE_VAR_ANCHOR, MODE_VAR_PATCH),
    ("(R) 렌더 분기",         RENDER_ANCHOR, RENDER_PATCH),
]


def apply_patch(file_path: Path, anchor: str, patch: str, label: str) -> bool:
    text = file_path.read_text(encoding="utf-8")
    if patch in text:
        print(f"  [SKIP] {label} — already patched.")
        return True
    if anchor not in text:
        print(f"  [ERROR] {label} — anchor not found.")
        return False
    if text.count(anchor) > 1:
        print(f"  [ERROR] {label} — anchor matched {text.count(anchor)} times.")
        return False
    new_text = text.replace(anchor, patch, 1)
    if not new_text.rstrip().endswith("})();"):
        print(f"  [ERROR] {label} IIFE closing lost.")
        return False
    file_path.write_text(new_text, encoding="utf-8")
    print(f"  [OK] {label} applied.")
    return True


def main() -> int:
    if not TARGET.exists():
        print(f"[ERROR] target not found: {TARGET}")
        return 1

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = TARGET.with_suffix(f".js.bak_outbound_group_{ts}")
    shutil.copy2(TARGET, backup)
    print(f"[INFO] backup: {backup.name}")
    print()

    ok = True
    for label, anchor, patch in PATCHES:
        print(f"=== {label} ===")
        ok &= apply_patch(TARGET, anchor, patch, label)
        print()

    if not ok:
        print("[FAIL] 일부 패치 미적용 — 검토 필요")
        return 2

    # syntax check
    r = subprocess.run(["node", "--check", str(TARGET)], capture_output=True, text=True)
    if r.returncode != 0:
        print(f"[FAIL] node --check 실패:\n{r.stderr}")
        return 3
    print("[OK] node --check syntax OK")
    print()
    print("🎉 Outbound 그룹화 (LOT/고객사/출고일) 추가 완료")
    return 0


if __name__ == "__main__":
    sys.exit(main())
