# -*- coding: utf-8 -*-
"""
patch_picked_grouping.py
=========================
Purpose: Picked 탭에 LOT별/고객사별/입고일별 그룹화 모드 추가
Why    : 사용자 요청 — Pending/Available처럼 그룹화 선택 가능하게
Method : Pending 패턴(_pendingViewMode + _renderPendingGroupRows) 차용
         Picked 전용 변수 _pickedViewMode + 그룹화 함수 신규
         IIFE 패턴 보존 + 멱등성 보장
Rule   : CLAUDE.md Rule 5 — Python 스크립트만, IIFE 보존
Author : Ruby — 2026-05-16

데이터 키:
  r.lot_no, r.picking_no, r.customer (or r.picked_to),
  r.tonbag_count, r.total_kg, r.mxbg_pallet,
  r.tb_available, r.tb_reserved, r.tb_picked,
  r.avail_mt, r.reserved_mt, r.picked_mt, r.total_bags,
  r.inbound_date (없을 수 있음 → r.picking_date fallback)

그룹화 모드:
  - lot      (기본) : 기존 17컬럼 LOT 테이블
  - customer        : 고객사별 묶음
  - date            : 입고일별 묶음 (inbound_date || picking_date)
"""
import sys
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
TARGET = ROOT / "frontend" / "js" / "sqm-picked.js"


# ── (1) 헤더에 모드 토글 버튼 추가 ──────────────────────────────────
# 기존 헤더: [↩ PICKED → RESERVED][📊 Excel 내보내기][🔁 새로고침]
# 신규 헤더: 그 옆에 [LOT별][고객사별][입고일별] 추가
HEADER_ANCHOR = """  function loadPickedPage() {
    var route = window.getCurrentRoute();
    var c = document.getElementById('page-container');
    if (!c) return;
    c.innerHTML = [
      '<section class="page" data-page="picked">',
      '<div style="display:flex;align-items:center;gap:12px;padding:8px 0 12px">',
      '  <h2 style="margin:0">🚛 Picked - 피킹 완료 (화물 결정)</h2>',
      '  <div style="margin-left:auto;display:flex;gap:8px;align-items:center">',
      '    <button class="btn" onclick="window.allocRevertStep(\\'PICKED\\')" style="font-size:12px" title="PICKED 상태를 RESERVED로 되돌립니다">↩ PICKED &rarr; RESERVED</button>',
      '    <button class="btn btn-secondary" onclick="window.exportPickedExcel()" style="font-size:12px" title="현재 Picked 데이터를 Excel로 내보냅니다">📊 Excel 내보내기</button>',
      '    <button class="btn btn-secondary" onclick="renderPage(\\'picked\\')">🔁 새로고침</button>',
      '  </div>',
      '</div>',"""

HEADER_PATCH = """  function loadPickedPage() {
    var route = window.getCurrentRoute();
    var c = document.getElementById('page-container');
    if (!c) return;
    // v868 fix (2026-05-16): Picked 그룹화 모드 (LOT/고객사/입고일)
    var pickedMode = window._pickedViewMode || 'lot';
    function _pickedModeBtnHtml(val, label, cur) {
      var act = val === cur
        ? 'background:var(--accent,#3b82f6);color:#fff;border-color:var(--accent,#3b82f6);'
        : 'background:var(--surface,#1e293b);color:var(--text-muted);border-color:var(--border,#334155);';
      return '<button class="btn" style="font-size:12px;padding:4px 10px;' + act + '" '
        + 'onclick="window._pickedViewMode=\\'' + val + '\\';window.loadPickedPage()">' + label + '</button>';
    }
    c.innerHTML = [
      '<section class="page" data-page="picked">',
      '<div style="display:flex;align-items:center;gap:12px;padding:8px 0 12px;flex-wrap:wrap">',
      '  <h2 style="margin:0">🚛 Picked - 피킹 완료 (화물 결정)</h2>',
      '  <div style="display:flex;gap:4px;margin-left:8px">',
      '    ' + _pickedModeBtnHtml('lot', 'LOT별', pickedMode),
      '    ' + _pickedModeBtnHtml('customer', '고객사별', pickedMode),
      '    ' + _pickedModeBtnHtml('date', '입고일별', pickedMode),
      '  </div>',
      '  <div style="margin-left:auto;display:flex;gap:8px;align-items:center">',
      '    <button class="btn" onclick="window.allocRevertStep(\\'PICKED\\')" style="font-size:12px" title="PICKED 상태를 RESERVED로 되돌립니다">↩ PICKED &rarr; RESERVED</button>',
      '    <button class="btn btn-secondary" onclick="window.exportPickedExcel()" style="font-size:12px" title="현재 Picked 데이터를 Excel로 내보냅니다">📊 Excel 내보내기</button>',
      '    <button class="btn btn-secondary" onclick="renderPage(\\'picked\\')">🔁 새로고침</button>',
      '  </div>',
      '</div>',"""


