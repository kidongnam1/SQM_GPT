# -*- coding: utf-8 -*-
"""
patch_allocation_grouping.py
=============================
Purpose: Allocation 탭에 LOT별/컨테이너별/입고일별 그룹화 모드 추가
Why    : 사용자 요청 — Pending/Available처럼 그룹화 선택 가능하게
Method : Pending 패턴(_pendingViewMode + _renderPendingGroupRows) 차용
         Allocation 전용 변수 _allocViewMode + 그룹화 함수 신규
Rule   : CLAUDE.md Rule 5 — sqm-inline.js (7523줄 IIFE) Python 스크립트만
Idempotent: 이미 패치되어 있으면 SKIP
Author : Ruby (Senior Software Architect) — 2026-05-16
"""
import sys
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
TARGET = ROOT / "frontend" / "js" / "sqm-inline.js"

# ─────────────────────────────────────────────────────────────
# 1) HEADER: 모드 토글 버튼 3개를 알림 제목 옆에 삽입
# ─────────────────────────────────────────────────────────────
HEADER_ANCHOR = (
    "      '<div class=\"alloc-header\" style=\"display:flex;align-items:center;gap:8px;flex-wrap:wrap;padding:8px 0 12px\">',\n"
    "      '  <h2 style=\"margin:0;font-size:16px\">📋 판매 배정 (Allocation)</h2>',\n"
    "      '  <span id=\"alloc-summary-label\" style=\"color:var(--text-muted);font-size:12px\"></span>',\n"
    "      '  <div style=\"margin-left:auto;display:flex;gap:6px;align-items:center;flex-wrap:wrap\">',\n"
)

HEADER_PATCH = (
    "      '<div class=\"alloc-header\" style=\"display:flex;align-items:center;gap:8px;flex-wrap:wrap;padding:8px 0 12px\">',\n"
    "      '  <h2 style=\"margin:0;font-size:16px\">📋 판매 배정 (Allocation)</h2>',\n"
    "      '  <span id=\"alloc-summary-label\" style=\"color:var(--text-muted);font-size:12px\"></span>',\n"
    "      /* v868 fix (2026-05-16): Allocation 그룹화 모드 토글 (LOT/컨테이너/입고일) */\n"
    "      '  <div style=\"display:flex;gap:4px;margin-left:8px\">',\n"
    "      '    ' + _allocModeBtn('lot', 'LOT별'),\n"
    "      '    ' + _allocModeBtn('container', '컨테이너별'),\n"
    "      '    ' + _allocModeBtn('date', '입고일별'),\n"
    "      '  </div>',\n"
    "      '  <div style=\"margin-left:auto;display:flex;gap:6px;align-items:center;flex-wrap:wrap\">',\n"
)

# ─────────────────────────────────────────────────────────────
# 2) STATE: _allocState 선언 직후에 _allocViewMode 추가 + 헬퍼 함수
# ─────────────────────────────────────────────────────────────
STATE_ANCHOR = (
    "  var _allocState = { currentFilter: 'all', rows: [], selectedLots: new Set() };\n"
    "  /* [Sprint 1-1-D] 편집 가능 필드 (백엔드 _ALLOC_EDITABLE_FIELDS 와 일치 필요) */\n"
    "  var ALLOC_EDITABLE_FIELDS = new Set(['customer', 'sale_ref', 'qty_mt', 'outbound_date']);\n"
)

