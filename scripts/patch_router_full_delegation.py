# -*- coding: utf-8 -*-
"""
patch_router_full_delegation.py
================================
Purpose: sqm-inline.js 라우터의 모든 case를 window 함수로 일괄 위임
Why    : 전수 검사 결과 — 7개 case가 IIFE 내부 옛 함수 호출 중
         (inventory/allocation/inbound/return/move/log/scan/tonbag)
         이전에 pending/available/picked/outbound만 위임했지만 나머지도 동일 패치 필요
Fix    : 각 case에 if (window.loadXxxPage) { window.loadXxxPage() } else { loadXxxPage() } 패턴
Note   : dashboard는 window 노출 없음 (sqm-inline 내부 함수만) → 그대로 둠
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

# 현재 상태 (pending/available/picked/outbound는 이미 위임됨)
ANCHOR = """      case 'dashboard':  loadDashboard();     break;
      case 'inventory':  loadInventoryPage();  break;
      // v868 053fa7a — PENDING 입고 대기 워크플로우 (sqm-inventory.js 노출)
      case 'pending':    if (window.loadPendingPage)   { window.loadPendingPage();   } else { loadStubPage(route); } break;
      // v868 v9.5 — AVAILABLE 재고 필터 뷰 (sqm-inventory.js 노출)
      case 'available':  if (window.loadAvailablePage) { window.loadAvailablePage(); } else { loadStubPage(route); } break;
      case 'allocation': loadAllocationPage(); break;
      // v868 fix (2026-05-17): Picked/Outbound도 window 함수로 위임 (sqm-picked.js/sqm-logistics.js 우선)
      case 'picked':     if (window.loadPickedPage)   { window.loadPickedPage();   } else { loadPickedPage(); } break;
      case 'inbound':    loadInboundPage();    break;
      case 'outbound':   if (window.loadOutboundPage) { window.loadOutboundPage(); } else { loadOutboundPage(); } break;
      case 'return':     loadReturnPage();     break;
      case 'move':       loadMovePage();       break;
      case 'log':        loadLogPage();        break;
      case 'scan':       loadScanPage();       break;
      case 'tonbag':     loadTonbagPage();     break;"""

# 모든 case를 window 함수로 위임 (dashboard는 window 노출 없어서 제외)
PATCH = """      case 'dashboard':  loadDashboard();     break;
      // v868 fix (2026-05-17 전수): 모든 case를 window 함수로 위임 — IIFE 옛 함수 우회
      case 'inventory':  if (window.loadInventoryPage)  { window.loadInventoryPage();  } else { loadInventoryPage();  } break;
      // v868 053fa7a — PENDING 입고 대기 워크플로우 (sqm-inventory.js 노출)
      case 'pending':    if (window.loadPendingPage)    { window.loadPendingPage();    } else { loadStubPage(route);  } break;
      // v868 v9.5 — AVAILABLE 재고 필터 뷰 (sqm-inventory.js 노출)
      case 'available':  if (window.loadAvailablePage)  { window.loadAvailablePage();  } else { loadStubPage(route);  } break;
      case 'allocation': if (window.loadAllocationPage) { window.loadAllocationPage(); } else { loadAllocationPage(); } break;
      // v868 fix (2026-05-17): Picked/Outbound도 window 함수로 위임 (sqm-picked.js/sqm-logistics.js 우선)
      case 'picked':     if (window.loadPickedPage)     { window.loadPickedPage();     } else { loadPickedPage();     } break;
      case 'inbound':    if (window.loadInboundPage)    { window.loadInboundPage();    } else { loadInboundPage();    } break;
      case 'outbound':   if (window.loadOutboundPage)   { window.loadOutboundPage();   } else { loadOutboundPage();   } break;
      case 'return':     if (window.loadReturnPage)     { window.loadReturnPage();     } else { loadReturnPage();     } break;
      case 'move':       if (window.loadMovePage)       { window.loadMovePage();       } else { loadMovePage();       } break;
      case 'log':        if (window.loadLogPage)        { window.loadLogPage();        } else { loadLogPage();        } break;
      case 'scan':       if (window.loadScanPage)       { window.loadScanPage();       } else { loadScanPage();       } break;
      case 'tonbag':     if (window.loadTonbagPage)     { window.loadTonbagPage();     } else { loadTonbagPage();     } break;"""


def main() -> int:
    text = TARGET.read_text(encoding="utf-8")

    if "v868 fix (2026-05-17 전수): 모든 case를 window 함수로 위임" in text:
        print("[SKIP] already patched.")
        return 0
    if ANCHOR not in text:
        print("[ERROR] anchor not found", file=sys.stderr)
        return 2
    if text.count(ANCHOR) > 1:
        print(f"[ERROR] matched {text.count(ANCHOR)} times", file=sys.stderr)
        return 3

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = TARGET.with_suffix(f".js.bak_router_full_{ts}")
    shutil.copy2(TARGET, backup)
    print(f"[INFO] backup: {backup.name}")

    new_text = text.replace(ANCHOR, PATCH, 1)
    if not new_text.rstrip().endswith("})();"):
        print("[ERROR] IIFE closing lost", file=sys.stderr)
        return 4

    TARGET.write_bytes(new_text.encode("utf-8"))
    r = subprocess.run(["node", "--check", str(TARGET)], capture_output=True, text=True)
    if r.returncode != 0:
        print(f"[FAIL] syntax: {r.stderr}")
        return 5
    print("[OK] 라우터 전수 위임 완료 — 12개 case 모두 window 함수 우선")
    return 0


if __name__ == "__main__":
    sys.exit(main())