# ── (2) tbody 렌더 분기 추가 ─────────────────────────────────────────
# 기존: rows.length 체크 후 바로 LOT 테이블 렌더
# 신규: 모드별 분기 — 그룹 모드면 별도 컨테이너에 그룹 렌더, LOT 모드는 기존 그대로
BRANCH_ANCHOR = """    apiGet('/api/q/picked-list').then(function(res){
      if (window.getCurrentRoute() !== route) return;
      var rows = extractRows(res);
      document.getElementById('picked-loading').style.display = 'none';
      if (!rows.length) { document.getElementById('picked-empty').style.display='block'; return; }
      var tbody = document.getElementById('picked-tbody');"""

BRANCH_PATCH = """    apiGet('/api/q/picked-list').then(function(res){
      if (window.getCurrentRoute() !== route) return;
      var rows = extractRows(res);
      document.getElementById('picked-loading').style.display = 'none';
      if (!rows.length) { document.getElementById('picked-empty').style.display='block'; return; }
      // v868 fix (2026-05-16): 그룹화 모드 분기 — 고객사별/입고일별이면 별도 렌더 후 return
      if (pickedMode === 'customer' || pickedMode === 'date') {
        var tblEl = document.getElementById('picked-table');
        if (tblEl) tblEl.style.display = 'none';
        var hostEl = document.getElementById('picked-empty');
        if (hostEl) { hostEl.style.display = 'none'; }
        var pageEl = document.querySelector('section[data-page="picked"]');
        var oldGrp = document.getElementById('picked-group-host');
        if (oldGrp) oldGrp.parentNode.removeChild(oldGrp);
        var grpHost = document.createElement('div');
        grpHost.id = 'picked-group-host';
        grpHost.style.marginTop = '8px';
        if (pageEl) pageEl.insertBefore(grpHost, document.getElementById('picked-detail-panel'));
        grpHost.innerHTML = window._renderPickedGroup(rows, pickedMode);
        return;
      }
      var tbody = document.getElementById('picked-tbody');"""


# ── (3) 그룹화 헬퍼 함수 추가 ────────────────────────────────────────
# 위치: loadPickedPage 함수 직전 (function loadPickedPage() { 앞)
GROUP_HELPER_ANCHOR = """  function loadPickedPage() {
    var route = window.getCurrentRoute();
    var c = document.getElementById('page-container');"""

