# -*- coding: utf-8 -*-
"""
Phase B - Slice S8: 모달 인프라 추출 (드래그/리사이즈)

sqm-core.js에 없음 → 새 모듈 추출 필요 (S6a/S1과 유사 패턴)

대상: sqm-inline.js
- 본문: 현 line 2083-2217 (135줄)
  - 섹션 주석 8. MODAL
  - window._sqmZ 초기화
  - var _zFloatTop
  - function _bringToFront + window._bringToFront 노출
  - function _makeDraggableResizable
  - function _sqmExtractModalHeadingText
  - function _sqmSyncModalHeaderFromContent + window._sqmSyncModalHeaderFromContent 노출
  - window._sqmSetModalTitleBar = function 직접 정의
  - function ensureModal
  - function showDataModal
- 잔재: 별도 line 4812-4813 (2줄)
  - window.showDataModal = showDataModal;
  - window._makeDraggableResizable = _makeDraggableResizable;
  (line 4811 주석은 그대로 둠 — 인접 노출들과 묶여 있음)

내부 의존:
- window._sqmZ — IIFE 외부 공유 (다른 JS 파일도 사용) → 그대로 유지
- escapeHtml, _sqmExtractModalHeadingText — 모듈 내부

호출 호환:
- sqm-inline.js 내부 호출 (showDataModal 15회, _bringToFront 3회 등) → window.* 폴백
- 다른 파일 (sqm-listview.js, sqm-tonbag.js 등) → 이미 window.* 사용

사용:
    python scripts/patch_split_modal_S8.py --dry-run
    python scripts/patch_split_modal_S8.py
    python scripts/patch_split_modal_S8.py --rollback
"""

import argparse
import sys
import shutil
from datetime import datetime
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

ROOT = Path(__file__).resolve().parent.parent
INLINE = ROOT / 'frontend' / 'js' / 'sqm-inline.js'
MODAL_FILE = ROOT / 'frontend' / 'js' / 'sqm-util-modal.js'
HTML = ROOT / 'frontend' / 'index.html'
SLICE_ID = 'S8'

# 본문 추출 (1-based)
BODY_START = 2083
BODY_END = 2217
BODY_COUNT = BODY_END - BODY_START + 1  # 135줄

# 잔재 노출 라인 (2줄, 인접)
RESIDUE_LINE_1 = '  window.showDataModal = showDataModal;'
RESIDUE_LINE_2 = '  window._makeDraggableResizable = _makeDraggableResizable;'

# 시그니처
SIG_BODY_START_PREFIX = '  /* ==='
SIG_BODY_START_HINT = '8. MODAL'
SIG_BODY_END = '  }'  # showDataModal 닫힘
SIG_OUTER_IIFE_CLOSE = '})();'

# index.html 삽입
HTML_INSERT_AFTER = 'sqm-util-toast.js'
HTML_NEW_TAG = '    <script src="js/sqm-util-modal.js?v=20260523a"></script>\n'

IDEMPOTENCY_MARKER = '__SQM_UTIL_MODAL_INSTALLED__'


def log(msg, level='INFO'):
    icons = {'INFO': 'ℹ', 'OK': '✓', 'WARN': '⚠', 'ERR': '✗', 'DRY': '🧪'}
    print(f"{icons.get(level, '·')} [{level}] {msg}")


def read_lines(path):
    with path.open('r', encoding='utf-8', newline='') as f:
        return f.readlines()


def write_lines(path, lines):
    with path.open('w', encoding='utf-8', newline='') as f:
        f.writelines(lines)


def write_text(path, text):
    with path.open('w', encoding='utf-8', newline='') as f:
        f.write(text)


def backup(path, slice_id):
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    bak = path.with_suffix(path.suffix + f'.bak_{slice_id}_{ts}')
    shutil.copy2(path, bak)
    return bak


def already_extracted():
    return MODAL_FILE.exists()


