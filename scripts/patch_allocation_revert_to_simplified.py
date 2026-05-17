# -*- coding: utf-8 -*-
"""
patch_allocation_revert_to_simplified.py
==========================================
Purpose: case 'allocation'만 위임 해제 — sqm-inline.js의 단순화된 버전 호출
Why    : 사용자 보고 — Allocation에 옛 11개 버튼 다시 출현
         원인: 라우터 전수 위임으로 window.loadAllocationPage(sqm-allocation.js 원본) 호출
              우리가 4단계에 걸쳐 단순화한 sqm-inline.js IIFE 버전이 무시됨
Fix    : case 'allocation'만 옛 패턴(IIFE 내부 함수 직접 호출)로 복구
         다른 11개 case는 위임 유지
Rule   : CLAUDE.md Rule 5 — Python 스크립트만
Author : Ruby (Senior Software Architect) — 2026-05-17
"""
import sys
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
TARGET = ROOT / "frontend" / "js" / "sqm-inline.js"

ANCHOR = """      case 'allocation': if (window.loadAllocationPage) { window.loadAllocationPage(); } else { loadAllocationPage(); } break;"""

PATCH = """      // v868 fix (2026-05-17 +): Allocation은 sqm-inline.js의 단순화 버전 유지
      // (sqm-allocation.js의 원본 11개 버튼 버전이 window 덮어쓰지 못하게 직접 호출)
      case 'allocation': loadAllocationPage(); break;"""


def main() -> int:
    text = TARGET.read_text(encoding="utf-8")

    if "v868 fix (2026-05-17 +): Allocation은 sqm-inline.js의 단순화 버전" in text:
        print("[SKIP] already patched.")
        return 0
    if ANCHOR not in text:
        print("[ERROR] anchor not found", file=sys.stderr)
        return 2
    if text.count(ANCHOR) > 1:
        print(f"[ERROR] matched {text.count(ANCHOR)} times")
        return 3

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = TARGET.with_suffix(f".js.bak_alloc_revert_{ts}")
    shutil.copy2(TARGET, backup)
    print(f"[INFO] backup: {backup.name}")

    new_text = text.replace(ANCHOR, PATCH, 1)
    if not new_text.rstrip().endswith("})();"):
        print("[ERROR] IIFE closing lost")
        return 4

    TARGET.write_bytes(new_text.encode("utf-8"))
    r = subprocess.run(["node", "--check", str(TARGET)], capture_output=True, text=True)
    if r.returncode != 0:
        print(f"[FAIL] {r.stderr}")
        return 5
    print("[OK] Allocation 단순화 버전 복구 완료")
    return 0


if __name__ == "__main__":
    sys.exit(main())
