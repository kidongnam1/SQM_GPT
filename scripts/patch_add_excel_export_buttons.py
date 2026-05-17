# -*- coding: utf-8 -*-
"""
patch_add_excel_export_buttons.py
==================================
Purpose: Pending / Available / Picked 탭에 Excel 내보내기 버튼 추가
Why    : 사용자 요청 — 다른 탭(Allocation)과 동일한 UX
Fix    : 각 탭의 헤더 영역에 [📊 Excel 내보내기] 버튼 추가
         window.exportTableToExcel(table, filename)으로 클라이언트 측 변환
Rule   : CLAUDE.md Rule 5 — sqm-inventory.js(1100줄), sqm-picked.js(150줄)
         sqm-inventory.js는 1000줄 이상이라 Python 스크립트 필수
Author : Ruby (Senior Software Architect) — 2026-05-16
"""
import sys
import shutil
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent

# ─────────────────────────────────────────────────────────────────────
# 1. sqm-inventory.js — Pending + Available
# ─────────────────────────────────────────────────────────────────────
INV = ROOT / "frontend" / "js" / "sqm-inventory.js"

# Pending: line 647-648
PENDING_ANCHOR = """        + '<button class="btn btn-ghost" style="font-size:12px" onclick="window.loadPendingPage()">🔄 새로고침</button>'
        + '<button class="btn" style="background:var(--accent,#3b82f6);color:#fff;font-size:12px;padding:4px 12px" onclick="window.bulkConfirmPending()">✅ 선택 일괄 확정</button>'"""

PENDING_PATCH = """        + '<button class="btn btn-ghost" style="font-size:12px" onclick="window.loadPendingPage()">🔄 새로고침</button>'
        + '<button class="btn btn-secondary" style="font-size:12px;padding:4px 12px" onclick="window.exportPendingExcel()" title="현재 화면 Pending 데이터를 Excel로 내보냅니다">📊 Excel 내보내기</button>'
        + '<button class="btn" style="background:var(--accent,#3b82f6);color:#fff;font-size:12px;padding:4px 12px" onclick="window.bulkConfirmPending()">✅ 선택 일괄 확정</button>'"""

# Available: line 753 — 새로고침 버튼 뒤에 추가
AVAIL_ANCHOR = """        + '<button class="btn btn-ghost" style="font-size:12px;margin-left:auto" onclick="window.loadAvailablePage()">🔄 새로고침</button>
        + '</div>'"""
# 실제 매칭을 위해 한 줄로 (Python string + 사이의 줄바꿈/연결문자)
AVAIL_ANCHOR_REAL = "        + '<button class=\"btn btn-ghost\" style=\"font-size:12px;margin-left:auto\" onclick=\"window.loadAvailablePage()\">🔄 새로고침</button>'\n        + '</div>'"

AVAIL_PATCH = """        + '<button class="btn btn-secondary" style="font-size:12px" onclick="window.exportAvailableExcel()" title="현재 화면 Available 데이터를 Excel로 내보냅니다">📊 Excel 내보내기</button>'
        + '<button class="btn btn-ghost" style="font-size:12px" onclick="window.loadAvailablePage()">🔄 새로고침</button>'
        + '</div>'"""

# 헬퍼 함수 추가용 앵커 (window.loadInventoryPage 노출 부분)
HELPER_ANCHOR = """  window.loadInventoryPage  = loadInventoryPage;
})();"""

HELPER_PATCH = """  // v868 fix (2026-05-16): Pending/Available 탭 Excel 내보내기 헬퍼
  window.exportPendingExcel = function() {
    var tbl = document.querySelector('#page-container table.data-table');
    if (!tbl) { if (window.showToast) showToast('warn', '내보낼 테이블이 없습니다'); return; }
    var ts = new Date().toISOString().slice(0,10);
    if (window.exportTableToExcel) {
      window.exportTableToExcel(tbl, 'pending_' + ts + '.xlsx');
    } else {
      alert('Excel 내보내기 함수를 찾을 수 없습니다 (exportTableToExcel)');
    }
  };
  window.exportAvailableExcel = function() {
    var tbl = document.querySelector('#page-container table.data-table');
    if (!tbl) { if (window.showToast) showToast('warn', '내보낼 테이블이 없습니다'); return; }
    var ts = new Date().toISOString().slice(0,10);
    if (window.exportTableToExcel) {
      window.exportTableToExcel(tbl, 'available_' + ts + '.xlsx');
    } else {
      alert('Excel 내보내기 함수를 찾을 수 없습니다 (exportTableToExcel)');
    }
  };
  window.loadInventoryPage  = loadInventoryPage;
})();"""