def verify_inline_bounds(lines):
    errors = []
    if len(lines) < 4500:
        errors.append(f"줄수 너무 적음: {len(lines)}")
        return errors

    lstart = lines[BODY_START - 1].rstrip()
    if not lstart.startswith(SIG_BODY_START_PREFIX):
        errors.append(f"line {BODY_START} 시작 시그니처 불일치: got {lstart[:60]!r}")

    block = ''.join(lines[BODY_START - 1:BODY_START + 4])
    if SIG_BODY_START_HINT not in block:
        errors.append(f"line {BODY_START}+4 영역에 '{SIG_BODY_START_HINT}' 힌트 없음")

    lend = lines[BODY_END - 1].rstrip()
    if lend != SIG_BODY_END.rstrip():
        errors.append(f"line {BODY_END} 끝 시그니처 불일치: got {lend!r}")

    last = lines[-1].rstrip()
    if last != SIG_OUTER_IIFE_CLOSE:
        errors.append(f"마지막 줄 outer IIFE 닫힘 손상: got {last!r}")

    # 잔재 라인 2개 검증
    for sig in [RESIDUE_LINE_1, RESIDUE_LINE_2]:
        found = any(line.rstrip() == sig.rstrip() for line in lines)
        if not found:
            errors.append(f"잔재 marker 못 찾음: {sig!r}")

    return errors


def find_residue_indices(lines):
    """잔재 라인 2개 (line 4812, 4813)의 정확한 인덱스 찾기.

    Returns: (idx1, idx2) 0-based — 반드시 idx2 = idx1 + 1 이어야 함 (인접 검증).
    """
    idx1 = idx2 = None
    for i, line in enumerate(lines):
        l = line.rstrip()
        if l == RESIDUE_LINE_1.rstrip():
            if idx1 is not None:
                raise RuntimeError(f"잔재1이 여러 곳에 있음: {RESIDUE_LINE_1!r}")
            idx1 = i
        if l == RESIDUE_LINE_2.rstrip():
            if idx2 is not None:
                raise RuntimeError(f"잔재2가 여러 곳에 있음: {RESIDUE_LINE_2!r}")
            idx2 = i

    if idx1 is None or idx2 is None:
        raise RuntimeError("잔재 라인 못 찾음")
    if idx2 != idx1 + 1:
        raise RuntimeError(f"잔재 라인이 인접하지 않음: idx1={idx1}, idx2={idx2}")

    return idx1, idx2


def build_modal_module(extracted_lines):
    today = datetime.now().strftime('%Y-%m-%d')
    header = (
        f'/* =======================================================================\n'
        f'   SQM Inventory - sqm-util-modal.js — 모달 인프라 (드래그/리사이즈)\n'
        f'   Extracted from sqm-inline.js (Phase B-S8) — {today}\n'
        f'   Source: sqm-inline.js line 2083-2217 (135줄) + line 4812-4813 잔재\n'
        f'\n'
        f'   주요 함수:\n'
        f'   - _bringToFront, _makeDraggableResizable: 모달 z-index/드래그/리사이즈\n'
        f'   - ensureModal, showDataModal: 모달 표시\n'
        f'   - _sqmSetModalTitleBar 등: 타이틀바 동기화\n'
        f'\n'
        f'   외부 공유: window._sqmZ (다른 JS 파일도 사용)\n'
        f'   외부 노출: showDataModal/_makeDraggableResizable/_bringToFront/_sqmSetModalTitleBar\n'
        f'   ======================================================================= */\n'
        f'(function () {{\n'
        f"  'use strict';\n"
        f'  if (window.{IDEMPOTENCY_MARKER}) return;\n'
        f'  window.{IDEMPOTENCY_MARKER} = true;\n'
        f'\n'
    )
    body = ''.join(extracted_lines)
    footer = (
        '\n'
        '  // 글로벌 노출 (sqm-inline.js 기존 호출 호환 + 다른 파일 의존성)\n'
        '  window.showDataModal = showDataModal;\n'
        '  window._makeDraggableResizable = _makeDraggableResizable;\n'
        '})();\n'
    )
    return header + body + footer


def update_index_html(html_lines):
    for line in html_lines:
        if 'sqm-util-modal.js' in line:
            return html_lines, False, None

    for i, line in enumerate(html_lines):
        if HTML_INSERT_AFTER in line:
            new_lines = html_lines[:i + 1] + [HTML_NEW_TAG] + html_lines[i + 1:]
            return new_lines, True, i + 2

    raise RuntimeError(f"index.html에서 '{HTML_INSERT_AFTER}' 못 찾음")


def rollback():
    paths = [INLINE, HTML]
    candidates = []
    for p in paths:
        baks = sorted(p.parent.glob(f'{p.name}.bak_{SLICE_ID}_*'), reverse=True)
        if baks:
            candidates.append((p, baks[0]))

    if not candidates:
        log(f'{SLICE_ID} 백업 못 찾음', 'ERR')
        return False

    for target, bak in candidates:
        shutil.copy2(bak, target)
        log(f'복원: {target.name} ← {bak.name}', 'OK')

    if MODAL_FILE.exists():
        MODAL_FILE.unlink()
        log(f'생성 파일 삭제: {MODAL_FILE.name}', 'OK')

    return True


