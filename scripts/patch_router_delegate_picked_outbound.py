# -*- coding: utf-8 -*-
"""
patch_router_delegate_picked_outbound.py
=========================================
Purpose: sqm-inline.js 라우터의 case 'picked'/'outbound'를 window 함수로 위임
Why    : 사용자 보고 — Picked/Outbound 헤더에 새로고침만 보임
         원인: sqm-inline.js의 옛 loadPickedPage/loadOutboundPage 가 IIFE 내부에서 호출됨
               (window.loadPickedPage 무시) → 새 sqm-picked.js / sqm-logistics.js 코드 미적용
Fix    : case 'pending'/'available'과 동일 패턴 — window.loadPickedPage / window.loadOutboundPage 호출
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

ANCHOR = """      case 'allocation': loadAllocationPage(); break;
      case 'picked':     loadPickedPage();     break;
      case 'inbound':    loadInboundPage();    break;
      case 'outbound':   loadOutboundPage();   break;"""

PATCH = """      case 'allocation': loadAllocationPage(); break;
      // v868 fix (2026-05-17): Picked/Outbound도 window 함수로 위임 (sqm-picked.js/sqm-logistics.js 우선)
      case 'picked':     if (window.loadPickedPage)   { window.loadPickedPage();   } else { loadPickedPage(); } break;
      case 'inbound':    loadInboundPage();    break;
      case 'outbound':   if (window.loadOutboundPage) { window.loadOutboundPage(); } else { loadOutboundPage(); } break;"""


def main() -> int:
    text = TARGET.read_text(encoding="utf-8")

    if "v868 fix (2026-05-17): Picked/Outbound도 window 함수로 위임" in text:
        print("[SKIP] already patched.")
        return 0
    if ANCHOR not in text:
        print("[ERROR] anchor not found")
        return 2
    if text.count(ANCHOR) > 1:
        print(f"[ERROR] matched {text.count(ANCHOR)} times")
        return 3

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = TARGET.with_suffix(f".js.bak_router_delegate_{ts}")
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
    print("[OK] case 'picked'/'outbound' → window 함수 위임 완료")
    return 0


if __name__ == "__main__":
    sys.exit(main())