GROUP_HELPER_PATCH = """  // v868 fix (2026-05-16): Picked 그룹화 헬퍼 — Pending 패턴 차용
  window._renderPickedGroup = function(rows, mode) {
    var groups = {};
    function keyOf(r) {
      if (mode === 'customer') return (r.customer || r.picked_to || '(고객사 미지정)');
      if (mode === 'date') {
        var d = r.inbound_date || r.picking_date || '';
        d = String(d).slice(0, 10);
        return d || '(입고일 미지정)';
      }
      return r.lot_no || '(LOT 미지정)';
    }
    rows.forEach(function(r) {
      var k = keyOf(r);
      if (!groups[k]) groups[k] = [];
      groups[k].push(r);
    });
    var keys = Object.keys(groups).sort(function(a, b) {
      if (a.indexOf('미지정') >= 0) return 1;
      if (b.indexOf('미지정') >= 0) return -1;
      // 날짜 모드는 최신순(내림차순)
      if (mode === 'date') return b.localeCompare(a);
      return a.localeCompare(b);
    });
    var labelPrefix = (mode === 'customer') ? '고객사: ' : (mode === 'date' ? '입고일: ' : 'LOT: ');
    var html = '';
    keys.forEach(function(k, idx) {
      var lots = groups[k];
      var sumBags = 0, sumKg = 0, sumAvail = 0, sumReserved = 0, sumPacked = 0;
      lots.forEach(function(r) {
        sumBags     += Number(r.tonbag_count || 0) || 0;
        sumKg       += Number(r.total_kg     || 0) || 0;
        sumAvail    += Number(r.tb_available || 0) || 0;
        sumReserved += Number(r.tb_reserved  || 0) || 0;
        sumPacked   += Number(r.tb_picked    || 0) || 0;
      });
      var groupId = 'pickg-' + idx;
      html += '<div style="margin-bottom:12px;border:1px solid var(--border,#334155);border-radius:8px;overflow:hidden">'
        + '<div style="display:flex;align-items:center;gap:10px;padding:10px 14px;background:var(--surface,#1e293b);cursor:pointer;flex-wrap:wrap" '
        + 'onclick="window._togglePickedGroup(\\'' + groupId + '\\')">'
        + '<strong style="color:#3b82f6;font-family:monospace">' + escapeHtml(labelPrefix + k) + '</strong>'
        + '<span style="font-size:12px;color:var(--text-muted)">' + lots.length + ' LOT · ' + sumBags + ' Bags · ' + fmtN(sumKg) + ' kg</span>'
        + '<span style="font-size:11px;color:var(--text-muted);margin-left:auto">'
        + '<span style="color:#22c55e">A ' + sumAvail + '</span> · '
        + '<span style="color:#3b82f6">R ' + sumReserved + '</span> · '
        + '<span style="color:#f59e0b">P ' + sumPacked + '</span>'
        + '</span>'
        + '</div>'
        + '<div id="' + groupId + '" style="display:block">'
        + _renderPickedLotTableOnly(lots)
        + '</div>'
        + '</div>';
    });
    return html;
  };

  window._togglePickedGroup = function(id) {
    var el = document.getElementById(id);
    if (!el) return;
    el.style.display = el.style.display === 'none' ? 'block' : 'none';
  };

  // 그룹 내부용 LOT 표 (헤더 포함, 컴팩트)
  function _renderPickedLotTableOnly(rows) {
    var html = '<div style="overflow-x:auto"><table class="data-table" style="margin:0;font-size:12px"><thead><tr>'
      + '<th style="text-align:center">LOT No</th>'
      + '<th>피킹No</th><th>고객사</th>'
      + '<th style="text-align:right">톤백수</th><th style="text-align:right">중량(kg)</th>'
      + '<th style="text-align:center">MXBG</th>'
      + '<th style="text-align:center">Available</th>'
      + '<th style="text-align:center">Reserved</th>'
      + '<th style="text-align:center">Packed</th>'
      + '<th>Title Transfer</th>'
      + '<th style="width:32px;text-align:center">⋯</th>'
      + '</tr></thead><tbody>';
    rows.forEach(function(r) {
      var lot = escapeHtml(r.lot_no || '');
      var availBags = Number(r.tb_available || 0) || 0;
      var reservedBags = Number(r.tb_reserved || 0) || 0;
      var packedBags = Number(r.tb_picked || 0) || 0;
      html += '<tr class="picked-summary-row" data-lot="' + lot + '" style="cursor:pointer" onclick="window.togglePickedDetail(\\'' + lot + '\\')">'
        + '<td class="mono-cell cell-left" style="color:var(--accent);font-weight:600">' + lot + '</td>'
        + '<td class="mono-cell">' + escapeHtml(r.picking_no || '') + '</td>'
        + '<td>' + escapeHtml(r.customer || r.picked_to || '') + '</td>'
        + '<td class="mono-cell" style="text-align:right">' + (r.tonbag_count || 0) + '</td>'
        + '<td class="mono-cell" style="text-align:right">' + (r.total_kg != null ? fmtN(r.total_kg) : '-') + '</td>'
        + '<td class="mono-cell" style="text-align:center">' + (r.mxbg_pallet != null ? r.mxbg_pallet : '-') + '</td>'
        + '<td class="mono-cell" style="text-align:center;color:#22c55e;font-weight:700">' + availBags + '</td>'
        + '<td class="mono-cell" style="text-align:center;color:#3b82f6;font-weight:700">' + reservedBags + '</td>'
        + '<td class="mono-cell" style="text-align:center;color:#f59e0b;font-weight:700">' + packedBags + '</td>'
        + '<td class="mono-cell">' + escapeHtml(r.picking_date || '') + '</td>'
        + '<td style="text-align:center;padding:3px 4px"><button class="btn btn-ghost btn-xs" data-lot="' + lot + '" onclick="event.stopPropagation();window.showPickedActionMenu(this)" style="font-size:15px;padding:0 4px;letter-spacing:1px" title="추가기능">⋯</button></td>'
        + '</tr>';
    });
    return html + '</tbody></table></div>';
  }

  function loadPickedPage() {
    var route = window.getCurrentRoute();
    var c = document.getElementById('page-container');"""