def main():
    parser = argparse.ArgumentParser(description='S8: 모달 인프라 추출')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--rollback', action='store_true')
    args = parser.parse_args()

    if args.rollback:
        log(f'=== Rollback {SLICE_ID} ===')
        return 0 if rollback() else 1

    mode = 'DRY-RUN' if args.dry_run else 'EXECUTE'
    log(f'=== S8 모달 인프라 추출 ({mode}) ===')

    if already_extracted():
        log('이미 추출됨 (sqm-util-modal.js 존재). 무동작.', 'WARN')
        return 0

    inline_lines = read_lines(INLINE)
    html_lines = read_lines(HTML)
    log(f'입력 sqm-inline.js: {len(inline_lines)} 줄')
    log(f'입력 index.html: {len(html_lines)} 줄')

    errors = verify_inline_bounds(inline_lines)
    if errors:
        log('사전 검증 실패:', 'ERR')
        for e in errors:
            log(f'  - {e}', 'ERR')
        return 1
    log(f'사전 검증 통과 (line {BODY_START} 섹션, line {BODY_END} 끝, 잔재 라인 2개 발견)', 'OK')

    # 본문 추출
    extracted = inline_lines[BODY_START - 1:BODY_END]
    modal_module = build_modal_module(extracted)
    modal_lines = modal_module.count('\n')
    log(f'추출 줄수: {len(extracted)}, 새 모듈: {modal_lines}줄', 'OK')

    # 새 inline = 본문 제거 + 잔재 라인 2개 제거
    # 본문부터 제거 (위쪽)
    after_body_removed = inline_lines[:BODY_START - 1] + inline_lines[BODY_END:]

    # 잔재 라인 찾기 (인접 검증) + 제거
    residue_idx1, residue_idx2 = find_residue_indices(after_body_removed)
    new_inline_lines = (
        after_body_removed[:residue_idx1]
        + after_body_removed[residue_idx2 + 1:]
    )

    expected = len(inline_lines) - BODY_COUNT - 2  # 본문 + 잔재 2줄
    if len(new_inline_lines) != expected:
        log(f'줄수 오류: 예상 {expected}, 실측 {len(new_inline_lines)}', 'ERR')
        return 1
    if new_inline_lines[-1].rstrip() != SIG_OUTER_IIFE_CLOSE:
        log('사후 outer IIFE 손상', 'ERR')
        return 1
    log(f'사후 검증 통과 ({len(inline_lines)} → {expected}, -{BODY_COUNT}-2)', 'OK')

    new_html_lines, html_inserted, html_line_no = update_index_html(html_lines)
    if html_inserted:
        log(f'index.html line {html_line_no} 삽입 예정', 'OK')

    if args.dry_run:
        log('=== DRY-RUN ===', 'DRY')
        log(f'  sqm-inline.js: {len(inline_lines)} → {expected}', 'DRY')
        log(f'  index.html: {len(html_lines)} → {len(new_html_lines)}', 'DRY')
        log(f'  생성: sqm-util-modal.js ({modal_lines} 줄)', 'DRY')
        return 0

    bak_inline = backup(INLINE, SLICE_ID)
    log(f'백업: {bak_inline.name}', 'OK')
    bak_html = backup(HTML, SLICE_ID)
    log(f'백업: {bak_html.name}', 'OK')

    write_text(MODAL_FILE, modal_module)
    log(f'생성: {MODAL_FILE.name} ({modal_lines}줄)', 'OK')
    write_lines(INLINE, new_inline_lines)
    log(f'수정: {INLINE.name} ({len(new_inline_lines)}줄)', 'OK')
    write_lines(HTML, new_html_lines)
    log(f'수정: {HTML.name} ({len(new_html_lines)}줄)', 'OK')

    final = read_lines(INLINE)
    if final[-1].rstrip() != SIG_OUTER_IIFE_CLOSE:
        log('최종 outer IIFE 손상', 'ERR')
        return 1
    log('최종 검증 통과', 'OK')
    log('=== 완료 ===')
    return 0


if __name__ == '__main__':
    sys.exit(main())
