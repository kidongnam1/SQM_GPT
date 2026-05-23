# -*- coding: utf-8 -*-
"""
Phase B - Slice S1: Tooltip 시스템 추출

목표: frontend/js/sqm-inline.js (5,635줄)에서 line 11-142 (Tooltip IIFE)를
      별도 파일 frontend/js/sqm-tooltip.js로 분리.

설계 문서: docs/refactor/sqm-inline-split-plan.md §2

핵심 안전장치 (Rule 5 + 2026-05-15 사고 대비):
1. 줄번호 + 내용 이중 검증 (line 11 시작 마커, line 142 끝 마커)
2. outer IIFE 닫힘 (line 5635 `})();`) 수정 전후 확인
3. 타임스탬프 백업 (3개 파일: inline.js, index.html, 새 tooltip.js는 없음)
4. Idempotent (이미 추출됐으면 무동작)
5. --dry-run 지원 (실제 쓰기 없이 시뮬레이션)

사용:
    python scripts/patch_split_tooltip_S1.py --dry-run    # 시뮬레이션
    python scripts/patch_split_tooltip_S1.py             # 실제 적용
    python scripts/patch_split_tooltip_S1.py --rollback  # 백업에서 복원
"""

import argparse
import sys
import shutil
from datetime import datetime
from pathlib import Path

# Windows cp949 콘솔에서 유니코드 출력 보장
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

ROOT = Path(__file__).resolve().parent.parent
INLINE = ROOT / 'frontend' / 'js' / 'sqm-inline.js'
TOOLTIP = ROOT / 'frontend' / 'js' / 'sqm-tooltip.js'
HTML = ROOT / 'frontend' / 'index.html'

# 추출 경계 (1-based)
TOOLTIP_START_LINE = 11
TOOLTIP_END_LINE = 142
TOOLTIP_LINES_COUNT = TOOLTIP_END_LINE - TOOLTIP_START_LINE + 1  # 132줄

# 검증용 시그니처
SIG_LINE_11_PREFIX = '  /* ===='
SIG_LINE_142_CONTENT = '  })();'   # inner IIFE close
SIG_OUTER_IIFE_CLOSE = '})();'      # outer IIFE close (no leading spaces)
SIG_TOOLTIP_HEADER_CONTENT = 'CUSTOM TOOLTIP SYSTEM'  # line 12 안에 있어야 함

# index.html 삽입 위치 마커
HTML_INSERT_BEFORE = '<script src="js/sqm-inline.js'
HTML_NEW_SCRIPT_TAG = '    <script src="js/sqm-tooltip.js?v=20260523a"></script>\n'

# 이미 추출됐는지 감지
IDEMPOTENCY_MARKER = '__SQM_TOOLTIP_INSTALLED__'


def log(msg, level='INFO'):
    icons = {'INFO': 'ℹ', 'OK': '✓', 'WARN': '⚠', 'ERR': '✗', 'DRY': '🧪'}
    print(f"{icons.get(level, '·')} [{level}] {msg}")


def read_lines(path: Path):
    """파일을 줄 리스트로 읽음 (newline 보존). UTF-8."""
    with path.open('r', encoding='utf-8', newline='') as f:
        return f.readlines()


def write_lines(path: Path, lines):
    """줄 리스트를 파일에 씀."""
    with path.open('w', encoding='utf-8', newline='') as f:
        f.writelines(lines)


def write_text(path: Path, text: str):
    """텍스트를 파일에 씀."""
    with path.open('w', encoding='utf-8', newline='') as f:
        f.write(text)


def backup(path: Path, slice_id: str) -> Path:
    """타임스탬프 백업 생성. 반환: 백업 경로."""
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    bak = path.with_suffix(path.suffix + f'.bak_{slice_id}_{ts}')
    shutil.copy2(path, bak)
    return bak


def precheck_inline(lines):
    """추출 전 sqm-inline.js 무결성 검증.

    Returns: (ok: bool, errors: list[str])
    """
    errors = []

    if len(lines) < 5000:
        errors.append(f'줄수 너무 적음: {len(lines)} (예상 5500+)')

    # line 11 (0-indexed 10) 시작 검증
    if not lines[TOOLTIP_START_LINE - 1].startswith(SIG_LINE_11_PREFIX):
        errors.append(
            f'line {TOOLTIP_START_LINE} 시작 시그니처 불일치: '
            f"got {lines[TOOLTIP_START_LINE - 1][:30]!r}"
        )

    # line 12 (Tooltip 헤더) 검증
    if SIG_TOOLTIP_HEADER_CONTENT not in lines[TOOLTIP_START_LINE]:
        errors.append(
            f'line {TOOLTIP_START_LINE + 1} 에 "{SIG_TOOLTIP_HEADER_CONTENT}" 없음'
        )

    # line 142 (0-indexed 141) 끝 검증
    line_142 = lines[TOOLTIP_END_LINE - 1].rstrip()
    if line_142 != SIG_LINE_142_CONTENT:
        errors.append(
            f'line {TOOLTIP_END_LINE} 끝 시그니처 불일치: got {line_142!r}'
        )

    # outer IIFE 닫힘 검증 (마지막 줄 또는 그 근처)
    last_line = lines[-1].rstrip()
    if last_line != SIG_OUTER_IIFE_CLOSE:
        errors.append(
            f'마지막 줄 outer IIFE 닫힘 시그니처 불일치: got {last_line!r}'
        )

    return len(errors) == 0, errors


