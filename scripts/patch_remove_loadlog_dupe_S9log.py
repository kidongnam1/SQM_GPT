# -*- coding: utf-8 -*-
"""
Phase B - Slice S9-log: loadLogPage 중복 제거 (시범)

발견: sqm-inline.js의 loadLogPage는 dead duplicate
- sqm-logistics.js:695에 정의 + line 917에 window 노출
- sqm-inline.js는 정의만 있고 window 노출 없음
- sqm-core.js renderPage가 window.loadLogPage 호출 → sqm-logistics.js 신버전 사용
- sqm-logistics.js 버전이 더 완전 (colgroup, getCurrentRoute, 더 자세한 styling)

대상: sqm-inline.js (현 line 1859-1905, 47줄)

사용:
    python scripts/patch_remove_loadlog_dupe_S9log.py --dry-run
    python scripts/patch_remove_loadlog_dupe_S9log.py
    python scripts/patch_remove_loadlog_dupe_S9log.py --rollback
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
LOGISTICS = ROOT / 'frontend' / 'js' / 'sqm-logistics.js'
SLICE_ID = 'S9log'

START_LINE = 1859
END_LINE = 1905
EXPECTED_DELETE_COUNT = END_LINE - START_LINE + 1  # 47줄

SIG_START_PREFIX = '  /* ==='
SIG_START_HINT = '7g. PAGE: Log'
SIG_END_LINE = '  }'
SIG_OUTER_IIFE_CLOSE = '})();'

LOGISTICS_REQUIRED = [
    '  function loadLogPage() {',
    '  window.loadLogPage       = loadLogPage;',
]

IDEMPOTENCY_MARKER = '7g. PAGE: Log'


def log(msg, level='INFO'):
    icons = {'INFO': 'ℹ', 'OK': '✓', 'WARN': '⚠', 'ERR': '✗', 'DRY': '🧪'}
    print(f"{icons.get(level, '·')} [{level}] {msg}")


def read_lines(path):
    with path.open('r', encoding='utf-8', newline='') as f:
        return f.readlines()


def write_lines(path, lines):
    with path.open('w', encoding='utf-8', newline='') as f:
        f.writelines(lines)


def backup(path, slice_id):
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    bak = path.with_suffix(path.suffix + f'.bak_{slice_id}_{ts}')
    shutil.copy2(path, bak)
    return bak


def verify_safety_net():
    if not LOGISTICS.exists():
        return [f"안전망 파일 없음: {LOGISTICS}"]
    text = LOGISTICS.read_text(encoding='utf-8')
    errors = []
    for sig in LOGISTICS_REQUIRED:
        if sig not in text:
            errors.append(f"sqm-logistics.js에 시그니처 없음: {sig!r}")
    return errors


def verify_inline_bounds(lines):
    errors = []
    if len(lines) < 4000:
        errors.append(f"줄수 너무 적음: {len(lines)}")
        return errors

    lstart = lines[START_LINE - 1].rstrip()
    if not lstart.startswith(SIG_START_PREFIX):
        errors.append(f"line {START_LINE} 시작 시그니처 불일치: got {lstart[:60]!r}")

    block = ''.join(lines[START_LINE - 1:START_LINE + 3])
    if SIG_START_HINT not in block:
        errors.append(f"line {START_LINE}+3에 '{SIG_START_HINT}' 힌트 없음")

    lend = lines[END_LINE - 1].rstrip()
    if lend != SIG_END_LINE.rstrip():
        errors.append(f"line {END_LINE} 끝 시그니처 불일치: got {lend!r}")

    last = lines[-1].rstrip()
    if last != SIG_OUTER_IIFE_CLOSE:
        errors.append(f"마지막 줄 outer IIFE 닫힘 손상: got {last!r}")

    # sqm-inline.js는 window.loadLogPage를 노출하지 않아야 (dead duplicate)
    for line in lines:
        if 'window.loadLogPage' in line:
            errors.append("sqm-inline.js가 window.loadLogPage 노출 중 — dead duplicate 가정 무효")
            break

    return errors


def already_removed(lines):
    for line in lines[START_LINE - 5:START_LINE + 5]:
        if IDEMPOTENCY_MARKER in line:
            return False
    return True


def rollback():
    baks = sorted(INLINE.parent.glob(f'{INLINE.name}.bak_{SLICE_ID}_*'), reverse=True)
    if not baks:
        log(f'{SLICE_ID} 백업 못 찾음', 'ERR')
        return False
    shutil.copy2(baks[0], INLINE)
    log(f'복원: {INLINE.name} ← {baks[0].name}', 'OK')
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--rollback', action='store_true')
    args = parser.parse_args()

    if args.rollback:
        log(f'=== Rollback {SLICE_ID} ===')
        return 0 if rollback() else 1

    mode = 'DRY-RUN' if args.dry_run else 'EXECUTE'
    log(f'=== S9-log loadLogPage 중복 제거 ({mode}) ===')

    sn_errors = verify_safety_net()
    if sn_errors:
        for e in sn_errors:
            log(f'  - {e}', 'ERR')
        return 1
    log('sqm-logistics.js 안전망 통과', 'OK')

    inline_lines = read_lines(INLINE)
    log(f'입력 sqm-inline.js: {len(inline_lines)} 줄')

    if already_removed(inline_lines):
        log('이미 제거됨', 'WARN')
        return 0

    errors = verify_inline_bounds(inline_lines)
    if errors:
        for e in errors:
            log(f'  - {e}', 'ERR')
        return 1
    log(f'사전 검증 통과 (line {START_LINE}-{END_LINE}, dead duplicate 확인)', 'OK')

    new_lines = inline_lines[:START_LINE - 1] + inline_lines[END_LINE:]
    expected = len(inline_lines) - EXPECTED_DELETE_COUNT
    if len(new_lines) != expected or new_lines[-1].rstrip() != SIG_OUTER_IIFE_CLOSE:
        log('사후 검증 실패', 'ERR')
        return 1
    log(f'사후 검증 통과 ({len(inline_lines)} → {expected})', 'OK')

    if args.dry_run:
        log(f'DRY-RUN: {len(inline_lines)} → {expected}, 삭제 {EXPECTED_DELETE_COUNT}줄', 'DRY')
        return 0

    bak = backup(INLINE, SLICE_ID)
    log(f'백업: {bak.name}', 'OK')

    write_lines(INLINE, new_lines)
    log(f'수정: {INLINE.name} ({len(new_lines)}줄)', 'OK')

    final = read_lines(INLINE)
    if final[-1].rstrip() != SIG_OUTER_IIFE_CLOSE:
        log('최종 outer IIFE 손상', 'ERR')
        return 1
    log('=== 완료 ===')
    return 0


if __name__ == '__main__':
    sys.exit(main())