STATE_PATCH = (
    "  var _allocState = { currentFilter: 'all', rows: [], selectedLots: new Set() };\n"
    "  /* [Sprint 1-1-D] 편집 가능 필드 (백엔드 _ALLOC_EDITABLE_FIELDS 와 일치 필요) */\n"
    "  var ALLOC_EDITABLE_FIELDS = new Set(['customer', 'sale_ref', 'qty_mt', 'outbound_date']);\n"
    "\n"
    "  /* v868 fix (2026-05-16): Allocation 그룹화 모드 (LOT/컨테이너/입고일) — Pending 패턴 차용 */\n"
    "  window._allocViewMode = window._allocViewMode || 'lot';\n"
    "  function _allocModeBtn(val, label) {\n"
    "    var cur = window._allocViewMode || 'lot';\n"
    "    var act = (val === cur)\n"
    "      ? 'background:var(--accent,#3b82f6);color:#fff;border-color:var(--accent,#3b82f6);'\n"
    "      : 'background:var(--surface,#1e293b);color:var(--text-muted);border-color:var(--border,#334155);';\n"
    "    return '<button class=\"btn\" style=\"font-size:12px;padding:4px 10px;' + act + '\" '\n"
    "      + 'onclick=\"window._allocViewMode=\\\\\\'' + val + '\\\\\\';window.renderPage(\\\\\\'allocation\\\\\\')\">' + label + '</button>';\n"
    "  }\n"
    "  function _allocKeyContainer(r) { return r.container_no || r.container || '(컨테이너 미지정)'; }\n"
    "  function _allocKeyDate(r) {\n"
    "    var d = r.inbound_date || r.arrival_date || r.stock_date || '';\n"
    "    d = (d || '').toString().slice(0, 10);\n"
    "    return d || '(입고일 미지정)';\n"
    "  }\n"
    "  function _renderAllocGroupRows(rows, keyFn, labelPrefix, prefix) {\n"
    "    var groups = {};\n"
    "    rows.forEach(function(r) {\n"
    "      var k = keyFn(r) || '(미지정)';\n"
    "      if (!groups[k]) groups[k] = [];\n"
    "      groups[k].push(r);\n"
    "    });\n"
    "    var keys = Object.keys(groups).sort(function(a, b) {\n"
    "      if (a.indexOf('미지정') >= 0) return 1;\n"
    "      if (b.indexOf('미지정') >= 0) return -1;\n"
    "      return a.localeCompare(b);\n"
    "    });\n"
    "    var html = '';\n"
    "    keys.forEach(function(k, idx) {\n"
    "      var lots = groups[k];\n"
    "      var sumMt = 0;\n"
    "      lots.forEach(function(r) {\n"
    "        var q = (r.total_mt != null) ? Number(r.total_mt) : (r.qty_mt != null ? Number(r.qty_mt) : 0);\n"
    "        if (!isNaN(q)) sumMt += q;\n"
    "      });\n"
    "      var groupId = (prefix || 'ag') + '-' + idx;\n"
    "      html += '<div style=\"margin-bottom:12px;border:1px solid var(--border,#334155);border-radius:8px;overflow:hidden\">'\n"
    "        + '<div style=\"display:flex;align-items:center;gap:10px;padding:10px 14px;background:var(--surface,#1e293b);cursor:pointer\" '\n"
    "        + 'onclick=\"window._toggleAllocGroup(\\\\\\'' + groupId + '\\\\\\')\">'\n"
    "        + '<strong style=\"color:var(--accent);font-family:monospace\">' + escapeHtml(labelPrefix + k) + '</strong>'\n"
    "        + '<span style=\"font-size:12px;color:var(--text-muted)\">' + lots.length + ' LOT · ' + sumMt.toFixed(4) + ' MT</span>'\n"
    "        + '</div>'\n"
    "        + '<div id=\"' + groupId + '\" style=\"display:block\">'\n"
    "        + _renderAllocLotTableOnly(lots)\n"
    "        + '</div>'\n"
    "        + '</div>';\n"
    "    });\n"
    "    return html;\n"
    "  }\n"
    "  function _renderAllocLotTableOnly(rows) {\n"
    "    var html = '<table class=\"data-table\" style=\"margin:0;font-size:12px\"><thead><tr>'\n"
    "      + '<th style=\"width:32px\"></th>'\n"
    "      + '<th>LOT NO</th><th>SAP NO</th><th>PRODUCT</th>'\n"
    "      + '<th style=\"text-align:right\">QTY (MT)</th>'\n"
    "      + '<th>CUSTOMER</th><th>SALE REF</th><th>OUTBOUND DATE</th><th>WH</th><th>STATUS</th>'\n"
    "      + '</tr></thead><tbody>';\n"
    "    rows.forEach(function(r) {\n"
    "      var lot = escapeHtml(r.lot_no || '');\n"
    "      var qtyMt = (r.total_mt != null) ? Number(r.total_mt) : (r.qty_mt != null ? Number(r.qty_mt) : 0);\n"
    "      var status = (r.status || 'RESERVED').toUpperCase();\n"
    "      var statusColor = status === 'SOLD' ? '#66bb6a' : status === 'PICKED' ? '#42a5f5' : 'var(--warning)';\n"
    "      var statusFg = status === 'RESERVED' ? '#000' : '#fff';\n"
    "      var checked = _allocState.selectedLots.has(lot) ? 'checked' : '';\n"
    "      html += '<tr class=\"alloc-summary-row\" data-lot=\"' + lot + '\" data-status=\"' + status + '\" '\n"
    "        + 'oncontextmenu=\"window.allocContextMenu(event, \\\\\\'' + lot + '\\\\\\'); return false;\">'\n"
    "        + '<td style=\"text-align:center\"><input type=\"checkbox\" ' + checked + ' onclick=\"event.stopPropagation();window.allocToggleRow(\\\\\\'' + lot + '\\\\\\',this.checked)\"></td>'\n"
    "        + '<td class=\"mono-cell\" style=\"color:var(--accent);font-weight:600;cursor:pointer\" onclick=\"window.toggleAllocDetail(\\\\\\'' + lot + '\\\\\\')\">'\n"
    "        + '<span class=\"alloc-expand-icon\">▶</span> ' + lot + '</td>'\n"
    "        + '<td class=\"mono-cell\">' + escapeHtml(r.sap_no || '-') + '</td>'\n"
    "        + '<td>' + escapeHtml(r.product || '-') + '</td>'\n"
    "        + '<td class=\"mono-cell\" style=\"text-align:right\">' + (qtyMt ? qtyMt.toFixed(4) : '-') + '</td>'\n"
    "        + '<td>' + escapeHtml(r.customer || r.sold_to || '-') + '</td>'\n"
    "        + '<td class=\"mono-cell\">' + escapeHtml(r.sale_ref || '-') + '</td>'\n"
    "        + '<td class=\"mono-cell\">' + escapeHtml(r.outbound_date || r.ship_date || '-') + '</td>'\n"
    "        + '<td>' + escapeHtml(r.warehouse || r.wh || '-') + '</td>'\n"
    "        + '<td><span class=\"tag\" style=\"background:' + statusColor + ';color:' + statusFg + '\">' + status + '</span></td>'\n"
    "        + '</tr>';\n"
    "    });\n"
    "    return html + '</tbody></table>';\n"
    "  }\n"
    "  window._toggleAllocGroup = function(id) {\n"
    "    var el = document.getElementById(id);\n"
    "    if (!el) return;\n"
    "    el.style.display = (el.style.display === 'none') ? 'block' : 'none';\n"
    "  };\n"
)

