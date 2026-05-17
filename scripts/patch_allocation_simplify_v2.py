# -*- coding: utf-8 -*-
"""
patch_allocation_simplify_v2.py
================================
Purpose: Allocation 2차 단순화 — 승인 행 제거 + LOT 초기화 메인 toolbar에서 제거
Why    : 사용자 답변 (옵션 A):
         Q1=A: 승인 워크플로우 안 씀 (사장님 1인 운영, 입력자=승인자)
         Q2=A: LOT 초기화 한 번도 안 씀
         → 승인 행 자체 제거 + LOT 초기화 버튼 메인에서 제거
         (LOT 초기화는 우클릭 메뉴에 "🧹 이 행 초기화 (삭제)"로 이미 존재)
Result : 4행 → 3행, 11개 → 6개 메인 버튼 (45% 감소)
Rule   : CLAUDE.md Rule 5 — sqm-inline.js(7561줄) Python 스크립트만
Author : Ruby (Senior Software Architect) — 2026-05-16
"""
import sys
import shutil
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
TARGET = ROOT / "frontend" / "js" / "sqm-inline.js"

# Step 1차 패치 후의 4행 그룹화 상태 → 3행으로 축소
# (승인 행 전체 제거 + LOT 초기화 버튼 제거)
ANCHOR = """      /* ── 행 2: 승인 워크플로우 ── */
      '<div class="alloc-toolbar alloc-toolbar-approval" style="display:flex;flex-wrap:wrap;align-items:center;gap:6px;padding:6px 10px;background:var(--panel);border:1px solid var(--panel-border);border-radius:6px;margin-bottom:6px">',
      '  <span style="font-size:11px;font-weight:600;color:var(--text-muted);width:60px">승인:</span>',
      '  <button class="btn" onclick="window.allocApplyApproved()">📌 승인분 반영</button>',
      '  <button class="btn" onclick="window.allocShowApprovalQueue()">✅ 승인 대기</button>',
      '</div>',
      /* ── 행 3: 정방향 단계 (선택 LOT) ── */
      '<div class="alloc-toolbar alloc-toolbar-forward" style="display:flex;flex-wrap:wrap;align-items:center;gap:6px;padding:6px 10px;background:var(--panel);border:1px solid var(--panel-border);border-radius:6px;margin-bottom:6px">',
      '  <span style="font-size:11px;font-weight:600;color:#22c55e;width:60px">정방향 →:</span>',
      '  <button class="btn" onclick="window.allocPickSelected()" title="RESERVED → PICKED">📦 출고 실행 (PICKED)</button>',
      '  <button class="btn" onclick="window.allocConfirmSelected()" title="PICKED → SOLD">🔒 출고 확정 (SOLD)</button>',
      '</div>',
      /* ── 행 4: 역방향 (취소/원복) ── */
      '<div class="alloc-toolbar alloc-toolbar-reverse" style="display:flex;flex-wrap:wrap;align-items:center;gap:6px;padding:6px 10px;background:var(--panel);border:1px solid var(--panel-border);border-radius:6px;margin-bottom:6px">',
      '  <span style="font-size:11px;font-weight:600;color:#ef4444;width:60px">← 취소:</span>',
      '  <button class="btn btn-danger" onclick="window.allocCancelSelected()">❌ 선택 배정 취소</button>',
      '  <button class="btn" onclick="window.allocResetSelected()" title="선택된 LOT의 배정 기록을 완전 삭제 (allocation_plan 행 제거)">🧹 LOT 초기화 (배정 삭제)</button>',
      '  <button class="btn" onclick="window.allocCancelBySaleRef()" title="SALE REF 입력 후 해당 배정 전체 취소">🔖 SALE REF 취소</button>',
      '  <button class="btn btn-danger" onclick="window.allocResetAll()" title="모든 RESERVED/PICKED/OUTBOUND 배정을 한 번에 AVAILABLE로 원복 (SOLD는 보호)">⚠️ 원스탑 롤백 (전체 초기화)</button>',
      '</div>',"""

PATCH = """      /* v868 fix (2026-05-16 v2): 승인 행 제거 (1인 운영 환경) + LOT 초기화 메인에서 제거 (우클릭으로 이동) */
      /* ── 행 2: 정방향 단계 (선택 LOT) ── */
      '<div class="alloc-toolbar alloc-toolbar-forward" style="display:flex;flex-wrap:wrap;align-items:center;gap:6px;padding:6px 10px;background:var(--panel);border:1px solid var(--panel-border);border-radius:6px;margin-bottom:6px">',
      '  <span style="font-size:11px;font-weight:600;color:#22c55e;width:60px">정방향 →:</span>',
      '  <button class="btn" onclick="window.allocPickSelected()" title="RESERVED → PICKED">📦 출고 실행 (PICKED)</button>',
      '  <button class="btn" onclick="window.allocConfirmSelected()" title="PICKED → SOLD">🔒 출고 확정 (SOLD)</button>',
      '</div>',
      /* ── 행 3: 역방향 (취소/원복) — LOT 초기화는 우클릭 메뉴로 이동 ── */
      '<div class="alloc-toolbar alloc-toolbar-reverse" style="display:flex;flex-wrap:wrap;align-items:center;gap:6px;padding:6px 10px;background:var(--panel);border:1px solid var(--panel-border);border-radius:6px;margin-bottom:6px">',
      '  <span style="font-size:11px;font-weight:600;color:#ef4444;width:60px">← 취소:</span>',
      '  <button class="btn btn-danger" onclick="window.allocCancelSelected()">❌ 선택 배정 취소</button>',
      '  <button class="btn" onclick="window.allocCancelBySaleRef()" title="SALE REF 입력 후 해당 배정 전체 취소">🔖 SALE REF 취소</button>',
      '  <button class="btn btn-danger" onclick="window.allocResetAll()" title="모든 RESERVED/PICKED/OUTBOUND 배정을 한 번에 AVAILABLE로 원복 (SOLD는 보호)">⚠️ 원스탑 롤백 (전체 초기화)</button>',
      '  <span style="margin-left:auto;font-size:11px;color:var(--text-muted);font-style:italic">💡 LOT 초기화는 각 행에서 우클릭 → "🧹 이 행 초기화" 사용</span>',
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
    if "v868 fix (2026-05-16 v2)" in text:
        print("[SKIP] already patched.")
        return 0

    count = text.count(ANCHOR)
    if count == 0:
        print("[ERROR] anchor not found. v1 패치가 먼저 적용되어야 함.", file=sys.stderr)
        return 2
    if count > 1:
        print(f"[ERROR] anchor matched {count} times.", file=sys.stderr)
        return 3

    # 백업
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = TARGET.with_suffix(f".js.bak_alloc_v2_{ts}")
    shutil.copy2(TARGET, backup)
    print(f"[INFO] backup: {backup.name}")

    new_text = text.replace(ANCHOR, PATCH, 1)

    if not new_text.rstrip().endswith("})();"):
        print("[ERROR] IIFE closing lost. abort.", file=sys.stderr)
        return 4

    TARGET.write_bytes(new_text.encode("utf-8"))
    line_count_after = new_text.count("\n")
    print(f"[INFO] lines after: {line_count_after} (delta={line_count_after - line_count_before})")
    print("[OK] patch applied — 4행→3행, 11개→6개 메인 버튼 (45% 감소).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
