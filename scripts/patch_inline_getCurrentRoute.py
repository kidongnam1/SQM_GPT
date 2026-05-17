# -*- coding: utf-8 -*-
"""
patch_inline_getCurrentRoute.py
================================
Purpose: sqm-inline.js에 window.getCurrentRoute 노출 추가 — 라우터 상태 동기화
Why    : sqm-core.js와 sqm-inline.js가 각자 _currentRoute 변수를 가짐
         - sqm-core.js:996: window.getCurrentRoute = () => _currentRoute (sqm-core의 것)
         - sqm-inline.js: _currentRoute는 있지만 window 노출 없음
         결과: sqm-inline.js의 renderPage가 자기 _currentRoute='pending' 설정해도
               window.getCurrentRoute() = sqm-core의 _currentRoute = null 반환
               → loadPendingPage 첫 줄 if (window.getCurrentRoute() !== route) return; 에서 종료
               → page-container innerHTML 업데이트 안 됨 → 빈 화면

Fix    : sqm-inline.js의 renderPage 직후에 window.getCurrentRoute 덮어쓰기
         스크립트 로드 순서상 sqm-inline.js가 마지막이라 덮어쓰면 우선됨
Rule   : CLAUDE.md Rule 5 (강화) — 7547줄 IIFE 파일은 Python 스크립트만
Author : Ruby (Senior Software Architect) — 2026-05-16
"""
import sys
import shutil
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
TARGET = ROOT / "frontend" / "js" / "sqm-inline.js"

# 앵커: window.renderPage = renderPage; 뒤에 추가 (라우터 정의 직후)
ANCHOR = "  window.renderPage = renderPage;"

PATCH = """  window.renderPage = renderPage;
  // v868 fix (2026-05-16): sqm-core.js와 sqm-inline.js가 각자 _currentRoute를 가져 상태 불일치 발생
  // sqm-inventory.js의 loadPendingPage/loadAvailablePage가 window.getCurrentRoute()로 sqm-core의 stale 값을
  // 받아 빈 화면이 표시되는 버그 → sqm-inline.js의 _currentRoute(가장 최신)를 반환하도록 덮어씀
  window.getCurrentRoute = function() { return _currentRoute; };"""


def main() -> int:
    if not TARGET.exists():
        print(f"[ERROR] target not found: {TARGET}", file=sys.stderr)
        return 1

    text = TARGET.read_text(encoding="utf-8")
    line_count_before = text.count("\n")
    print(f"[INFO] file: {TARGET.name}")
    print(f"[INFO] lines before: {line_count_before}")

    # 멱등성
    if "// v868 fix (2026-05-16): sqm-core.js와 sqm-inline.js가 각자 _currentRoute" in text:
        print("[SKIP] already patched.")
        return 0

    count = text.count(ANCHOR)
    if count == 0:
        print("[ERROR] anchor not found.", file=sys.stderr)
        return 2
    if count > 1:
        print(f"[ERROR] anchor matched {count} times — ambiguous.", file=sys.stderr)
        return 3

    # 백업
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = TARGET.with_suffix(f".js.bak_getCurrentRoute_{ts}")
    shutil.copy2(TARGET, backup)
    print(f"[INFO] backup: {backup.name}")

    new_text = text.replace(ANCHOR, PATCH, 1)

    # IIFE 닫힘 보존 검증
    if not new_text.rstrip().endswith("})();"):
        print("[ERROR] IIFE closing `})();` lost after patch. abort.", file=sys.stderr)
        return 4

    TARGET.write_bytes(new_text.encode("utf-8"))
    print(f"[INFO] lines after: {new_text.count(chr(10))} (delta=+{new_text.count(chr(10)) - line_count_before})")
    print("[OK] patch applied.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