# ─────────────────────────────────────────────────────────────
# 3) RENDER: _renderAllocTable() 진입부에서 모드별 분기
# ─────────────────────────────────────────────────────────────
RENDER_ANCHOR = (
    "  /* ── 테이블 렌더 (필터 적용) ────────────────────────────────────── */\n"
    "  function _renderAllocTable() {\n"
    "    var filter = _allocState.currentFilter;\n"
    "    var rows = _allocState.rows.filter(function(r){\n"
    "      if (filter === 'all') return true;\n"
    "      return (r.status || 'RESERVED').toUpperCase() === filter;\n"
    "    });\n"
    "    var tbody = document.getElementById('alloc-summary-tbody');\n"
    "    var tfoot = document.getElementById('alloc-summary-tfoot');\n"
    "    var table = document.getElementById('alloc-summary-table');\n"
    "    var empty = document.getElementById('alloc-empty');\n"
    "    var lbl = document.getElementById('alloc-summary-label');\n"
    "\n"
    "    if (!rows.length) {\n"
)

RENDER_PATCH = (
    "  /* ── 테이블 렌더 (필터 적용) ────────────────────────────────────── */\n"
    "  function _renderAllocTable() {\n"
    "    var filter = _allocState.currentFilter;\n"
    "    var rows = _allocState.rows.filter(function(r){\n"
    "      if (filter === 'all') return true;\n"
    "      return (r.status || 'RESERVED').toUpperCase() === filter;\n"
    "    });\n"
    "    var tbody = document.getElementById('alloc-summary-tbody');\n"
    "    var tfoot = document.getElementById('alloc-summary-tfoot');\n"
    "    var table = document.getElementById('alloc-summary-table');\n"
    "    var empty = document.getElementById('alloc-empty');\n"
    "    var lbl = document.getElementById('alloc-summary-label');\n"
    "\n"
    "    /* v868 fix (2026-05-16): 그룹 모드 분기 — 컨테이너/입고일별이면 그룹 컨테이너에 렌더 */\n"
    "    var mode = window._allocViewMode || 'lot';\n"
    "    var grpHost = document.getElementById('alloc-group-host');\n"
    "    if (!grpHost) {\n"
    "      var pc = document.getElementById('page-container');\n"
    "      var sec = pc ? pc.querySelector('section[data-page=\"allocation\"]') : null;\n"
    "      if (sec) {\n"
    "        grpHost = document.createElement('div');\n"
    "        grpHost.id = 'alloc-group-host';\n"
    "        grpHost.style.marginTop = '6px';\n"
    "        var detailPanel = document.getElementById('alloc-detail-panel');\n"
    "        if (detailPanel) sec.insertBefore(grpHost, detailPanel);\n"
    "        else sec.appendChild(grpHost);\n"
    "      }\n"
    "    }\n"
    "    if (mode === 'container' || mode === 'date') {\n"
    "      if (!rows.length) {\n"
    "        if (table) table.style.display = 'none';\n"
    "        if (grpHost) grpHost.innerHTML = '';\n"
    "        if (empty) { empty.textContent = '📭 (' + filter + ') 배정 데이터 없음'; empty.style.display = 'block'; }\n"
    "        if (lbl) lbl.textContent = '(0/' + _allocState.rows.length + '건)';\n"
    "        return;\n"
    "      }\n"
    "      if (empty) empty.style.display = 'none';\n"
    "      if (table) table.style.display = 'none';\n"
    "      if (lbl) lbl.textContent = '(' + rows.length + '/' + _allocState.rows.length + '건)';\n"
    "      if (grpHost) {\n"
    "        if (mode === 'container') {\n"
    "          grpHost.innerHTML = _renderAllocGroupRows(rows, _allocKeyContainer, '컨테이너: ', 'agc');\n"
    "        } else {\n"
    "          grpHost.innerHTML = _renderAllocGroupRows(rows, _allocKeyDate, '입고일: ', 'agd');\n"
    "        }\n"
    "      }\n"
    "      return;\n"
    "    }\n"
    "    /* LOT 모드: 그룹 호스트 비우고 기본 테이블 사용 */\n"
    "    if (grpHost) grpHost.innerHTML = '';\n"
    "\n"
    "    if (!rows.length) {\n"
)

