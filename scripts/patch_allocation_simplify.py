# -*- coding: utf-8 -*-
"""
patch_allocation_simplify.py
============================
Purpose: Allocation 페이지 UI 단순화 — 4행 그룹화 + 라벨 명확화
Why    : 사용자 보고: 11개 버튼 한 줄에 나열되어 혼란
         "LOT 초기화 vs 전체 초기화" 라벨 비슷해서 혼동 야기
Fix    :
  1. 그룹별 4행 분리: [데이터] / [승인] / [정방향] / [취소/원복]
  2. 라벨 변경: "전체 초기화" → "원스탑 롤백 (전체 초기화)"
  3. 라벨 변경: "LOT 초기화" → "LOT 초기화 (배정 삭제)"
Target : sqm-inline.js (마지막 로드, 우선 적용됨)
Rule   : CLAUDE.md Rule 5 (강화) — 7551줄 IIFE 파일은 Python 스크립트만
Author : Ruby (Senior Software Architect) — 2026-05-16
"""
import sys
import shutil
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
TARGET = ROOT / "frontend" / "js" / "sqm-inline.js"

# Before: 11개 버튼이 한 toolbar div에 있음
ANCHOR = """      /* ── 액션 툴바 (v864-2 AllocationDialog primary_buttons 매핑) ── */
      '<div class="alloc-toolbar" style="display:flex;flex-wrap:wrap;align-items:center;gap:6px;padding:8px 10px;background:var(--panel);border:1px solid var(--panel-border);border-radius:6px;margin-bottom:8px">',
      '  <button class="btn btn-primary" onclick="window.allocUploadExcel()">📂 Excel 업로드</button>',
      '  <button class="btn" onclick="window.allocApplyApproved()">📌 승인분 반영</button>',
      '  <button class="btn" onclick="window.allocShowApprovalQueue()">✅ 승인 대기</button>',
      '  <span style="width:1px;height:22px;background:var(--panel-border);margin:0 4px"></span>',
      '  <button class="btn btn-danger" onclick="window.allocCancelSelected()">❌ 선택 배정 취소</button>',
      '  <span style="width:1px;height:22px;background:var(--panel-border);margin:0 4px"></span>',
      /* 백엔드 엔드포인트 미구현 — Sprint 1-1-E에서 연결 */
      '  <button class="btn" onclick="window.allocPickSelected()" title="RESERVED → PICKED">📦 출고 실행 (PICKED)</button>',
      '  <button class="btn" onclick="window.allocConfirmSelected()" title="PICKED → SOLD">🔒 출고 확정 (SOLD)</button>',
      '  <button class="btn" onclick="window.allocResetSelected()" title="LOT 배정 완전 삭제">🧹 LOT 초기화</button>',
      '  <span style="width:1px;height:22px;background:var(--panel-border);margin:0 4px"></span>',
      '  <button class="btn btn-danger" onclick="window.allocResetAll()" title="모든 배정 취소 + AVAILABLE 원복">⚠️ 전체 초기화</button>',
      '  <button class="btn" onclick="window.allocCancelBySaleRef()" title="SALE REF 입력 후 해당 배정 전체 취소">🔖 SALE REF 취소</button>',
      '  <button class="btn" onclick="window.allocOpenLotOverview()" title="LOT별 배정 현황 팝업">📦 LOT 현황</button>',
      '  <button class="btn btn-secondary" onclick="window.allocExportExcel()" title="현재 배정 데이터 Excel 다운로드">📊 Excel 내보내기</button>',
      '</div>',"""

# After: 4행으로 그룹화 + 라벨 명확화 (v868 fix 2026-05-16)
PATCH = """      /* v868 fix (2026-05-16): 4행 그룹화 + 라벨 명확화로 사용자 혼동 해소 */
      /* ── 행 1: 데이터 입출력 ── */
      '<div class="alloc-toolbar alloc-toolbar-data" style="display:flex;flex-wrap:wrap;align-items:center;gap:6px;padding:6px 10px;background:var(--panel);border:1px solid var(--panel-border);border-radius:6px;margin-bottom:6px">',
      '  <span style="font-size:11px;font-weight:600;color:var(--text-muted);width:60px">데이터:</span>',
      '  <button class="btn btn-primary" onclick="window.allocUploadExcel()">📂 Excel 업로드</button>',
      '  <button class="btn btn-secondary" onclick="window.allocExportExcel()" title="현재 배정 데이터 Excel 다운로드">📊 Excel 내보내기</button>',
      '  <button class="btn" onclick="window.allocOpenLotOverview()" title="LOT별 배정 현황 팝업">📦 LOT 현황</button>',
      '</div>',
      /* ── 행 2: 승인 워크플로우 ── */
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


def main() -> int:
    if not TARGET.exists():
        print(f"[ERROR] target not found: {TARGET}", file=sys.stderr)
        return 1

    text = TARGET.read_text(encoding="utf-8")
    line_count_before = text.count("\n")
    print(f"[INFO] file: {TARGET.name}")
    print(f"[INFO] lines before: {line_count_before}")

    # 멱등성
    if "alloc-toolbar-data" in text:
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
    backup = TARGET.with_suffix(f".js.bak_alloc_simplify_{ts}")
    shutil.copy2(TARGET, backup)
    print(f"[INFO] backup: {backup.name}")

    new_text = text.replace(ANCHOR, PATCH, 1)

    # IIFE 닫힘 보존 검증
    if not new_text.rstrip().endswith("})();"):
        print("[ERROR] IIFE closing `})();` lost. abort.", file=sys.stderr)
        return 4

    TARGET.write_bytes(new_text.encode("utf-8"))
    line_count_after = new_text.count("\n")
    print(f"[INFO] lines after: {line_count_after} (delta=+{line_count_after - line_count_before})")
    print("[OK] patch applied — Allocation 4행 그룹화 + 라벨 명확화 완료.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
