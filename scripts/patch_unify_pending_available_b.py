# -*- coding: utf-8 -*-
"""
patch_unify_pending_available_b.py
====================================
Purpose: 옵션 B — Pending과 Available을 공통 15컬럼으로 통일
Why    : 사용자 선택 "옵션 B로 해줘"
         두 탭 공통 컬럼만 추출 → 깔끔 + 일관
Columns: [☑][#][LOT][⋯][SAP][BL][Product][Container][Vessel][MXBG]
         [NET(MT)][Status][액션(✅or↩)][Arrival][WH]
Note   : Available의 톤백 상세(Available/Reserved/Packed)는 우클릭에서 접근 (기존 ⋯ 메뉴 유지)
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

# ────────────────────────────────────────────────────────────
# 1. Pending — 공통 15컬럼으로 통일
# ────────────────────────────────────────────────────────────
PENDING_ANCHOR = """  function _renderPendingLotRows(rows) {
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

PENDING_PATCH = """  function _renderPendingLotRows(rows) {
    // v868 fix (2026-05-16 옵션B): 두 탭 공통 15컬럼 통일
    var html = '<div style="overflow-x:auto"><table class="data-table"><thead><tr>'
      + '<th style="width:28px;text-align:center"><input type="checkbox" id="pending-select-all" onchange="window.pendingToggleAll(this)" title="전체 선택"></th>'
      + '<th>#</th><th style="text-align:center">LOT</th><th style="width:32px;text-align:center">⋯</th>'
      + '<th>SAP</th><th>BL</th><th>Product</th>'
      + '<th>Container</th><th>Vessel</th><th>MXBG</th><th>NET(MT)</th>'
      + '<th>Status</th><th style="text-align:center;color:#22c55e" title="입고 확정 → AVAILABLE">✅</th>'
      + '<th>Arrival</th><th>WH</th>'
      + '</tr></thead><tbody>';
    html += rows.map(function(r, i) {
      var lotSafe = escapeHtml(r.lot_no || '');
      var netMt = r.net_weight != null ? fmtN(r.net_weight / 1000) : '-';
      return '<tr>'
        + '<td style="text-align:center;padding:3px 6px"><input type="checkbox" class="pending-cb" data-lot="' + lotSafe + '"></td>'
        + '<td class="mono-cell" style="color:var(--text-muted)">' + (i+1) + '</td>'
        + '<td class="mono-cell cell-left" style="color:#94a3b8;font-weight:600;padding:6px 10px">' + lotSafe + '</td>'
        + '<td style="text-align:center;padding:3px 4px;width:32px"><button class="btn btn-ghost btn-xs" style="font-size:15px;padding:0 4px;letter-spacing:1px" title="추가기능" '
        + 'onclick="window.showPendingActionMenu(event,' + JSON.stringify(r.lot_no) + ')">⋯</button></td>'
        + '<td class="mono-cell">' + escapeHtml(r.sap_no || '-') + '</td>'
        + '<td class="mono-cell">' + escapeHtml(r.bl_no || '-') + '</td>'
        + '<td><span class="tag">' + escapeHtml(r.product || '-') + '</span></td>'
        + '<td class="mono-cell">' + escapeHtml(r.container_no || '-') + '</td>'
        + '<td class="mono-cell">' + escapeHtml(r.vessel || '-') + '</td>'
        + '<td class="mono-cell" style="text-align:center">' + (r.mxbg_pallet != null ? r.mxbg_pallet : '-') + '</td>'
        + '<td class="mono-cell" style="text-align:right">' + netMt + '</td>'
        + '<td><span class="tag" style="background:rgba(148,163,184,0.15);color:#94a3b8">⏳ PENDING</span></td>'
        + '<td style="text-align:center;padding:2px 4px"><button class="btn btn-ghost btn-xs" style="color:#22c55e;font-size:13px;padding:1px 5px;border:1px solid #22c55e55" '
        + 'onclick="window.showPendingConfirmModal(\\'' + lotSafe + '\\')" title="입고 확정 → AVAILABLE">✅</button></td>'
        + '<td class="mono-cell">' + escapeHtml(r.arrival_date || '-') + '</td>'
        + '<td class="mono-cell">' + escapeHtml(r.warehouse || '-') + '</td>'
        + '</tr>';
    }).join('');
    return html + '</tbody></table></div>';
  }"""

# ────────────────────────────────────────────────────────────
# 2. Available — 15컬럼으로 축소 (헤더만 변경)
# ────────────────────────────────────────────────────────────
AVAIL_HEAD_ANCHOR = """        + '<div style="overflow-x:auto"><table class="data-table"><thead><tr>'
        + '<th style="width:28px;text-align:center"><input type="checkbox" id="avail-select-all" onchange="window.availToggleAll(this)" title="전체 선택"></th>'
        + '<th>#</th><th style="text-align:center">LOT</th><th style="width:32px;text-align:center">+</th><th>SAP</th><th>BL</th><th>Product</th>'
        + '<th>Status</th><th style="text-align:center;color:#f59e0b" title="입고취소 → PENDING">↩️</th>'
        + '<th>Balance(MT)</th><th>NET(MT)</th><th>Container</th>'
        + '<th>MXBG</th><th>Available</th><th>Reserved</th><th>Packed</th><th>Total Bags</th><th>Remain Bags</th><th>AV</th><th>VR</th><th>AR</th><th>Invoice</th>'
        + '<th>Ship</th><th>Arrival</th><th>WH</th><th>Customs</th>'
        + '<th>Inbound(MT)</th><th>Location</th>'
        + '</tr></thead><tbody>';"""

AVAIL_HEAD_PATCH = """        // v868 fix (2026-05-16 옵션B): Pending과 동일한 15컬럼 헤더
        // 톤백 상세(Available/Reserved/Packed 등)는 우클릭 메뉴 "톤백 상세"에서 접근
        + '<div style="overflow-x:auto"><table class="data-table"><thead><tr>'
        + '<th style="width:28px;text-align:center"><input type="checkbox" id="avail-select-all" onchange="window.availToggleAll(this)" title="전체 선택"></th>'
        + '<th>#</th><th style="text-align:center">LOT</th><th style="width:32px;text-align:center">⋯</th>'
        + '<th>SAP</th><th>BL</th><th>Product</th>'
        + '<th>Container</th><th>Vessel</th><th>MXBG</th><th>NET(MT)</th>'
        + '<th>Status</th><th style="text-align:center;color:#f59e0b" title="입고취소 → PENDING">↩️</th>'
        + '<th>Arrival</th><th>WH</th>'
        + '</tr></thead><tbody>';"""


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
    backup = TARGET.with_suffix(f".js.bak_unify_b_{ts}")
    shutil.copy2(TARGET, backup)
    print(f"[INFO] backup: {backup.name}")
    print()

    ok = True
    print("=== Pending 헤더 15컬럼 통일 ===")
    ok &= apply_patch(TARGET, PENDING_ANCHOR, PENDING_PATCH, "(P) Pending 헤더 통일")

    print()
    print("=== Available 헤더 15컬럼 통일 ===")
    ok &= apply_patch(TARGET, AVAIL_HEAD_ANCHOR, AVAIL_HEAD_PATCH, "(A) Available 헤더 통일")

    if not ok:
        return 2

    # syntax 검증
    print()
    r = subprocess.run(["node", "--check", str(TARGET)], capture_output=True, text=True)
    if r.returncode != 0:
        print(f"[FAIL] {r.stderr}")
        return 3
    print("[OK] sqm-inventory.js syntax OK")
    print()
    print("🎉 Pending+Available 15컬럼 통일 완료 (옵션 B)")
    print("⚠️ 다음 작업: Available의 데이터 행도 새 15컬럼 구조로 매핑 필요")
    return 0


if __name__ == "__main__":
    sys.exit(main())