def already_extracted(lines):
    """이미 추출됐는지 확인 (idempotency)."""
    if TOOLTIP.exists():
        return True
    # sqm-inline.js에서 IDEMPOTENCY_MARKER가 line 11-150 영역에 있는지
    head = ''.join(lines[:200])
    return IDEMPOTENCY_MARKER in head and 'tooltip' in head.lower()


def build_tooltip_file(extracted_lines):
    """sqm-tooltip.js 본문 생성.

    Args:
        extracted_lines: line 11-142 (132줄) 원본 그대로

    Returns:
        새 파일 전체 텍스트
    """
    header = (
        '/* =======================================================================\n'
        '   SQM Inventory - sqm-tooltip.js\n'
        '   Extracted from sqm-inline.js (Phase B-S1) — 2026-05-23\n'
        '   Original: 2026-04-21 Ruby\n'
        '   Source: sqm-inline.js line 11-142 (Custom Dark Tooltip System)\n'
        '   ======================================================================= */\n'
        '(function () {\n'
        "  'use strict';\n"
        f'  if (window.{IDEMPOTENCY_MARKER}) return;\n'
        f'  window.{IDEMPOTENCY_MARKER} = true;\n'
        '\n'
    )
    # 추출 원본 (그대로, 들여쓰기 유지)
    body = ''.join(extracted_lines)
    footer = '})();\n'
    return header + body + footer


def update_index_html(html_lines, dry_run=False):
    """index.html 에 sqm-tooltip.js 스크립트 태그 삽입.

    sqm-inline.js 줄 바로 앞에 삽입.

    Returns:
        (modified_lines: list, inserted: bool, line_no: int|None)
    """
    # 이미 있는지 확인
    for i, line in enumerate(html_lines):
        if 'sqm-tooltip.js' in line:
            return html_lines, False, i + 1  # 이미 있음

    # sqm-inline.js 줄 찾기
    for i, line in enumerate(html_lines):
        if HTML_INSERT_BEFORE in line:
            new_lines = html_lines[:i] + [HTML_NEW_SCRIPT_TAG] + html_lines[i:]
            return new_lines, True, i + 1

    raise RuntimeError(f"index.html에서 '{HTML_INSERT_BEFORE}' 줄을 못 찾음")


def postcheck_inline(lines_after, original_line_count):
    """추출 후 sqm-inline.js 무결성 검증."""
    errors = []
    expected = original_line_count - TOOLTIP_LINES_COUNT
    if len(lines_after) != expected:
        errors.append(
            f'줄수 불일치: 예상 {expected}, 실측 {len(lines_after)}'
        )

    last_line = lines_after[-1].rstrip()
    if last_line != SIG_OUTER_IIFE_CLOSE:
        errors.append(
            f'outer IIFE 닫힘 손상: 마지막 줄 = {last_line!r}'
        )

    # line 11 부근에 Tooltip 잔해가 없어야 함
    head = ''.join(lines_after[:30])
    if SIG_TOOLTIP_HEADER_CONTENT in head:
        errors.append('line 30 이내에 Tooltip 헤더 잔해 발견')

    return len(errors) == 0, errors


def rollback():
    """가장 최근 S1 백업으로부터 복원."""
    paths = [INLINE, HTML, TOOLTIP]
    candidates = []
    for p in paths[:2]:  # tooltip은 생성 파일이므로 백업 없을 수 있음
        baks = sorted(p.parent.glob(f'{p.name}.bak_S1_*'), reverse=True)
        if baks:
            candidates.append((p, baks[0]))

    if not candidates:
        log('S1 백업 파일을 찾지 못함', 'ERR')
        return False

    for target, bak in candidates:
        shutil.copy2(bak, target)
        log(f'복원: {target.name} ← {bak.name}', 'OK')

    if TOOLTIP.exists():
        TOOLTIP.unlink()
        log(f'생성 파일 삭제: {TOOLTIP.name}', 'OK')

    return True


