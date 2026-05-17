"""
patch_p2_1_router.py — P2-1 라우터 단일화 리팩터링
=======================================================
목표: sqm-core.js 를 단일 권위 라우터로 승격
      sqm-inline.js 의 renderPage() 를 내부 포워더로 교체

변경 내용:
  [sqm-core.js]
    A) renderPage() switch-case 를 guard 패턴으로 업그레이드
       (window 함수 미노출 시 loadStubPage fallback)

  [sqm-inline.js]
    B) function renderPage(route) { ... } 전체 body → 1줄 forwarder
    C) window.renderPage = renderPage; 제거
    D) window.getCurrentRoute 재정의 제거
    E) window.loadAllocationPage = loadAllocationPage; 추가
       (sqm-inline의 단순화 버전이 sqm-allocation.js의 11개 버튼 버전 대신 사용되도록)
"""
import shutil, sys
from pathlib import Path
from datetime import datetime

BASE = Path("/sessions/eloquent-amazing-ramanujan/mnt/SQM_v868_claan/frontend/js")
ts = datetime.now().strftime("%Y%m%d_%H%M%S")
total_changes = 0

# ═══════════════════════════════════════════════════════════
# sqm-core.js 패치
# ═══════════════════════════════════════════════════════════
CORE = BASE / "sqm-core.js"
shutil.copy2(CORE, CORE.with_name(f"sqm-core.js.bak_p21_{ts}"))
print(f"[backup] sqm-core.js.bak_p21_{ts}")

core_src = CORE.read_text(encoding="utf-8")
core_orig = core_src
core_changes = 0

# A) switch-case 업그레이드: window.*() 직접 호출 → guard 패턴
OLD_A = (
    "    switch (route) {\n"
    "      case 'dashboard':  loadDashboard();     break;\n"
    "      case 'inventory':  window.loadInventoryPage();  break;\n"
    "      case 'pending':   window.loadPendingPage();   break;\n"
    "      case 'available':  window.loadAvailablePage();  break;  // v9.5 신규\n"
    "      case 'allocation': window.loadAllocationPage(); break;\n"
    "      case 'picked':     window.loadPickedPage();     break;\n"
    "      case 'inbound':    window.loadInboundPage();    break;\n"
    "      case 'outbound':   window.loadOutboundPage();   break;\n"
    "      case 'return':     window.loadReturnPage();     break;\n"
    "      case 'move':       window.loadMovePage();       break;\n"
    "      case 'log':        window.loadLogPage();        break;\n"
    "      case 'scan':       window.loadScanPage();       break;\n"
    "      case 'tonbag':     window.loadTonbagPage();     break;\n"
    "      default:           loadStubPage(route);  break;\n"
    "    }"
)
NEW_A = (
    "    // P2-1 (2026-05-17): 단일 권위 라우터 — guard 패턴 (window 미노출 시 stub)\n"
    "    switch (route) {\n"
    "      case 'dashboard':  loadDashboard();     break;\n"
    "      case 'inventory':  if (window.loadInventoryPage)  { window.loadInventoryPage();  } else { loadStubPage(route);  } break;\n"
    "      case 'pending':    if (window.loadPendingPage)    { window.loadPendingPage();    } else { loadStubPage(route);  } break;\n"
    "      case 'available':  if (window.loadAvailablePage)  { window.loadAvailablePage();  } else { loadStubPage(route);  } break;\n"
    "      // allocation: sqm-inline.js가 window.loadAllocationPage를 자신의 버전으로 덮어쓴 후 호출됨\n"
    "      case 'allocation': if (window.loadAllocationPage) { window.loadAllocationPage(); } else { loadStubPage(route);  } break;\n"
    "      case 'picked':     if (window.loadPickedPage)     { window.loadPickedPage();     } else { loadStubPage(route);  } break;\n"
    "      case 'inbound':    if (window.loadInboundPage)    { window.loadInboundPage();    } else { loadStubPage(route);  } break;\n"
    "      case 'outbound':   if (window.loadOutboundPage)   { window.loadOutboundPage();   } else { loadStubPage(route);  } break;\n"
    "      case 'return':     if (window.loadReturnPage)     { window.loadReturnPage();     } else { loadStubPage(route);  } break;\n"
    "      case 'move':       if (window.loadMovePage)       { window.loadMovePage();       } else { loadStubPage(route);  } break;\n"
    "      case 'log':        if (window.loadLogPage)        { window.loadLogPage();        } else { loadStubPage(route);  } break;\n"
    "      case 'scan':       if (window.loadScanPage)       { window.loadScanPage();       } else { loadStubPage(route);  } break;\n"
    "      case 'tonbag':     if (window.loadTonbagPage)     { window.loadTonbagPage();     } else { loadStubPage(route);  } break;\n"
    "      default:           loadStubPage(route);  break;\n"
    "    }"
)
if OLD_A in core_src:
    core_src = core_src.replace(OLD_A, NEW_A, 1); core_changes += 1
    print("[okA] sqm-core.js: renderPage switch guard 패턴 업그레이드")
