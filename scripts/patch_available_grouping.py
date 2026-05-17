# -*- coding: utf-8 -*-
"""
patch_available_grouping.py
============================
Purpose: Available 탭에 LOT별/컨테이너별/입고일별 그룹화 모드 추가
Why    : 사용자 요청 — Pending처럼 그룹화 선택 가능하게
Method : Pending 패턴(_pendingViewMode + _renderPendingGroupRows) 차용
         Available 전용 변수 _availViewMode + 그룹화 함수 신규
Rule   : CLAUDE.md Rule 5 — Python 스크립트만
Author : Ruby (Senior Software Architect) — 2026-05-16
"""
import sys
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
TARGET = ROOT / "frontend" / "js" / "sqm-inventory.js"

# Available 페이지 헤더에 모드 토글 + 그룹화 분기 추가
# 현재 헤더: [✅ Available] [LOT 수·Balance] [Excel내보내기][새로고침]
HEADER_ANCHOR = """      var html = '<section style="padding:12px 16px">'
        + '<div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;flex-wrap:wrap">'
        + '<h2 style="margin:0;font-size:16px;color:#22c55e">✅ Available 재고 — 판매 가능 물량</h2>'
        + '<span style="font-size:12px;color:var(--text-muted)">' + rows.length + ' LOT · Balance ' + fmtN(sumBal) + ' MT</span>'
        + '<button class="btn btn-secondary" style="font-size:12px" onclick="window.exportAvailableExcel()" title="현재 화면 Available 데이터를 Excel로 내보냅니다">📊 Excel 내보내기</button>'
        + '<button class="btn btn-ghost" style="font-size:12px" onclick="window.loadAvailablePage()">🔄 새로고침</button>'
        + '</div>'"""

HEADER_PATCH = """      // v868 fix (2026-05-16): Available에 그룹화 모드 추가 (LOT/컨테이너/입고일)
      var availMode = window._availViewMode || 'lot';
      var _availModeBtn = function(val, label, cur) {
        var act = val === cur
          ? 'background:var(--accent,#3b82f6);color:#fff;border-color:var(--accent,#3b82f6);'
          : 'background:var(--surface,#1e293b);color:var(--text-muted);border-color:var(--border,#334155);';
        return '<button class="btn" style="font-size:12px;padding:4px 10px;' + act + '" '
          + 'onclick="window._availViewMode=\\'' + val + '\\';window.loadAvailablePage()">' + label + '</button>';
      };
      var html = '<section style="padding:12px 16px">'
        + '<div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;flex-wrap:wrap">'
        + '<h2 style="margin:0;font-size:16px;color:#22c55e">✅ Available 재고 — 판매 가능 물량</h2>'
        + '<span style="font-size:12px;color:var(--text-muted)">' + rows.length + ' LOT · Balance ' + fmtN(sumBal) + ' MT</span>'
        + '<div style="display:flex;gap:4px;margin-left:8px">'
        + _availModeBtn('lot', 'LOT별', availMode)
        + _availModeBtn('container', '컨테이너별', availMode)
        + _availModeBtn('date', '입고일별', availMode)
        + '</div>'
        + '<button class="btn btn-secondary" style="font-size:12px" onclick="window.exportAvailableExcel()" title="현재 화면 Available 데이터를 Excel로 내보냅니다">📊 Excel 내보내기</button>'
        + '<button class="btn btn-ghost" style="font-size:12px" onclick="window.loadAvailablePage()">🔄 새로고침</button>'
        + '</div>'"""


