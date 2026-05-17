# -*- coding: utf-8 -*-
"""
patch_available_rows_15cols.py
================================
Purpose: Available 데이터 행 (mainRow + sampleRow)을 15컬럼으로 축소
Why    : 옵션 B 헤더 통일 후 데이터 행도 매핑 필요
Columns: [☑][#][LOT][⋯][SAP][BL][Product][Container][Vessel][MXBG]
         [NET(MT)][Status][↩️][Arrival][WH]
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

# ────────────────────────────────────────────────────────────
# 1. sampleRow (현재 28컬럼) → 15컬럼
# ────────────────────────────────────────────────────────────
SAMPLE_ANCHOR = """        if (hasSample) {
          // v868 fix (2026-05-16): 샘플 행을 일반 행과 동일한 28칼럼 매핑으로 정렬
          // LOT(SP)를 LOT 헤더(3번 칼럼)로 이동, 나머지 칼럼도 1칸씩 정렬
          sampleRow =
            '<tr style="background:rgba(234,179,8,0.08);border-left:3px solid #eab308">' +
            // 1:체크박스 자리 - 🔬
            '<td style="text-align:center;padding:6px 10px;color:#eab308">🔬</td>' +
            // 2:# 자리 - SP
            '<td class="mono-cell" style="color:#eab308;text-align:center">SP</td>' +
            // 3:LOT 자리 - LOT(SP) ← 핵심: LOT 헤더로 이동
            '<td class="mono-cell cell-left" style="color:#eab308;font-weight:700;padding:6px 10px">' + lotKey + '(SP)</td>' +
            // 4:+ 자리 - 빈 (—)
            '<td style="text-align:center;color:#555">—</td>' +
            // 5:SAP
            '<td class="mono-cell" style="color:#94a3b8">' + escapeHtml(r.sap||'') + '</td>' +
            // 6:BL
            '<td class="mono-cell" style="color:#94a3b8">' + escapeHtml(r.bl||'') + '</td>' +
            // 7:Product
            '<td><span class="tag" style="background:rgba(234,179,8,0.2);color:#eab308">' + escapeHtml(r.product||'') + '</span></td>' +
            // 8:Status
            '<td style="color:#eab308;font-weight:600">SAMPLE</td>' +
            // 9:↩ 자리 - 빈
            '<td style="text-align:center;color:#555">—</td>' +
            // 10:Balance(MT)
            '<td class="mono-cell" style="text-align:right;color:#eab308;font-weight:600">' + fmtN(r.sample_weight_mt||0) + '</td>' +
            // 11:NET(MT)
            '<td class="mono-cell" style="text-align:right;color:#eab308">' + fmtN(r.sample_weight_mt||0) + '</td>' +
            // 12:Container
            '<td class="mono-cell" style="color:#94a3b8">' + parentContainer + '</td>' +
            // 13:MXBG 자리 - 빈
            '<td class="mono-cell" style="text-align:center;color:#555">—</td>' +
            // 14:Available bags
            '<td class="mono-cell" style="text-align:center;color:#eab308;font-weight:700">' + r.sample_bags + '</td>' +
            // 15:Reserved
            '<td class="mono-cell" style="text-align:center;color:#555">0</td>' +
            // 16:Packed
            '<td class="mono-cell" style="text-align:center;color:#555">0</td>' +
            // 17:Total Bags
            '<td class="mono-cell" style="text-align:center;color:#eab308;font-weight:700">' + r.sample_bags + '</td>' +
            // 18:Remain
            '<td class="mono-cell" style="text-align:center;color:#555">0</td>' +
            // 19:AV
            '<td class="mono-cell" style="text-align:right;color:#eab308">' + fmtN(r.sample_weight_mt||0) + '</td>' +
            // 20:VR
            '<td class="mono-cell" style="text-align:right;color:#555">0</td>' +
            // 21:AR
            '<td class="mono-cell" style="text-align:right;color:#555">0</td>' +
            // 22-28: Invoice/Ship/Arrival/WH/Customs/Inbound/Location (7칼럼) - colspan
            '<td colspan="7" style="color:#555;text-align:center">—</td>' +
            '</tr>';
        }"""

SAMPLE_PATCH = """        if (hasSample) {
          // v868 fix (2026-05-16 옵션B): 샘플 행도 15컬럼 매핑 (Pending과 통일)
          sampleRow =
            '<tr style="background:rgba(234,179,8,0.08);border-left:3px solid #eab308">' +
            // 1:체크박스 - 🔬
            '<td style="text-align:center;padding:6px 10px;color:#eab308">🔬</td>' +
            // 2:# - SP
            '<td class="mono-cell" style="color:#eab308;text-align:center">SP</td>' +
            // 3:LOT
            '<td class="mono-cell cell-left" style="color:#eab308;font-weight:700;padding:6px 10px">' + lotKey + '(SP)</td>' +
            // 4:⋯ - 빈
            '<td style="text-align:center;color:#555">—</td>' +
            // 5:SAP
            '<td class="mono-cell" style="color:#94a3b8">' + escapeHtml(r.sap||'') + '</td>' +
            // 6:BL
            '<td class="mono-cell" style="color:#94a3b8">' + escapeHtml(r.bl||'') + '</td>' +
            // 7:Product
            '<td><span class="tag" style="background:rgba(234,179,8,0.2);color:#eab308">' + escapeHtml(r.product||'') + '</span></td>' +
            // 8:Container
            '<td class="mono-cell" style="color:#94a3b8">' + parentContainer + '</td>' +
            // 9:Vessel
            '<td class="mono-cell" style="color:#94a3b8">' + escapeHtml(r.vessel||'-') + '</td>' +
            // 10:MXBG - 빈
            '<td class="mono-cell" style="text-align:center;color:#555">—</td>' +
            // 11:NET(MT)
            '<td class="mono-cell" style="text-align:right;color:#eab308;font-weight:600">' + fmtN(r.sample_weight_mt||0) + '</td>' +
            // 12:Status
            '<td><span class="tag" style="background:rgba(234,179,8,0.2);color:#eab308">SAMPLE</span></td>' +
            // 13:↩ 자리 - 빈
            '<td style="text-align:center;color:#555">—</td>' +
            // 14:Arrival
            '<td class="mono-cell">' + escapeHtml((r.arrival_date||'').slice(0,10) || '-') + '</td>' +
            // 15:WH
            '<td class="mono-cell">' + escapeHtml(r.wh||'-') + '</td>' +
            '</tr>';
        }"""

# ────────────────────────────────────────────────────────────
# 2. mainRow (현재 28컬럼) → 15컬럼
# ────────────────────────────────────────────────────────────
MAIN_ANCHOR = """        var mainRow =
          '<tr style="' + (hasSample ? 'border-left:3px solid #22c55e' : '') + '">'
          + '<td style="text-align:center;padding:3px 6px"><input type="checkbox" class="avail-cb" data-lot="' + lotKey + '"></td>'
          + '<td class="mono-cell" style="color:var(--text-muted)">' + (i+1) + '</td>'
          + '<td class="mono-cell cell-left" style="color:var(--accent);font-weight:600;padding:6px 10px">' + lotKey + '</td>'
          + '<td style="text-align:center;padding:3px 4px;width:32px"><button class="btn btn-ghost btn-xs" data-lot="' + lotKey + '" onclick="window.showInvActionMenu(this)" style="font-size:15px;padding:0 4px;letter-spacing:1px" title="추가기능">⋯</button></td>'
          + '<td class="mono-cell">' + escapeHtml(r.sap||'') + '</td>'
          + '<td class="mono-cell">' + escapeHtml(r.bl||'') + '</td>'
          + '<td><span class="tag">' + escapeHtml(r.product||'') + '</span></td>'
          + '<td><span class="tag" style="background:rgba(34,197,94,0.15);color:#22c55e">✅ AVAILABLE</span></td>'
          + '<td style="text-align:center;padding:2px 4px"><button class="btn btn-ghost btn-xs" onclick="window.revertToPending(\\'' + lotSafe + '\\')" title="입고 취소 → PENDING" style="color:#f59e0b;font-size:13px;padding:1px 5px;border:1px solid #f59e0b55">↩️</button></td>'
          + '<td class="mono-cell" style="text-align:right">' + (r.balance!=null?fmtN(r.balance):'-') + '</td>'
          + '<td class="mono-cell" style="text-align:right">' + (r.net!=null?fmtN(r.net):'-') + '</td>'
          + '<td class="mono-cell">' + escapeHtml(r.container||'') + '</td>'
          + '<td class="mono-cell" style="text-align:center">'
            + (r.mxbg_pallet > 0
              ? '<button class="btn btn-ghost btn-xs" style="font-weight:700;color:var(--accent)" '
                + 'data-lot="' + lotKey + '" onclick="window.showTonbagModal(this.dataset.lot)">' + r.mxbg_pallet + '</button>'
              : '-')
          + '</td>'
          + '<td class="mono-cell" style="text-align:center;color:#22c55e;font-weight:700">' + availBags + '</td>'
          + '<td class="mono-cell" style="text-align:center;color:#3b82f6;font-weight:700">' + reservedBags + '</td>'
          + '<td class="mono-cell" style="text-align:center;color:#f59e0b;font-weight:700">' + packedBags + '</td>'
          + '<td class="mono-cell" style="text-align:center">' + totalBags + '</td>'
          + '<td class="mono-cell" style="text-align:center;font-weight:700">' + remainBags + '</td>'
          + '<td class="mono-cell" style="text-align:right;color:#22c55e;font-weight:700">' + (r.avail_mt!=null?fmtN(r.avail_mt):'-') + '</td>'
          + '<td class="mono-cell" style="text-align:right;color:#3b82f6;font-weight:700">' + (r.reserved_mt!=null?fmtN(r.reserved_mt):'-') + '</td>'
          + '<td class="mono-cell" style="text-align:right;color:#f59e0b;font-weight:700">' + (r.picked_mt!=null?fmtN(r.picked_mt):'-') + '</td>'
          + '<td class="mono-cell">' + escapeHtml(r.invoice_no||'') + '</td>'
          + '<td class="mono-cell">' + escapeHtml((r.ship_date||'').slice(0,10)) + '</td>'
          + '<td class="mono-cell">' + escapeHtml((r.arrival_date||'').slice(0,10)) + '</td>'
          + '<td class="mono-cell">' + escapeHtml(r.wh||'') + '</td>'
          + '<td class="mono-cell">' + escapeHtml(r.customs||'') + '</td>'
          + '<td class="mono-cell" style="text-align:right">' + (r.initial_weight!=null?fmtN(r.initial_weight):'-') + '</td>'
          + '<td><span class="tag">' + escapeHtml(r.location||'-') + '</span></td>'
          + '</tr>';"""

# 15컬럼 매핑: ☑ # LOT ⋯ SAP BL Product Container Vessel MXBG NET(MT) Status ↩️ Arrival WH
MAIN_PATCH = """        // v868 fix (2026-05-16 옵션B): mainRow도 15컬럼 매핑 (Pending과 통일)
        var mainRow =
          '<tr style="' + (hasSample ? 'border-left:3px solid #22c55e' : '') + '">'
          // 1:체크박스
          + '<td style="text-align:center;padding:3px 6px"><input type="checkbox" class="avail-cb" data-lot="' + lotKey + '"></td>'
          // 2:#
          + '<td class="mono-cell" style="color:var(--text-muted)">' + (i+1) + '</td>'
          // 3:LOT
          + '<td class="mono-cell cell-left" style="color:var(--accent);font-weight:600;padding:6px 10px">' + lotKey + '</td>'
          // 4:⋯ (액션 메뉴 — 톤백 상세는 여기서)
          + '<td style="text-align:center;padding:3px 4px;width:32px"><button class="btn btn-ghost btn-xs" data-lot="' + lotKey + '" onclick="window.showInvActionMenu(this)" style="font-size:15px;padding:0 4px;letter-spacing:1px" title="추가기능 (톤백 상세 등)">⋯</button></td>'
          // 5:SAP
          + '<td class="mono-cell">' + escapeHtml(r.sap||'') + '</td>'
          // 6:BL
          + '<td class="mono-cell">' + escapeHtml(r.bl||'') + '</td>'
          // 7:Product
          + '<td><span class="tag">' + escapeHtml(r.product||'') + '</span></td>'
          // 8:Container
          + '<td class="mono-cell">' + escapeHtml(r.container||'') + '</td>'
          // 9:Vessel
          + '<td class="mono-cell">' + escapeHtml(r.vessel||'-') + '</td>'
          // 10:MXBG (클릭 시 톤백 모달)
          + '<td class="mono-cell" style="text-align:center">'
            + (r.mxbg_pallet > 0
              ? '<button class="btn btn-ghost btn-xs" style="font-weight:700;color:var(--accent)" '
                + 'data-lot="' + lotKey + '" onclick="window.showTonbagModal(this.dataset.lot)" title="톤백 상세 보기">' + r.mxbg_pallet + '</button>'
              : '-')
          + '</td>'
          // 11:NET(MT)
          + '<td class="mono-cell" style="text-align:right">' + (r.net!=null?fmtN(r.net):'-') + '</td>'
          // 12:Status
          + '<td><span class="tag" style="background:rgba(34,197,94,0.15);color:#22c55e">✅ AVAILABLE</span></td>'
          // 13:↩️ (PENDING으로 되돌리기)
          + '<td style="text-align:center;padding:2px 4px"><button class="btn btn-ghost btn-xs" onclick="window.revertToPending(\\'' + lotSafe + '\\')" title="입고 취소 → PENDING" style="color:#f59e0b;font-size:13px;padding:1px 5px;border:1px solid #f59e0b55">↩️</button></td>'
          // 14:Arrival
          + '<td class="mono-cell">' + escapeHtml((r.arrival_date||'').slice(0,10)) + '</td>'
          // 15:WH
          + '<td class="mono-cell">' + escapeHtml(r.wh||'-') + '</td>'
          + '</tr>';"""


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
    backup = TARGET.with_suffix(f".js.bak_avail_rows_{ts}")
    shutil.copy2(TARGET, backup)
    print(f"[INFO] backup: {backup.name}")
    print()

    ok = True
    print("=== Available sampleRow 15컬럼 ===")
    ok &= apply_patch(TARGET, SAMPLE_ANCHOR, SAMPLE_PATCH, "(S) sampleRow")
    print()
    print("=== Available mainRow 15컬럼 ===")
    ok &= apply_patch(TARGET, MAIN_ANCHOR, MAIN_PATCH, "(M) mainRow")

    if not ok:
        return 2

    print()
    r = subprocess.run(["node", "--check", str(TARGET)], capture_output=True, text=True)
    if r.returncode != 0:
        print(f"[FAIL] {r.stderr}")
        return 3
    print("[OK] syntax OK")
    print()
    print("🎉 Available 데이터 행 15컬럼 완료")
    return 0


if __name__ == "__main__":
    sys.exit(main())