def apply_patch(file_path: Path, anchor: str, patch: str, label: str) -> bool:
    text = file_path.read_text(encoding="utf-8")
    if patch in text:
        print(f"  [SKIP] {label} -- already patched.")
        return True
    if anchor not in text:
        print(f"  [ERROR] {label} -- anchor not found.")
        return False
    cnt = text.count(anchor)
    if cnt > 1:
        print(f"  [ERROR] {label} -- anchor matched {cnt} times (not unique).")
        return False
    new_text = text.replace(anchor, patch, 1)
    if not new_text.rstrip().endswith("})();"):
        print(f"  [ERROR] {label} -- IIFE closing lost.")
        return False
    file_path.write_text(new_text, encoding="utf-8")
    print(f"  [OK] {label} applied.")
    return True


def main() -> int:
    if not TARGET.exists():
        print(f"[FATAL] Target not found: {TARGET}")
        return 1
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = TARGET.with_suffix(f".js.bak_picked_group_{ts}")
    shutil.copy2(TARGET, backup)
    print(f"[INFO] backup: {backup.name}")
    print()

    ok = True
    # 순서 중요: 헬퍼 먼저(함수 선언) → 헤더(모드 버튼) → 브랜치(렌더 분기)
    print("=== (1/3) 그룹화 헬퍼 함수 추가 (loadPickedPage 직전) ===")
    ok &= apply_patch(TARGET, GROUP_HELPER_ANCHOR, GROUP_HELPER_PATCH, "(H) 그룹 헬퍼")
    print()
    print("=== (2/3) 헤더에 모드 토글 버튼 추가 ===")
    ok &= apply_patch(TARGET, HEADER_ANCHOR, HEADER_PATCH, "(M) 모드 토글")
    print()
    print("=== (3/3) tbody 렌더 분기 추가 ===")
    ok &= apply_patch(TARGET, BRANCH_ANCHOR, BRANCH_PATCH, "(B) 렌더 분기")

    if not ok:
        print("[FAIL] 일부 패치 실패 -- 백업 복원 권장")
        return 2

    print()
    print("=== node --check ===")
    r = subprocess.run(["node", "--check", str(TARGET)], capture_output=True, text=True)
    if r.returncode != 0:
        print(f"[FAIL] syntax error:\n{r.stderr}")
        return 3
    print("[OK] syntax OK")
    print()
    print("Picked 그룹화 (LOT/고객사/입고일) 추가 완료")
    print("  - window._pickedViewMode : 'lot' (default) / 'customer' / 'date'")
    print("  - window._renderPickedGroup(rows, mode)")
    print("  - window._togglePickedGroup(id)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