# ─────────────────────────────────────────────────────────────────────
# 2. sqm-picked.js — Picked
# ─────────────────────────────────────────────────────────────────────
PICKED = ROOT / "frontend" / "js" / "sqm-picked.js"

PICKED_ANCHOR = """      '    <button class="btn" onclick="window.allocRevertStep(\\'PICKED\\')" style="font-size:12px" title="PICKED 상태를 RESERVED로 되돌립니다">↩ PICKED &rarr; RESERVED</button>',
      '    <button class="btn btn-secondary" onclick="renderPage(\\'picked\\')">🔁 새로고침</button>',"""

PICKED_PATCH = """      '    <button class="btn" onclick="window.allocRevertStep(\\'PICKED\\')" style="font-size:12px" title="PICKED 상태를 RESERVED로 되돌립니다">↩ PICKED &rarr; RESERVED</button>',
      '    <button class="btn btn-secondary" onclick="window.exportPickedExcel()" style="font-size:12px" title="현재 Picked 데이터를 Excel로 내보냅니다">📊 Excel 내보내기</button>',
      '    <button class="btn btn-secondary" onclick="renderPage(\\'picked\\')">🔁 새로고침</button>',"""

# Picked 헬퍼 함수 추가용 (loadPickedPage 함수 위에)
PICKED_HELPER_ANCHOR = "  function loadPickedPage() {"

PICKED_HELPER_PATCH = """  // v868 fix (2026-05-16): Picked 탭 Excel 내보내기 헬퍼
  window.exportPickedExcel = function() {
    var tbl = document.getElementById('picked-table');
    if (!tbl) { if (window.showToast) showToast('warn', '내보낼 테이블이 없습니다'); return; }
    var ts = new Date().toISOString().slice(0,10);
    if (window.exportTableToExcel) {
      window.exportTableToExcel(tbl, 'picked_' + ts + '.xlsx');
    } else {
      alert('Excel 내보내기 함수를 찾을 수 없습니다 (exportTableToExcel)');
    }
  };

  function loadPickedPage() {"""


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
    # IIFE 닫힘 보존 (sqm-inventory.js만 체크)
    if file_path.name == "sqm-inventory.js" and not new_text.rstrip().endswith("})();"):
        print(f"  [ERROR] IIFE closing lost in {label}. abort.")
        return False
    file_path.write_text(new_text, encoding="utf-8")
    print(f"  [OK] {label} applied.")
    return True


def main() -> int:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 백업
    bk_inv = INV.with_suffix(f".js.bak_excel_{ts}")
    bk_picked = PICKED.with_suffix(f".js.bak_excel_{ts}")
    shutil.copy2(INV, bk_inv)
    shutil.copy2(PICKED, bk_picked)
    print(f"[INFO] backups: {bk_inv.name}, {bk_picked.name}")
    print()

    print("=== sqm-inventory.js — Pending/Available ===")
    ok = True
    ok &= apply_patch(INV, PENDING_ANCHOR, PENDING_PATCH, "(P) Pending 버튼")
    ok &= apply_patch(INV, AVAIL_ANCHOR_REAL, AVAIL_PATCH, "(A) Available 버튼")
    ok &= apply_patch(INV, HELPER_ANCHOR, HELPER_PATCH, "(H) 헬퍼 함수")

    print()
    print("=== sqm-picked.js — Picked ===")
    ok &= apply_patch(PICKED, PICKED_HELPER_ANCHOR, PICKED_HELPER_PATCH, "(P-H) Picked 헬퍼")
    ok &= apply_patch(PICKED, PICKED_ANCHOR, PICKED_PATCH, "(P-B) Picked 버튼")

    if not ok:
        return 2

    # syntax 검증
    import subprocess
    for f in (INV, PICKED):
        r = subprocess.run(["node", "--check", str(f)], capture_output=True, text=True)
        if r.returncode != 0:
            print(f"[FAIL] {f.name} syntax: {r.stderr}")
            return 3
        print(f"[OK] {f.name} syntax OK")

    print()
    print("🎉 ALL Excel 내보내기 버튼 추가 완료")
    return 0


if __name__ == "__main__":
    sys.exit(main())