else:
    print("[WARNA] sqm-core.js switch 앵커 없음")

if core_changes > 0:
    CORE.write_text(core_src, encoding="utf-8")
    print(f"[done] sqm-core.js 저장 (변경 {core_changes}곳)")
    old_n = core_orig.count("\n"); new_n = core_src.count("\n")
    print(f"[lines] {old_n} → {new_n} (diff {new_n-old_n:+d})")
else:
    print("[WARN] sqm-core.js 변경 없음 — 원본 유지")
total_changes += core_changes

# ═══════════════════════════════════════════════════════════
# sqm-inline.js 패치
# ═══════════════════════════════════════════════════════════
INLINE = BASE / "sqm-inline.js"
shutil.copy2(INLINE, INLINE.with_name(f"sqm-inline.js.bak_p21_{ts}"))
print(f"\n[backup] sqm-inline.js.bak_p21_{ts}")

inline_src = INLINE.read_text(encoding="utf-8")
inline_orig = inline_src
inline_changes = 0

# B) renderPage() 전체 body → forwarder
OLD_B = (
    "  function renderPage(route) {\n"
    "    _currentRoute = route;\n"
    "    closeAllMenus();\n"
    "    showPage(route);\n"
    "    try { getStore().setItem('sqm_last_tab', route); } catch {}\n"
    "    if (history.replaceState) history.replaceState(null,'','#' + route);\n"
    "    switch (route) {\n"
    "      case 'dashboard':  loadDashboard();     break;\n"
    "      // v868 fix (2026-05-17 전수): 모든 case를 window 함수로 위임 — IIFE 옛 함수 우회\n"
    "      case 'inventory':  if (window.loadInventoryPage)  { window.loadInventoryPage();  } else { loadInventoryPage();  } break;\n"
    "      // v868 053fa7a — PENDING 입고 대기 워크플로우 (sqm-inventory.js 노출)\n"
    "      case 'pending':    if (window.loadPendingPage)    { window.loadPendingPage();    } else { loadStubPage(route);  } break;\n"
    "      // v868 v9.5 — AVAILABLE 재고 필터 뷰 (sqm-inventory.js 노출)\n"
    "      case 'available':  if (window.loadAvailablePage)  { window.loadAvailablePage();  } else { loadStubPage(route);  } break;\n"
    "      // v868 fix (2026-05-17 +): Allocation은 sqm-inline.js의 단순화 버전 유지\n"
    "      // (sqm-allocation.js의 원본 11개 버튼 버전이 window 덮어쓰지 못하게 직접 호출)\n"
    "      case 'allocation': loadAllocationPage(); break;\n"
    "      // v868 fix (2026-05-17): Picked/Outbound도 window 함수로 위임 (sqm-picked.js/sqm-logistics.js 우선)\n"
    "      case 'picked':     if (window.loadPickedPage)     { window.loadPickedPage();     } else { loadPickedPage();     } break;\n"
    "      case 'inbound':    if (window.loadInboundPage)    { window.loadInboundPage();    } else { loadInboundPage();    } break;\n"
    "      case 'outbound':   if (window.loadOutboundPage)   { window.loadOutboundPage();   } else { loadOutboundPage();   } break;\n"
    "      case 'return':     if (window.loadReturnPage)     { window.loadReturnPage();     } else { loadReturnPage();     } break;\n"
    "      case 'move':       if (window.loadMovePage)       { window.loadMovePage();       } else { loadMovePage();       } break;\n"
    "      case 'log':        if (window.loadLogPage)        { window.loadLogPage();        } else { loadLogPage();        } break;\n"
    "      case 'scan':       if (window.loadScanPage)       { window.loadScanPage();       } else { loadScanPage();       } break;\n"
    "      case 'tonbag':     if (window.loadTonbagPage)     { window.loadTonbagPage();     } else { loadTonbagPage();     } break;\n"
    "      default:           loadStubPage(route);  break;\n"
    "    }\n"
    "  }"
)
NEW_B = (
    "  function renderPage(route) {\n"
    "    // P2-1 (2026-05-17): 라우터 단일화 — sqm-core.js가 단일 권위 라우터\n"
    "    // 이 함수는 IIFE 내부 호출을 window.renderPage(sqm-core)로 포워딩만 함\n"
    "    window.renderPage(route);\n"
    "  }"
)
if OLD_B in inline_src:
    inline_src = inline_src.replace(OLD_B, NEW_B, 1); inline_changes += 1
    print("[okB] sqm-inline.js: renderPage → 1줄 forwarder 교체")
