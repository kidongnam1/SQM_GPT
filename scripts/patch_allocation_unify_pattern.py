# -*- coding: utf-8 -*-
"""
patch_allocation_unify_pattern.py
==================================
Purpose: Allocation 페이지를 Pending/Available 패턴으로 완전 통일
Why    : 사용자 요청 — "Pending과 Available과 동일한 로직으로 구현"
Fix    : 4개 toolbar 행 + 단계 되돌리기 행 모두 제거
         → 1줄 헤더로 통합 (Pending/Available 동일 패턴)
         액션은 우클릭 메뉴(showAllocActionMenu)로 통합
Result :
  Before: 5행 (헤더 + 데이터 + 정방향 + 취소 + 단계되돌리기) + 필터
  After:  1줄 헤더 + 필터 + 테이블 (Pending/Available과 동일)
Safety : 백엔드 API 보존, 함수 보존 (allocPickSelected/allocConfirmSelected 등)
         우클릭 메뉴 신규 추가 (액션 통합)
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

# ────────────────────────────────────────────────────────────
# 1. 헤더 + 4개 toolbar 행 + 단계 되돌리기 행 → 1줄 헤더로 통합
# ────────────────────────────────────────────────────────────
ANCHOR = """      /* ── 헤더 ── */
      '<div class="alloc-header" style="display:flex;align-items:center;gap:12px;padding:8px 0 8px">',
      '  <h2 style="margin:0">📋 판매 배정 (Allocation)</h2>',
      '  <span id="alloc-summary-label" style="color:var(--text-muted);font-size:.9rem"></span>',
      '  <button class="btn btn-secondary" onclick="renderPage(\\'allocation\\')" style="margin-left:auto">🔁 새로고침</button>',
      '</div>',
      /* v868 fix (2026-05-16): 4행 그룹화 + 라벨 명확화로 사용자 혼동 해소 */
      /* ── 행 1: 데이터 입출력 ── */
      '<div class="alloc-toolbar alloc-toolbar-data" style="display:flex;flex-wrap:wrap;align-items:center;gap:6px;padding:6px 10px;background:var(--panel);border:1px solid var(--panel-border);border-radius:6px;margin-bottom:6px">',
      '  <span style="font-size:11px;font-weight:600;color:var(--text-muted);width:60px">데이터:</span>',
      '  <button class="btn btn-primary" onclick="window.allocUploadExcel()">📂 Excel 업로드</button>',
      '  <button class="btn btn-secondary" onclick="window.allocExportExcel()" title="현재 배정 데이터 Excel 다운로드">📊 Excel 내보내기</button>',
      '  <button class="btn" onclick="window.allocOpenLotOverview()" title="LOT별 배정 현황 팝업">📦 LOT 현황</button>',
      '</div>',
      /* v868 fix (2026-05-16 v2): 승인 행 제거 (1인 운영 환경) + LOT 초기화 메인에서 제거 (우클릭으로 이동) */
      /* ── 행 2: 정방향 단계 (선택 LOT) ── */
      '<div class="alloc-toolbar alloc-toolbar-forward" style="display:flex;flex-wrap:wrap;align-items:center;gap:6px;padding:6px 10px;background:var(--panel);border:1px solid var(--panel-border);border-radius:6px;margin-bottom:6px">',
      '  <span style="font-size:11px;font-weight:600;color:#22c55e;width:60px">정방향 →:</span>',
      '  <button class="btn" onclick="window.allocPickSelected()" title="RESERVED → PICKED">📦 출고 실행 (PICKED)</button>',
      '  <button class="btn" onclick="window.allocConfirmSelected()" title="PICKED → SOLD">🔒 출고 확정 (SOLD)</button>',
      '</div>',
      /* v868 fix (2026-05-16 v4): SALE REF 취소 + 원스탑 롤백 제거 — 사용자 미사용 (백엔드 API는 보존) */
      /* ── 행 3: 역방향 (취소) — 단일 기능으로 축소 ── */
      '<div class="alloc-toolbar alloc-toolbar-reverse" style="display:flex;flex-wrap:wrap;align-items:center;gap:6px;padding:6px 10px;background:var(--panel);border:1px solid var(--panel-border);border-radius:6px;margin-bottom:6px">',
      '  <span style="font-size:11px;font-weight:600;color:#ef4444;width:60px">← 취소:</span>',
      '  <button class="btn btn-danger" onclick="window.allocCancelSelected()">❌ 선택 배정 취소</button>',
      '</div>',
      /* ── 단계 되돌리기 버튼 행 ── */
      '<div style="display:flex;flex-wrap:wrap;gap:6px;align-items:center;padding:6px 8px;background:var(--panel);border:1px solid var(--panel-border);border-radius:6px;margin-bottom:8px">',
      '  <span style="font-size:12px;font-weight:600;white-space:nowrap">&#x21A9; 단계 되돌리기:</span>',
      '  <button class="btn" onclick="window.allocRevertStep(\\'RESERVED\\')" style="font-size:12px">RESERVED &rarr; AVAILABLE</button>',
      '  <button class="btn" onclick="window.allocRevertStep(\\'PICKED\\')" style="font-size:12px">PICKED &rarr; RESERVED</button>',
      '  <button class="btn" onclick="window.allocRevertStep(\\'SOLD\\')" style="font-size:12px">SOLD &rarr; PICKED</button>',
      '</div>',"""

# v868 fix (2026-05-16 v5): Pending/Available 패턴으로 완전 통일 — 1줄 헤더
PATCH = """      /* v868 fix (2026-05-16 v5): Pending/Available 패턴으로 완전 통일 — 1줄 헤더 */
      /* ── 1줄 헤더 (제목 · 건수 · 액션 4개) ── */
      '<div class="alloc-header" style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;padding:8px 0 12px">',
      '  <h2 style="margin:0;font-size:16px">📋 판매 배정 (Allocation)</h2>',
      '  <span id="alloc-summary-label" style="color:var(--text-muted);font-size:12px"></span>',
      '  <div style="margin-left:auto;display:flex;gap:6px;align-items:center;flex-wrap:wrap">',
      '    <button class="btn btn-ghost" style="font-size:12px" onclick="renderPage(\\'allocation\\')" title="새로고침">🔄</button>',
      '    <button class="btn btn-primary" style="font-size:12px;padding:4px 10px" onclick="window.allocUploadExcel()" title="배정 Excel 업로드">📂 Excel 업로드</button>',
      '    <button class="btn btn-secondary" style="font-size:12px;padding:4px 10px" onclick="window.allocExportExcel()" title="현재 배정 데이터 Excel 다운로드">📊 Excel 내보내기</button>',
      '    <button class="btn" style="font-size:12px;padding:4px 10px" onclick="window.allocOpenLotOverview()" title="LOT별 배정 현황 팝업">📦 LOT 현황</button>',
      '    <button class="btn btn-danger" style="font-size:12px;padding:4px 10px" onclick="window.allocCancelSelected()" title="체크된 LOT 배정 일괄 취소">❌ 선택 배정 취소</button>',
      '  </div>',
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
    if "v868 fix (2026-05-16 v5)" in text:
        print("[SKIP] already patched.")
        return 0

    count = text.count(ANCHOR)
    if count == 0:
        print("[ERROR] anchor not found. 이전 패치 상태 확인 필요.", file=sys.stderr)
        return 2
    if count > 1:
        print(f"[ERROR] anchor matched {count} times.", file=sys.stderr)
        return 3

    # 백업
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = TARGET.with_suffix(f".js.bak_alloc_unify_{ts}")
    shutil.copy2(TARGET, backup)
    print(f"[INFO] backup: {backup.name}")

    new_text = text.replace(ANCHOR, PATCH, 1)

    if not new_text.rstrip().endswith("})();"):
        print("[ERROR] IIFE closing lost.", file=sys.stderr)
        return 4

    TARGET.write_bytes(new_text.encode("utf-8"))
    line_count_after = new_text.count("\n")
    print(f"[INFO] lines after: {line_count_after} (delta={line_count_after - line_count_before})")

    # syntax 검증
    r = subprocess.run(["node", "--check", str(TARGET)], capture_output=True, text=True)
    if r.returncode != 0:
        print(f"[FAIL] syntax: {r.stderr}")
        return 5

    print("[OK] Allocation = Pending/Available 패턴 통일 완료.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
