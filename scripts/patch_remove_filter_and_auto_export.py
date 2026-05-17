# -*- coding: utf-8 -*-
"""
patch_remove_filter_and_auto_export.py
=======================================
Purpose: 1) Allocation 필터 행 제거 (전체/RESERVED/PICKED/SOLD)
         2) enhanceDataTables의 자동 Excel 내보내기 버튼 비활성화
            (헤더 버튼과 중복)
Why    : 사용자 요청 — "필요없는 것 같다", "우측 하단 Excel 내보내기 삭제"
Safety : 백엔드/함수 모두 보존. UI만 변경
Rule   : CLAUDE.md Rule 5 — sqm-inline.js + sqm-core.js Python 스크립트
Author : Ruby (Senior Software Architect) — 2026-05-16
"""
import sys
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
INLINE = ROOT / "frontend" / "js" / "sqm-inline.js"
CORE = ROOT / "frontend" / "js" / "sqm-core.js"

# ────────────────────────────────────────────────────────────
# 1. sqm-inline.js: Allocation 필터 행 제거
# ────────────────────────────────────────────────────────────
INLINE_FILTER_ANCHOR = """      /* ── 상태 필터 ── */
      '<div class="alloc-filter" style="display:flex;gap:4px;margin-bottom:8px">',
      '  <button class="alloc-filter-btn active" data-filter="all" onclick="window.allocFilterBy(\\'all\\')">전체</button>',
      '  <button class="alloc-filter-btn" data-filter="RESERVED" onclick="window.allocFilterBy(\\'RESERVED\\')">RESERVED</button>',
      '  <button class="alloc-filter-btn" data-filter="PICKED" onclick="window.allocFilterBy(\\'PICKED\\')">PICKED</button>',
      '  <button class="alloc-filter-btn" data-filter="SOLD" onclick="window.allocFilterBy(\\'SOLD\\')">SOLD</button>',
      '</div>',"""

INLINE_FILTER_PATCH = """      /* v868 fix (2026-05-16 v6): 필터 제거 — 사용자 미사용. 필요시 우클릭 메뉴로 충분 */"""

# ────────────────────────────────────────────────────────────
# 2. sqm-core.js: 자동 Excel 내보내기 버튼 비활성화
# ────────────────────────────────────────────────────────────
# enhanceDataTables 함수 내부 — 자동 버튼 추가 부분
CORE_AUTO_EXPORT_ANCHOR = """      host.className = 'sqm-table-export-bar';
      host.innerHTML =
        '<button type="button" class="btn btn-ghost btn-xs sqm-table-export-btn" data-sqm-tip="현재 표를 Excel 파일로 내보냅니다">Excel 내보내기</button>';
      var btn = host.querySelector('button');
      btn.addEventListener('click', function(ev) {
        ev.preventDefault();
        ev.stopPropagation();
        exportTableToExcel(table);
      });
      if (parent && parent.classList.contains('sqm-table-scroll')) {
        parent.parentNode.insertBefore(host, parent);
      } else {
        table.parentNode.insertBefore(host, table);
      }
    });"""

CORE_AUTO_EXPORT_PATCH = """      // v868 fix (2026-05-16 v6): 자동 Excel 내보내기 버튼 비활성화
      // 각 페이지(Pending/Available/Picked/Allocation)가 헤더에 자체 Excel 버튼을
      // 명시적으로 추가하므로 자동 추가 시 중복 발생 → 자동 추가 로직 비활성화.
      // host.className = 'sqm-table-export-bar';
      // (자동 추가 비활성화 — 위 if 블록 진입 시 아무 작업 안 함)
      return; // 추가 안 함
    });"""


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
    # IIFE 닫힘 보존
    if not new_text.rstrip().endswith("})();"):
        print(f"  [ERROR] {label} IIFE closing lost.")
        return False
    file_path.write_text(new_text, encoding="utf-8")
    print(f"  [OK] {label} applied.")
    return True


def main() -> int:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    bk_inline = INLINE.with_suffix(f".js.bak_filter_export_{ts}")
    bk_core = CORE.with_suffix(f".js.bak_filter_export_{ts}")
    shutil.copy2(INLINE, bk_inline)
    shutil.copy2(CORE, bk_core)
    print(f"[INFO] backups: {bk_inline.name}, {bk_core.name}")
    print()

    print("=== sqm-inline.js: Allocation 필터 제거 ===")
    ok = apply_patch(INLINE, INLINE_FILTER_ANCHOR, INLINE_FILTER_PATCH, "(F) Allocation 필터")

    print()
    print("=== sqm-core.js: 자동 Excel 버튼 비활성화 ===")
    ok &= apply_patch(CORE, CORE_AUTO_EXPORT_ANCHOR, CORE_AUTO_EXPORT_PATCH, "(E) 자동 Excel 버튼")

    if not ok:
        return 2

    # syntax 검증
    print()
    for f in (INLINE, CORE):
        r = subprocess.run(["node", "--check", str(f)], capture_output=True, text=True)
        if r.returncode != 0:
            print(f"[FAIL] {f.name}: {r.stderr}")
            return 3
        print(f"[OK] {f.name} syntax OK")

    print()
    print("🎉 필터 제거 + 자동 Excel 버튼 비활성화 완료")
    return 0


if __name__ == "__main__":
    sys.exit(main())