# 테이블 렌더링 분기 추가 — `+ '<div style="overflow-x:auto"><table class="data-table"><thead>...`
# 모드에 따라 컨테이너별/입고일별 그룹 렌더링 또는 LOT별 (기존) 렌더링
GROUP_HELPER = '''
  // v868 fix (2026-05-16): Available 그룹화 헬퍼 — Pending 패턴 차용
  function _renderAvailableGroup(rows, keyFn, labelPrefix) {
    var groups = {};
    rows.forEach(function(r) {
      var k = keyFn(r) || '(미지정)';
      if (!groups[k]) groups[k] = [];
      groups[k].push(r);
    });
    var keys = Object.keys(groups).sort();
    var html = '';
    keys.forEach(function(k, idx) {
      var lots = groups[k];
      var sumNet = 0;
      lots.forEach(function(r){ if (r.net != null) sumNet += Number(r.net); });
      var groupId = 'avg-' + idx;
      html += '<div style="margin-bottom:12px;border:1px solid var(--border,#334155);border-radius:8px;overflow:hidden">'
        + '<div style="display:flex;align-items:center;gap:10px;padding:10px 14px;background:var(--surface,#1e293b);cursor:pointer" '
        + 'onclick="(function(el){var t=document.getElementById(\\'' + groupId + '\\');if(t)t.style.display=t.style.display===\\'none\\'?\\'block\\':\\'none\\';})(this)">'
        + '<strong style="color:#22c55e;font-family:monospace">' + escapeHtml(labelPrefix + k) + '</strong>'
        + '<span style="font-size:12px;color:var(--text-muted)">' + lots.length + ' LOT · ' + fmtN(sumNet) + ' MT</span>'
        + '</div>'
        + '<div id="' + groupId + '" style="display:block">'
        + _renderAvailLotTableOnly(lots)
        + '</div>'
        + '</div>';
    });
    return html;
  }

  // LOT별 모드의 테이블 body만 렌더 (그룹 내부용)
  function _renderAvailLotTableOnly(rows) {
    // 그룹 내부에서는 헤더 없이 행만 렌더링 — 기존 mainRow 로직 재사용 필요
    // 임시: 간단한 LOT 목록 표시
    var html = '<table class="data-table" style="margin:0;font-size:12px"><thead><tr>'
      + '<th>LOT</th><th>SAP</th><th>Product</th><th>Container</th><th>Vessel</th><th>NET(MT)</th><th>Arrival</th><th>WH</th>'
      + '</tr></thead><tbody>';
    rows.forEach(function(r) {
      html += '<tr>'
        + '<td class="mono-cell" style="color:var(--accent);font-weight:600">' + escapeHtml(r.lot||'') + '</td>'
        + '<td class="mono-cell">' + escapeHtml(r.sap||'-') + '</td>'
        + '<td><span class="tag">' + escapeHtml(r.product||'-') + '</span></td>'
        + '<td class="mono-cell">' + escapeHtml(r.container||'-') + '</td>'
        + '<td class="mono-cell">' + escapeHtml(r.vessel||'-') + '</td>'
        + '<td class="mono-cell" style="text-align:right">' + (r.net!=null?fmtN(r.net):'-') + '</td>'
        + '<td class="mono-cell">' + escapeHtml((r.arrival_date||'').slice(0,10) || '-') + '</td>'
        + '<td class="mono-cell">' + escapeHtml(r.wh||'-') + '</td>'
        + '</tr>';
    });
    return html + '</tbody></table>';
  }

'''

# GROUP_HELPER을 loadAvailablePage 직전에 삽입
HELPER_ANCHOR = """  /* ===================================================
     7a-2. PAGE: Available (AVAILABLE 톤백 필터 뷰) — v9.5
     =================================================== */
  function loadAvailablePage() {"""

HELPER_PATCH = GROUP_HELPER + """  /* ===================================================
     7a-2. PAGE: Available (AVAILABLE 톤백 필터 뷰) — v9.5
     =================================================== */
  function loadAvailablePage() {"""


# 모드별 분기: 기존 LOT별 테이블 코드 앞에 모드 체크 추가
# 기존: + '<div style="overflow-x:auto"><table class="data-table"><thead><tr>'  (line ~759)
# 패치: 컨테이너/날짜 모드면 그룹 렌더 후 return; 아니면 기존 코드 진행
TABLE_ANCHOR = """        // v868 fix (2026-05-16 옵션B): Pending과 동일한 15컬럼 헤더
        // 톤백 상세(Available/Reserved/Packed 등)는 우클릭 메뉴 "톤백 상세"에서 접근
        + '<div style="overflow-x:auto"><table class="data-table"><thead><tr>'"""

TABLE_PATCH = """        // v868 fix (2026-05-16): 모드별 분기 — 그룹 모드는 별도 렌더
        ;
      if (availMode === 'container') {
        c.innerHTML = html + _renderAvailableGroup(rows, function(r){ return r.container || ''; }, '컨테이너: ') + '</section>';
        return;
      }
      if (availMode === 'date') {
        c.innerHTML = html + _renderAvailableGroup(rows, function(r){ return (r.date || r.inbound_date || '').slice(0,10); }, '입고일: ') + '</section>';
        return;
      }
      // LOT별 모드 (기본) — 기존 28컬럼 테이블 렌더링 계속
      html = html
        // v868 fix (2026-05-16 옵션B): Pending과 동일한 15컬럼 헤더
        // 톤백 상세(Available/Reserved/Packed 등)는 우클릭 메뉴 "톤백 상세"에서 접근
        + '<div style="overflow-x:auto"><table class="data-table"><thead><tr>'"""


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
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = TARGET.with_suffix(f".js.bak_avail_group_{ts}")
    shutil.copy2(TARGET, backup)
    print(f"[INFO] backup: {backup.name}")
    print()

    ok = True
    print("=== 그룹화 헬퍼 함수 추가 ===")
    ok &= apply_patch(TARGET, HELPER_ANCHOR, HELPER_PATCH, "(H) 헬퍼")
    print()
    print("=== 헤더에 모드 토글 추가 ===")
    ok &= apply_patch(TARGET, HEADER_ANCHOR, HEADER_PATCH, "(M) 모드 토글")
    print()
    print("=== 테이블 분기 추가 ===")
    ok &= apply_patch(TARGET, TABLE_ANCHOR, TABLE_PATCH, "(B) 분기")

    if not ok:
        return 2

    print()
    r = subprocess.run(["node", "--check", str(TARGET)], capture_output=True, text=True)
    if r.returncode != 0:
        print(f"[FAIL] {r.stderr}")
        return 3
    print("[OK] syntax OK")
    print()
    print("🎉 Available 그룹화 (LOT/컨테이너/입고일) 추가 완료")
    return 0


if __name__ == "__main__":
    sys.exit(main())