else:
    print("[WARNB] sqm-inline.js renderPage 앵커 없음 — 전체 함수 매칭 실패")
    idx = inline_src.find("function renderPage(route)")
    if idx >= 0:
        print("  → 현재 함수 시작:", repr(inline_src[idx:idx+80]))

# C+D) window.renderPage / window.getCurrentRoute 재정의 제거 + window.loadAllocationPage 추가
OLD_CD = (
    "  window.renderPage = renderPage;\n"
    "  // v868 fix (2026-05-16): sqm-core.js와 sqm-inline.js가 각자 _currentRoute를 가져 상태 불일치 발생\n"
    "  // sqm-inventory.js의 loadPendingPage/loadAvailablePage가 window.getCurrentRoute()로 sqm-core의 stale 값을\n"
    "  // 받아 빈 화면이 표시되는 버그 → sqm-inline.js의 _currentRoute(가장 최신)를 반환하도록 덮어씀\n"
    "  window.getCurrentRoute = function() { return _currentRoute; };"
)
NEW_CD = (
    "  // P2-1 (2026-05-17): window.renderPage 및 getCurrentRoute는 sqm-core.js 버전이 권위\n"
    "  // (sqm-inline.js의 renderPage는 내부 포워더, window 재정의 불필요)\n"
    "  // allocation: sqm-inline의 단순화 버전을 window에 노출해 sqm-core.js가 사용하게 함\n"
    "  window.loadAllocationPage = loadAllocationPage;"
)
if OLD_CD in inline_src:
    inline_src = inline_src.replace(OLD_CD, NEW_CD, 1); inline_changes += 1
    print("[okCD] sqm-inline.js: window.renderPage/getCurrentRoute 재정의 제거 + loadAllocationPage 노출")
else:
    print("[WARNCD] sqm-inline.js window.renderPage 앵커 없음")
    idx = inline_src.find("window.renderPage = renderPage;")
    if idx >= 0:
        print("  →", repr(inline_src[max(0,idx-10):idx+200]))

if inline_changes > 0:
    INLINE.write_text(inline_src, encoding="utf-8")
    print(f"[done] sqm-inline.js 저장 (변경 {inline_changes}곳)")
    old_n = inline_orig.count("\n"); new_n = inline_src.count("\n")
    print(f"[lines] {old_n} → {new_n} (diff {new_n-old_n:+d})")
else:
    print("[WARN] sqm-inline.js 변경 없음")
total_changes += inline_changes

# ═══════════════════════════════════════════════════════════
# 검증
# ═══════════════════════════════════════════════════════════
print(f"\n[총 변경] {total_changes}곳 (목표 3)")
if total_changes < 3:
    print("[WARN] 일부 패치 미적용 — 위 WARN 확인 필요")
