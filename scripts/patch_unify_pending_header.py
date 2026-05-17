# -*- coding: utf-8 -*-
"""
patch_unify_pending_header.py
==============================
Purpose: Pending 테이블 헤더 + 행을 Available 28컬럼과 통일
Why    : 사용자 요청 — "Available 테이블 헤더 기준으로 순서 및 포함되는 데이터 헤더 열을 맞춰줘"
Result : 두 탭의 헤더가 완전히 일치 → 시각 일관성 100%
Note   : Pending 단계에서 의미 없는 컬럼은 "-" 표시
         (Reserved, Packed, AV/VR/AR, Inbound(MT), Location, Customs 등)
Rule   : CLAUDE.md Rule 5 — sqm-inventory.js Python 스크립트만
Author : Ruby (Senior Software Architect) — 2026-05-16
"""
import sys
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
TARGET = ROOT / "frontend" / "js" / "sqm-inventory.js"

ANCHOR = """  function _renderPendingLotRows(rows) {
    var html = '<div style="overflow-x:auto"><table class="data-table"><thead><tr>'
      + '<th><input type="checkbox" id="pending-select-all" onchange="window.pendingToggleAll(this)"></th>'
      + '<th>LOT</th><th>Product</th><th>Grade</th>'
      + '<th>Qty</th><th>Unit</th><th>BL No</th><th>Container</th><th>Vessel</th>'
      + '<th>Arrival Date</th><th>등록일</th><th style="width:50px">⚙️</th>'
      + '</tr></thead><tbody>';
    html += rows.map(function(r) {
      return '<tr>'
        + '<td style="text-align:center"><input type="checkbox" class="pending-cb" data-lot="' + escapeHtml(r.lot_no||'') + '"></td>'
        + '<td class="mono-cell" style="color:#94a3b8;font-weight:600">' + escapeHtml(r.lot_no||'') + '</td>'
        + '<td><span class="tag">' + escapeHtml(r.product||'-') + '</span></td>'
        + '<td class="mono-cell">' + escapeHtml(r.grade||'-') + '</td>'
        + '<td class="mono-cell" style="text-align:right">' + (r.quantity!=null?fmtN(r.quantity):(r.net_weight!=null?fmtN(r.net_weight):'-')) + '</td>'
        + '<td class="mono-cell">' + escapeHtml(r.unit||'-') + '</td>'
        + '<td class="mono-cell">' + escapeHtml(r.bl_no||'-') + '</td>'
        + '<td class="mono-cell">' + escapeHtml(r.container_no||'-') + '</td>'
        + '<td class="mono-cell">' + escapeHtml(r.vessel||'-') + '</td>'
        + '<td class="mono-cell">' + escapeHtml(r.arrival_date||'-') + '</td>'
        + '<td class="mono-cell" style="color:var(--text-muted)">' + escapeHtml((r.created_at||'').slice(0,10)) + '</td>'
        + '<td style="text-align:center"><button class="btn btn-ghost" style="padding:2px 8px;font-size:13px" '
        + 'onclick="window.showPendingActionMenu(event,' + JSON.stringify(r.lot_no) + ')">⋯</button></td>'
        + '</tr>';
    }).join('');
    return html + '</tbody></table></div>';
  }"""