def main():
    parser = argparse.ArgumentParser(description='S1: Tooltip 추출')
    parser.add_argument('--dry-run', action='store_true',
                        help='시뮬레이션만 (파일 변경 없음)')
    parser.add_argument('--rollback', action='store_true',
                        help='최근 S1 백업으로부터 복원')
    args = parser.parse_args()

    if args.rollback:
        log('=== Rollback 모드 ===')
        ok = rollback()
        return 0 if ok else 1

    mode = 'DRY-RUN' if args.dry_run else 'EXECUTE'
    log(f'=== S1 Tooltip 추출 ({mode}) ===')

    # 1. 입력 검증
    if not INLINE.exists():
        log(f'파일 없음: {INLINE}', 'ERR')
        return 1
    if not HTML.exists():
        log(f'파일 없음: {HTML}', 'ERR')
        return 1

    inline_lines = read_lines(INLINE)
    html_lines = read_lines(HTML)
    log(f'입력 sqm-inline.js: {len(inline_lines)} 줄')
    log(f'입력 index.html: {len(html_lines)} 줄')

    # 2. Idempotency
    if already_extracted(inline_lines):
        log('이미 추출됨 (sqm-tooltip.js 존재 또는 마커 발견)', 'WARN')
        log('아무것도 하지 않음. --rollback 으로 복원 가능.', 'INFO')
        return 0

    # 3. 사전 검증
    ok, errs = precheck_inline(inline_lines)
    if not ok:
        log('사전 검증 실패:', 'ERR')
        for e in errs:
            log(f'  - {e}', 'ERR')
        return 1
    log('사전 검증 통과 (line 11 시작, line 142 끝, line 5635 outer IIFE 닫힘)', 'OK')

    # 4. 추출
    # 0-indexed: line 11 → idx 10, line 142 → idx 141 (포함)
    extracted = inline_lines[TOOLTIP_START_LINE - 1:TOOLTIP_END_LINE]
    assert len(extracted) == TOOLTIP_LINES_COUNT, \
        f'추출 줄수 불일치: {len(extracted)} != {TOOLTIP_LINES_COUNT}'
    log(f'추출 줄수: {len(extracted)} (line {TOOLTIP_START_LINE}-{TOOLTIP_END_LINE})', 'OK')

    # 5. 새 파일 본문 생성
    tooltip_content = build_tooltip_file(extracted)
    tooltip_line_count = tooltip_content.count('\n')
    log(f'sqm-tooltip.js 예상 줄수: {tooltip_line_count}', 'INFO')

    # 6. sqm-inline.js 수정안
    new_inline_lines = (
        inline_lines[:TOOLTIP_START_LINE - 1]
        + inline_lines[TOOLTIP_END_LINE:]
    )

    # 7. 사후 검증 (수정안 기준)
    ok, errs = postcheck_inline(new_inline_lines, len(inline_lines))
    if not ok:
        log('사후 검증 실패:', 'ERR')
        for e in errs:
            log(f'  - {e}', 'ERR')
        return 1
    log(f'사후 검증 통과 (예상 줄수 {len(new_inline_lines)}, outer IIFE 닫힘 유지)', 'OK')

    # 8. index.html 수정안
    new_html_lines, html_inserted, insert_line = update_index_html(
        html_lines, dry_run=args.dry_run
    )
    if html_inserted:
        log(f'index.html line {insert_line} 앞에 <script src="js/sqm-tooltip.js"> 삽입 예정', 'OK')
    else:
        log(f'index.html에 이미 sqm-tooltip.js 태그 존재 (line {insert_line})', 'WARN')

    # 9. DRY-RUN 종료
    if args.dry_run:
        log('=== DRY-RUN 결과 (실제 변경 없음) ===', 'DRY')
        log(f'  sqm-inline.js: {len(inline_lines)} → {len(new_inline_lines)} 줄', 'DRY')
        log(f'  sqm-tooltip.js: 생성 예정 ({tooltip_line_count} 줄)', 'DRY')
        log(f'  index.html: {len(html_lines)} → {len(new_html_lines)} 줄', 'DRY')
        log('OK 실제 적용은 --dry-run 없이 실행', 'DRY')
        return 0

    # 10. 실제 적용
    log('=== 백업 생성 ===')
    bak_inline = backup(INLINE, 'S1')
    log(f'  {bak_inline.name}', 'OK')
    bak_html = backup(HTML, 'S1')
    log(f'  {bak_html.name}', 'OK')

    log('=== 파일 쓰기 ===')
    write_text(TOOLTIP, tooltip_content)
    log(f'  새 파일: {TOOLTIP.name} ({tooltip_line_count} 줄)', 'OK')
    write_lines(INLINE, new_inline_lines)
    log(f'  수정: {INLINE.name} ({len(new_inline_lines)} 줄)', 'OK')
    write_lines(HTML, new_html_lines)
    log(f'  수정: {HTML.name} ({len(new_html_lines)} 줄)', 'OK')

    # 11. 최종 사후 검증 (디스크에서 재로딩)
    log('=== 최종 검증 ===')
    final_inline = read_lines(INLINE)
    final_last = final_inline[-1].rstrip()
    if final_last == SIG_OUTER_IIFE_CLOSE:
        log(f'  outer IIFE 닫힘 유지: 마지막 줄 = {final_last!r}', 'OK')
    else:
        log(f'  outer IIFE 닫힘 손상: 마지막 줄 = {final_last!r}', 'ERR')
        log('  → 즉시 --rollback 실행 권장', 'ERR')
        return 1

    log('=== 완료 ===')
    log('다음 단계: node --check, 앱 실행, Playwright 회귀', 'INFO')
    return 0


if __name__ == '__main__':
    sys.exit(main())
