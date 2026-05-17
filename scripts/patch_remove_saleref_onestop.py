# -*- coding: utf-8 -*-
"""
patch_remove_saleref_onestop.py
================================
Purpose: SALE REF 취소 + 원스탑 롤백 (전체 초기화) UI 제거
Why    : 사용자 답변: "SALE REF 취소나 원스탑 롤백도 삭제해줘"
         사장님 1인 운영 환경 — 사용 안 함 명시
Fix    : sqm-inline.js의 "← 취소" 행에서 두 버튼 제거
         결과: 취소 행에는 "선택 배정 취소" 1개만 남음
Safety : 백엔드 API 보존 (/api/allocation/reset-all, /cancel-by-sale-ref)
         함수 보존 (window.allocResetAll, window.allocCancelBySaleRef)
         → 30초 작업으로 복원 가능
Rule   : CLAUDE.md Rule 5 — sqm-inline.js Python 스크립트만
Author : Ruby (Senior Software Architect) — 2026-05-16
"""
import sys
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
TARGET = ROOT / "frontend" / "js" / "sqm-inline.js"

# 현재 (LOT 초기화 제거 후) "← 취소" 행 상태
ANCHOR = """      /* ── 행 3: 역방향 (취소/원복) — LOT 초기화는 우클릭 메뉴로 이동 ── */
      '<div class="alloc-toolbar alloc-toolbar-reverse" style="display:flex;flex-wrap:wrap;align-items:center;gap:6px;padding:6px 10px;background:var(--panel);border:1px solid var(--panel-border);border-radius:6px;margin-bottom:6px">',
      '  <span style="font-size:11px;font-weight:600;color:#ef4444;width:60px">← 취소:</span>',
      '  <button class="btn btn-danger" onclick="window.allocCancelSelected()">❌ 선택 배정 취소</button>',
      '  <button class="btn" onclick="window.allocCancelBySaleRef()" title="SALE REF 입력 후 해당 배정 전체 취소">🔖 SALE REF 취소</button>',
      '  <button class="btn btn-danger" onclick="window.allocResetAll()" title="모든 RESERVED/PICKED/OUTBOUND 배정을 한 번에 AVAILABLE로 원복 (SOLD는 보호)">⚠️ 원스탑 롤백 (전체 초기화)</button>',
      '</div>',"""

PATCH = """      /* v868 fix (2026-05-16 v4): SALE REF 취소 + 원스탑 롤백 제거 — 사용자 미사용 (백엔드 API는 보존) */
      /* ── 행 3: 역방향 (취소) — 단일 기능으로 축소 ── */
      '<div class="alloc-toolbar alloc-toolbar-reverse" style="display:flex;flex-wrap:wrap;align-items:center;gap:6px;padding:6px 10px;background:var(--panel);border:1px solid var(--panel-border);border-radius:6px;margin-bottom:6px">',
      '  <span style="font-size:11px;font-weight:600;color:#ef4444;width:60px">← 취소:</span>',
      '  <button class="btn btn-danger" onclick="window.allocCancelSelected()">❌ 선택 배정 취소</button>',
      '</div>',"""


def main() -> int:
    if not TARGET.exists():
        print(f"[ERROR] target not found: {TARGET}", file=sys.stderr)
        return 1

    text = TARGET.read_text(encoding="utf-8")
    line_count_before = text.count("\n")
    print(f"[INFO] file: {TARGET.name}")
    print(f"[INFO] lines before: {line_count_before}")

    # 멱등성
    if "v868 fix (2026-05-16 v4)" in text:
        print("[SKIP] already patched.")
        return 0

    count = text.count(ANCHOR)
    if count == 0:
        print("[ERROR] anchor not found.", file=sys.stderr)
        return 2
    if count > 1:
        print(f"[ERROR] anchor matched {count} times.", file=sys.stderr)
        return 3

    # 백업
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = TARGET.with_suffix(f".js.bak_saleref_onestop_{ts}")
    shutil.copy2(TARGET, backup)
    print(f"[INFO] backup: {backup.name}")

    new_text = text.replace(ANCHOR, PATCH, 1)

    # IIFE 닫힘 보존
    if not new_text.rstrip().endswith("})();"):
        print("[ERROR] IIFE closing lost. abort.", file=sys.stderr)
        return 4

    TARGET.write_bytes(new_text.encode("utf-8"))
    line_count_after = new_text.count("\n")
    print(f"[INFO] lines after: {line_count_after} (delta={line_count_after - line_count_before})")

    # syntax 검증
    r = subprocess.run(["node", "--check", str(TARGET)], capture_output=True, text=True)
    if r.returncode != 0:
        print(f"[FAIL] syntax: {r.stderr}")
        return 5

    print("[OK] SALE REF + 원스탑 롤백 UI 제거 완료. 백엔드 API 보존.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
