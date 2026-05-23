# -*- coding: utf-8 -*-
"""
Phase B - Slice S6a: showToast + ensureToastContainer 추출

sqm-inline.js 진짜 소유 (sqm-core.js에 없음 → 새 모듈 추출 필요)

대상: sqm-inline.js (현 line 247-273, 27줄)
- function ensureToastContainer (line 247-256)
- var TOAST_ICONS (line 258)
- function showToast (line 260-272)
- window.showToast = showToast; (line 273)

호출 횟수:
- sqm-inline.js 내부: 143회 (escapeHtml 다음으로 많음)
- 외부 파일: main.js, pages/*.js, sqm-allocation.js, sqm-aux-modals.js 등 10+

전략:
- 새 모듈 frontend/js/sqm-util-toast.js 생성
- window.showToast 동일 노출 (호환 유지)
- sqm-inline.js 내부 호출은 JavaScript 스코프 체인으로 window.* 폴백

내부 의존:
- escapeHtml — S2에서 sqm-util-escape.js로 추출되어 window.escapeHtml 노출 중
- 새 모듈에서 `escapeHtml(message)` 그대로 호출 → window 폴백

index.html 로딩 순서:
- sqm-util-escape.js (line 407) 다음에 sqm-util-toast.js 삽입
- sqm-util-dbg.js (line 409) 직후, sqm-inline.js (line 410) 앞

사용:
    python scripts/patch_split_toast_S6a.py --dry-run
    python scripts/patch_split_toast_S6a.py
    python scripts/patch_split_toast_S6a.py --rollback
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
TOAST = ROOT / 'frontend' / 'js' / 'sqm-util-toast.js'
HTML = ROOT / 'frontend' / 'index.html'
SLICE_ID = 'S6a'

START_LINE = 247
END_LINE = 273
EXTRACTED_COUNT = END_LINE - START_LINE + 1  # 27줄

# 검증 시그니처
SIG_START_PREFIX = '  function ensureToastContainer'
SIG_END_LINE = '  window.showToast = showToast;'
SIG_OUTER_IIFE_CLOSE = '})();'

# index.html 삽입 위치 (sqm-util-dbg.js 다음, sqm-inline.js 앞)
HTML_INSERT_AFTER = 'sqm-util-dbg.js'
HTML_NEW_TAG = '    <script src="js/sqm-util-toast.js?v=20260523a"></script>\n'

IDEMPOTENCY_MARKER = '__SQM_UTIL_TOAST_INSTALLED__'


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


def verify_inline_bounds(lines):
    errors = []
    if len(lines) < 5000:
        errors.append(f"줄수 너무 적음: {len(lines)}")
        return errors

    lstart = lines[START_LINE - 1].rstrip()
    if not lstart.startswith(SIG_START_PREFIX):
        errors.append(f"line {START_LINE} 시작 시그니처 불일치: got {lstart[:60]!r}")

    lend = lines[END_LINE - 1].rstrip()
    if lend != SIG_END_LINE.rstrip():
        errors.append(f"line {END_LINE} 끝 시그니처 불일치: got {lend!r}")

    last = lines[-1].rstrip()
    if last != SIG_OUTER_IIFE_CLOSE:
        errors.append(f"마지막 줄 outer IIFE 닫힘 손상: got {last!r}")

    return errors


def already_extracted():
    return TOAST.exists()


def build_toast_module(extracted_lines):
    today = datetime.now().strftime('%Y-%m-%d')
    header = (
        f'/* =======================================================================\n'
        f'   SQM Inventory - sqm-util-toast.js — 토스트 알림 시스템\n'
        f'   Extracted from sqm-inline.js (Phase B-S6a) — {today}\n'
        f'   Source: sqm-inline.js line 247-273 (ensureToastContainer + showToast)\n'
        f'\n'
        f'   외부 의존: window.escapeHtml (sqm-util-escape.js, S2)\n'
        f'   외부 노출: window.showToast (다른 10+ 파일에서 사용)\n'
        f'   ======================================================================= */\n'
        f'(function () {{\n'
        f"  'use strict';\n"
        f'  if (window.{IDEMPOTENCY_MARKER}) return;\n'
        f'  window.{IDEMPOTENCY_MARKER} = true;\n'
        f'\n'
    )
    body = ''.join(extracted_lines)
    footer = '})();\n'
    return header + body + footer


def update_index_html(html_lines):
    """sqm-util-dbg.js 줄 다음에 sqm-util-toast.js 줄 삽입."""
    # 이미 있는지
    for line in html_lines:
        if 'sqm-util-toast.js' in line:
            return html_lines, False, None

    # sqm-util-dbg.js 찾기
    for i, line in enumerate(html_lines):
        if HTML_INSERT_AFTER in line:
            new_lines = html_lines[:i + 1] + [HTML_NEW_TAG] + html_lines[i + 1:]
            return new_lines, True, i + 2  # 1-based, 삽입된 줄 번호

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

    if TOAST.exists():
        TOAST.unlink()
        log(f'생성 파일 삭제: {TOAST.name}', 'OK')

    return True


def main():
    parser = argparse.ArgumentParser(description='S6a: showToast 추출')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--rollback', action='store_true')
    args = parser.parse_args()

    if args.rollback:
        log(f'=== Rollback {SLICE_ID} ===')
        return 0 if rollback() else 1

    mode = 'DRY-RUN' if args.dry_run else 'EXECUTE'
    log(f'=== S6a showToast 추출 ({mode}) ===')

    if already_extracted():
        log('이미 추출됨 (sqm-util-toast.js 존재). 무동작.', 'WARN')
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
    log(f'사전 검증 통과 (line {START_LINE} ensureToastContainer, line {END_LINE} window.showToast)', 'OK')

    # 추출 + 새 파일 생성
    extracted = inline_lines[START_LINE - 1:END_LINE]
    new_module = build_toast_module(extracted)
    new_module_lines = new_module.count('\n')
    log(f'추출 줄수: {len(extracted)}, 새 모듈 줄수: {new_module_lines}', 'OK')

    # sqm-inline.js에서 제거
    new_inline_lines = inline_lines[:START_LINE - 1] + inline_lines[END_LINE:]
    expected = len(inline_lines) - EXTRACTED_COUNT
    if len(new_inline_lines) != expected:
        log(f'줄수 계산 오류: 예상 {expected}, 실측 {len(new_inline_lines)}', 'ERR')
        return 1
    if new_inline_lines[-1].rstrip() != SIG_OUTER_IIFE_CLOSE:
        log(f'사후 outer IIFE 손상', 'ERR')
        return 1
    log(f'사후 검증 통과 (sqm-inline.js {len(inline_lines)} → {expected})', 'OK')

    new_html_lines, html_inserted, html_line_no = update_index_html(html_lines)
    if html_inserted:
        log(f'index.html에 line {html_line_no} 삽입 예정 (sqm-util-dbg.js 다음)', 'OK')
    else:
        log('index.html에 이미 sqm-util-toast.js 태그 있음', 'WARN')

    if args.dry_run:
        log('=== DRY-RUN 결과 ===', 'DRY')
        log(f'  sqm-inline.js: {len(inline_lines)} → {expected}', 'DRY')
        log(f'  index.html: {len(html_lines)} → {len(new_html_lines)}', 'DRY')
        log(f'  생성: sqm-util-toast.js ({new_module_lines} 줄)', 'DRY')
        return 0

    log('=== 백업 ===')
    bak_inline = backup(INLINE, SLICE_ID)
    log(f'  {bak_inline.name}', 'OK')
    bak_html = backup(HTML, SLICE_ID)
    log(f'  {bak_html.name}', 'OK')

    log('=== 파일 쓰기 ===')
    write_text(TOAST, new_module)
    log(f'  새 파일: {TOAST.name} ({new_module_lines} 줄)', 'OK')
    write_lines(INLINE, new_inline_lines)
    log(f'  수정: {INLINE.name} ({len(new_inline_lines)} 줄)', 'OK')
    write_lines(HTML, new_html_lines)
    log(f'  수정: {HTML.name} ({len(new_html_lines)} 줄)', 'OK')

    final = read_lines(INLINE)
    if final[-1].rstrip() != SIG_OUTER_IIFE_CLOSE:
        log('최종 outer IIFE 손상', 'ERR')
        return 1
    log('최종 검증 통과', 'OK')
    log('=== 완료 ===')
    return 0


if __name__ == '__main__':
    sys.exit(main())