# Available 28컬럼과 동일한 헤더 + 행 매핑
# v868 fix (2026-05-16): Pending 헤더를 Available과 통일 (28컬럼)
PATCH = """  function _renderPendingLotRows(rows) {
    // v868 fix (2026-05-16): Pending 헤더를 Available 28컬럼과 통일
    // 데이터 없는 칸(Pending 단계에서 의미 없는 것)은 "-" 표시
    var html = '<div style="overflow-x:auto"><table class="data-table"><thead><tr>'
      + '<th style="width:28px;text-align:center"><input type="checkbox" id="pending-select-all" onchange="window.pendingToggleAll(this)" title="전체 선택"></th>'
      + '<th>#</th><th style="text-align:center">LOT</th><th style="width:32px;text-align:center">+</th><th>SAP</th><th>BL</th><th>Product</th>'
      + '<th>Status</th><th style="text-align:center;color:#94a3b8" title="입고 확정 → AVAILABLE">✅</th>'
      + '<th>Balance(MT)</th><th>NET(MT)</th><th>Container</th>'
      + '<th>MXBG</th><th>Available</th><th>Reserved</th><th>Packed</th><th>Total Bags</th><th>Remain Bags</th><th>AV</th><th>VR</th><th>AR</th><th>Invoice</th>'
      + '<th>Ship</th><th>Arrival</th><th>WH</th><th>Customs</th>'
      + '<th>Inbound(MT)</th><th>Location</th>'
      + '</tr></thead><tbody>';
    html += rows.map(function(r, i) {
      var lotSafe = escapeHtml(r.lot_no || '');
      var netMt = r.net_weight != null ? fmtN(r.net_weight / 1000) : '-';
      return '<tr>'
        // 1: 체크박스
        + '<td style="text-align:center;padding:3px 6px"><input type="checkbox" class="pending-cb" data-lot="' + lotSafe + '"></td>'
        // 2: # (순번)
        + '<td class="mono-cell" style="color:var(--text-muted)">' + (i+1) + '</td>'
        // 3: LOT
        + '<td class="mono-cell cell-left" style="color:#94a3b8;font-weight:600;padding:6px 10px">' + lotSafe + '</td>'
        // 4: + 버튼 (⋯)
        + '<td style="text-align:center;padding:3px 4px;width:32px"><button class="btn btn-ghost btn-xs" style="font-size:15px;padding:0 4px;letter-spacing:1px" title="추가기능" '
        + 'onclick="window.showPendingActionMenu(event,' + JSON.stringify(r.lot_no) + ')">⋯</button></td>'
        // 5: SAP (Pending에 없음)
        + '<td class="mono-cell">' + escapeHtml(r.sap_no || '-') + '</td>'
        // 6: BL
        + '<td class="mono-cell">' + escapeHtml(r.bl_no || '-') + '</td>'
        // 7: Product
        + '<td><span class="tag">' + escapeHtml(r.product || '-') + '</span></td>'
        // 8: Status — PENDING 고정
        + '<td><span class="tag" style="background:rgba(148,163,184,0.15);color:#94a3b8">⏳ PENDING</span></td>'
        // 9: ✅ 입고확정 버튼 (Pending에선 ↩ 대신 정방향 액션)
        + '<td style="text-align:center;padding:2px 4px"><button class="btn btn-ghost btn-xs" style="color:#22c55e;font-size:13px;padding:1px 5px;border:1px solid #22c55e55" '
        + 'onclick="window.showPendingConfirmModal(\\'' + lotSafe + '\\')" title="입고 확정 → AVAILABLE">✅</button></td>'
        // 10: Balance(MT) - Pending 단계에선 net_weight 표시
        + '<td class="mono-cell" style="text-align:right">' + netMt + '</td>'
        // 11: NET(MT)
        + '<td class="mono-cell" style="text-align:right">' + netMt + '</td>'
        // 12: Container
        + '<td class="mono-cell">' + escapeHtml(r.container_no || '-') + '</td>'
        // 13: MXBG
        + '<td class="mono-cell" style="text-align:center">' + (r.mxbg_pallet != null ? r.mxbg_pallet : '-') + '</td>'
        // 14: Available bags (Pending엔 톤백 미생성 또는 미반입)
        + '<td class="mono-cell" style="text-align:center;color:#555">-</td>'
        // 15: Reserved
        + '<td class="mono-cell" style="text-align:center;color:#555">-</td>'
        // 16: Packed
        + '<td class="mono-cell" style="text-align:center;color:#555">-</td>'
        // 17: Total Bags
        + '<td class="mono-cell" style="text-align:center">' + (r.mxbg_pallet != null ? r.mxbg_pallet : '-') + '</td>'
        // 18: Remain Bags
        + '<td class="mono-cell" style="text-align:center;color:#555">-</td>'
        // 19: AV
        + '<td class="mono-cell" style="text-align:right;color:#555">-</td>'
        // 20: VR
        + '<td class="mono-cell" style="text-align:right;color:#555">-</td>'
        // 21: AR
        + '<td class="mono-cell" style="text-align:right;color:#555">-</td>'
        // 22: Invoice
        + '<td class="mono-cell">' + escapeHtml(r.salar_invoice_no || '-') + '</td>'
        // 23: Ship
        + '<td class="mono-cell">' + escapeHtml(r.ship_date || '-') + '</td>'
        // 24: Arrival
        + '<td class="mono-cell">' + escapeHtml(r.arrival_date || '-') + '</td>'
        // 25: WH
        + '<td class="mono-cell">' + escapeHtml(r.warehouse || '-') + '</td>'
        // 26: Customs (Pending엔 의미 없음)
        + '<td class="mono-cell" style="color:#555">-</td>'
        // 27: Inbound(MT) — Pending엔 미반입
        + '<td class="mono-cell" style="text-align:right;color:#555">-</td>'
        // 28: Location (미배정)
        + '<td class="mono-cell" style="color:#555">-</td>'
        + '</tr>';
    }).join('');
    return html + '</tbody></table></div>';
  }"""


def main() -> int:
    if not TARGET.exists():
        print(f"[ERROR] target not found: {TARGET}", file=sys.stderr)
        return 1
    text = TARGET.read_text(encoding="utf-8")
    line_count_before = text.count("\n")
    print(f"[INFO] file: {TARGET.name}")
    print(f"[INFO] lines before: {line_count_before}")

    if "Pending 헤더를 Available 28컬럼과 통일" in text:
        print("[SKIP] already patched.")
        return 0
    if ANCHOR not in text:
        print("[ERROR] anchor not found.", file=sys.stderr)
        return 2
    if text.count(ANCHOR) > 1:
        print(f"[ERROR] anchor matched {text.count(ANCHOR)} times.", file=sys.stderr)
        return 3

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = TARGET.with_suffix(f".js.bak_pending_header_{ts}")
    shutil.copy2(TARGET, backup)
    print(f"[INFO] backup: {backup.name}")

    new_text = text.replace(ANCHOR, PATCH, 1)
    if not new_text.rstrip().endswith("})();"):
        print("[ERROR] IIFE closing lost.", file=sys.stderr)
        return 4
    TARGET.write_bytes(new_text.encode("utf-8"))
    print(f"[INFO] lines after: {new_text.count(chr(10))}")

    r = subprocess.run(["node", "--check", str(TARGET)], capture_output=True, text=True)
    if r.returncode != 0:
        print(f"[FAIL] {r.stderr}")
        return 5
    print("[OK] Pending 헤더 Available 28컬럼과 통일 완료.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