# ─────────────────────────────────────────────────────────────
# Patch utilities
# ─────────────────────────────────────────────────────────────
def apply_patch(file_path: Path, anchor: str, patch: str, label: str) -> bool:
    text = file_path.read_text(encoding="utf-8")
    if patch in text:
        print(f"  [SKIP] {label} — already patched.")
        return True
    if anchor not in text:
        print(f"  [ERROR] {label} — anchor not found.")
        return False
    cnt = text.count(anchor)
    if cnt > 1:
        print(f"  [ERROR] {label} — anchor matched {cnt} times (must be unique).")
        return False
    new_text = text.replace(anchor, patch, 1)
    if not new_text.rstrip().endswith("})();"):
        print("  [ERROR] " + label + " — IIFE closing lost!")
        return False
    file_path.write_text(new_text, encoding="utf-8")
    delta = len(new_text.splitlines()) - len(text.splitlines())
    print(f"  [OK] {label} applied (delta +{delta} lines).")
    return True


def main() -> int:
    if not TARGET.exists():
        print(f"[FATAL] {TARGET} not found")
        return 1

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = TARGET.with_suffix(f".js.bak_alloc_group_{ts}")
    shutil.copy2(TARGET, backup)
    print(f"[INFO] backup: {backup.name}")
    print(f"[INFO] target: {TARGET}")
    print(f"[INFO] before: {len(TARGET.read_text(encoding='utf-8').splitlines())} lines")
    print()

    ok = True
    print("=== (1) STATE + 헬퍼 함수 추가 ===")
    ok &= apply_patch(TARGET, STATE_ANCHOR, STATE_PATCH, "(S) state/헬퍼")
    print()
    print("=== (2) HEADER 모드 토글 버튼 추가 ===")
    ok &= apply_patch(TARGET, HEADER_ANCHOR, HEADER_PATCH, "(H) 헤더 토글")
    print()
    print("=== (3) RENDER 분기 추가 ===")
    ok &= apply_patch(TARGET, RENDER_ANCHOR, RENDER_PATCH, "(R) 렌더 분기")

    if not ok:
        print("\n[ABORT] one or more patches failed; restore from backup if needed.")
        return 2

    print()
    print(f"[INFO] after : {len(TARGET.read_text(encoding='utf-8').splitlines())} lines")

    # Syntax check
    print()
    print("=== node --check (syntax) ===")
    r = subprocess.run(["node", "--check", str(TARGET)], capture_output=True, text=True)
    if r.returncode != 0:
        print("[FAIL]")
        print(r.stderr)
        return 3
    print("[OK] node --check passed")

    print()
    print("🎉 Allocation 그룹화 (LOT/컨테이너/입고일) 추가 완료")
    print("   사용자 검증:")
    print("   1) Allocation 탭 진입 → 헤더에 [LOT별][컨테이너별][입고일별] 3개 버튼 표시")
    print("   2) 컨테이너별/입고일별 클릭 → 그룹 카드 + 내부 LOT 목록 확인")
    return 0


if __name__ == "__main__":
    sys.exit(main())
