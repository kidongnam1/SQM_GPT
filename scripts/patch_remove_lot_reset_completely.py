# -*- coding: utf-8 -*-
"""
patch_remove_lot_reset_completely.py
=====================================
Purpose: LOT 초기화 기능 UI에서 완전 제거 — 사용자가 안 쓴다고 명시
Why    : 사용자 답변: "LOT 초기화 기능도 삭제해줘"
Fix    : 1) sqm-inline.js — 우클릭 메뉴 "🧹 이 행 초기화 (삭제)" 항목 제거
         2) sqm-inline.js — Allocation 페이지 안내 메시지 제거
         3) sqm-allocation.js — 우클릭 메뉴 동일 항목 제거 (안전 차원)
         4) 함수 `allocResetSelected`는 유지 (백엔드 API 호출 코드 보존)
            → 나중에 필요해지면 1줄 추가로 복원 가능
Safety : 백엔드 API (/api/allocation/{lot}/reset) 그대로 유지 (DB 보호)
Rule   : CLAUDE.md Rule 5 — sqm-inline.js(7556줄) Python 스크립트만
Author : Ruby (Senior Software Architect) — 2026-05-16
"""
import sys
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
INLINE = ROOT / "frontend" / "js" / "sqm-inline.js"
ALLOC = ROOT / "frontend" / "js" / "sqm-allocation.js"

# ────────────────────────────────────────────────────────────
# 1. sqm-inline.js: 우클릭 메뉴 항목 제거
# ────────────────────────────────────────────────────────────
INLINE_MENU_ANCHOR = """    }, false);

    mi('🧹 이 행 초기화 (삭제)', function(){
      if (!confirm('🧹 ' + lot + '\\nallocation 기록 삭제 + inventory AVAILABLE 원복\\n(SOLD 는 보호됨)\\n계속하시겠습니까?')) return;
      apiPost('/api/allocation/' + encodeURIComponent(lot) + '/reset', {})
        .then(function(res){ showToast('success', (res.data && res.data.message) || (lot + ' 초기화됨')); loadAllocationPage(); })
        .catch(function(err){ showToast('error', '초기화 실패: ' + (err.message || err)); });
    }, true);

    document.body.appendChild(m);"""

INLINE_MENU_PATCH = """    }, false);

    // v868 fix (2026-05-16 v3): LOT 초기화 메뉴 제거 — 사용자 미사용 (백엔드 API는 보존)

    document.body.appendChild(m);"""

# ────────────────────────────────────────────────────────────
# 2. sqm-inline.js: 안내 메시지 제거 (Allocation 페이지 toolbar)
# ────────────────────────────────────────────────────────────
INLINE_HINT_ANCHOR = """      '  <button class="btn btn-danger" onclick="window.allocResetAll()" title="모든 RESERVED/PICKED/OUTBOUND 배정을 한 번에 AVAILABLE로 원복 (SOLD는 보호)">⚠️ 원스탑 롤백 (전체 초기화)</button>',
      '  <span style="margin-left:auto;font-size:11px;color:var(--text-muted);font-style:italic">💡 LOT 초기화는 각 행에서 우클릭 → "🧹 이 행 초기화" 사용</span>',
      '</div>',"""

INLINE_HINT_PATCH = """      '  <button class="btn btn-danger" onclick="window.allocResetAll()" title="모든 RESERVED/PICKED/OUTBOUND 배정을 한 번에 AVAILABLE로 원복 (SOLD는 보호)">⚠️ 원스탑 롤백 (전체 초기화)</button>',
      '</div>',"""

# ────────────────────────────────────────────────────────────
# 3. sqm-allocation.js: 우클릭 메뉴 항목 제거 (안전 차원 — sqm-inline.js가 덮어쓰지만 양쪽 정리)
# ────────────────────────────────────────────────────────────
ALLOC_MENU_ANCHOR = """    }, false);

    mi('🧹 이 행 초기화 (삭제)', function(){
      if (!confirm('🧹 ' + lot + '\\nallocation 기록 삭제 + inventory AVAILABLE 원복\\n(SOLD 는 보호됨)\\n계속하시겠습니까?')) return;
      apiPost('/api/allocation/' + encodeURIComponent(lot) + '/reset', {})
        .then(function(res){ showToast('success', (res.data && res.data.message) || (lot + ' 초기화됨')); loadAllocationPage(); })
        .catch(function(err){ showToast('error', '초기화 실패: ' + (err.message || err)); });
    }, true);

    document.body.appendChild(m);"""

ALLOC_MENU_PATCH = """    }, false);

    // v868 fix (2026-05-16 v3): LOT 초기화 메뉴 제거 — 사용자 미사용 (백엔드 API는 보존)

    document.body.appendChild(m);"""


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
    # IIFE 닫힘 보존 (둘 다 IIFE)
    if not new_text.rstrip().endswith("})();"):
        print(f"  [ERROR] {label} IIFE closing lost. abort.")
        return False
    file_path.write_text(new_text, encoding="utf-8")
    print(f"  [OK] {label} applied.")
    return True


def main() -> int:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    bk_inline = INLINE.with_suffix(f".js.bak_lot_reset_remove_{ts}")
    bk_alloc = ALLOC.with_suffix(f".js.bak_lot_reset_remove_{ts}")
    shutil.copy2(INLINE, bk_inline)
    shutil.copy2(ALLOC, bk_alloc)
    print(f"[INFO] backups: {bk_inline.name}, {bk_alloc.name}")
    print()

    print("=== sqm-inline.js ===")
    ok = True
    ok &= apply_patch(INLINE, INLINE_MENU_ANCHOR, INLINE_MENU_PATCH, "(I-M) 우클릭 메뉴 제거")
    ok &= apply_patch(INLINE, INLINE_HINT_ANCHOR, INLINE_HINT_PATCH, "(I-H) 안내 메시지 제거")

    print()
    print("=== sqm-allocation.js ===")
    ok &= apply_patch(ALLOC, ALLOC_MENU_ANCHOR, ALLOC_MENU_PATCH, "(A-M) 우클릭 메뉴 제거")

    if not ok:
        print("\n[FAIL] one or more patches failed.")
        return 2

    # syntax 검증
    print()
    for f in (INLINE, ALLOC):
        r = subprocess.run(["node", "--check", str(f)], capture_output=True, text=True)
        if r.returncode != 0:
            print(f"[FAIL] {f.name}: {r.stderr}")
            return 3
        print(f"[OK] {f.name} syntax OK")

    print()
    print("🎉 LOT 초기화 UI 완전 제거 완료 (백엔드 API는 보존)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
