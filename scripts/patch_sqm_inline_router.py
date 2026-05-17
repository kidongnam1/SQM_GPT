# -*- coding: utf-8 -*-
"""
patch_sqm_inline_router.py
==========================
Purpose: sqm-inline.js renderPage() switch에 case 'pending' / case 'available' 2줄 추가
Why    : v868 053fa7a + v9.5 PENDING/AVAILABLE 라우트가 sqm-inline.js 구버전 라우터에
         누락되어 "Preparing: pending" stub만 표시되는 버그 수정
Rule   : CLAUDE.md Rule 5 — 7516줄 파일은 Edit 툴 금지, Python 스크립트만 허용
Author : Ruby (Senior Software Architect) — 2026-05-15
"""
import re
import sys
import shutil
from pathlib import Path
from datetime import datetime

TARGET = Path(__file__).resolve().parent.parent / "frontend" / "js" / "sqm-inline.js"

# 정확한 매칭 — 한 번만 일치해야 안전
ANCHOR = "      case 'inventory':  loadInventoryPage();  break;\n      case 'allocation': loadAllocationPage(); break;"

PATCH = """      case 'inventory':  loadInventoryPage();  break;
      // v868 053fa7a — PENDING 입고 대기 워크플로우 (sqm-inventory.js 노출)
      case 'pending':    if (window.loadPendingPage)   { window.loadPendingPage();   } else { loadStubPage(route); } break;
      // v868 v9.5 — AVAILABLE 재고 필터 뷰 (sqm-inventory.js 노출)
      case 'available':  if (window.loadAvailablePage) { window.loadAvailablePage(); } else { loadStubPage(route); } break;
      case 'allocation': loadAllocationPage(); break;"""


def main() -> int:
    if not TARGET.exists():
        print(f"[ERROR] target not found: {TARGET}", file=sys.stderr)
        return 1

    # 1) 원본 읽기 (바이너리 모드 + 줄바꿈 보존)
    raw = TARGET.read_bytes()
    text = raw.decode("utf-8")
    line_count_before = text.count("\n")
    crlf = b"\r\n" in raw
    print(f"[INFO] file: {TARGET.name}")
    print(f"[INFO] lines before: {line_count_before}")
    print(f"[INFO] line ending : {'CRLF' if crlf else 'LF'}")

    # 2) 이미 패치되어 있으면 스킵 (멱등성)
    if "case 'pending':" in text and "window.loadPendingPage" in text:
        # renderPage 함수 안에 있는지 검증
        m = re.search(
            r"function renderPage\(route\).*?\n\s*\}",
            text,
            flags=re.DOTALL,
        )
        if m and "case 'pending':" in m.group(0):
            print("[SKIP] already patched (idempotent).")
            return 0

    # 3) 앵커 매칭 검증 — 정확히 1회만 매칭되어야 함
    count = text.count(ANCHOR)
    if count == 0:
        print("[ERROR] anchor not found. file may have been modified.", file=sys.stderr)
        return 2
    if count > 1:
        print(f"[ERROR] anchor matched {count} times — ambiguous. abort.", file=sys.stderr)
        return 3

    # 4) 백업
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = TARGET.with_suffix(f".js.bak_router_{ts}")
    shutil.copy2(TARGET, backup)
    print(f"[INFO] backup: {backup.name}")

    # 5) 패치 적용
    new_text = text.replace(ANCHOR, PATCH, 1)

    # 6) 끝부분 IIFE 닫힘 보존 검증
    if not new_text.rstrip().endswith("})();"):
        print("[ERROR] IIFE closing `})();` lost after patch. abort.", file=sys.stderr)
        return 4

    # 7) 라인 수 검증 (정확히 +4 라인 증가 예상)
    line_count_after = new_text.count("\n")
    delta = line_count_after - line_count_before
    if delta != 4:
        print(f"[ERROR] line delta != 4 (got {delta}). abort.", file=sys.stderr)
        return 5

    # 8) 기록 (원본 줄바꿈 보존)
    if crlf:
        # 원본이 CRLF였다면 그대로 유지 (현재는 LF로 확인됨)
        TARGET.write_bytes(new_text.encode("utf-8"))
    else:
        TARGET.write_bytes(new_text.encode("utf-8"))

    print(f"[INFO] lines after : {line_count_after} (delta=+{delta})")
    print("[OK] patch applied successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
