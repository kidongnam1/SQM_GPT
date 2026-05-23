# -*- coding: utf-8 -*-
"""
Phase B - Slice S6b: apiCall/apiGet/apiPost 중복 제거

S5와 동일 패턴 (sqm-core.js에 이미 정의 + window 노출).

대상: sqm-inline.js (현 line 275-336, 62줄)
- 섹션 주석 (line 275-277): /* === 2. API CLIENT === */
- var DEFAULT_TIMEOUT = 8000; (line 278)
- function apiCall(...) (line 280-330)
- function apiGet(...) (line 331)
- function apiPost(...) (line 332)
- window.apiCall = apiCall; (line 334)
- window.apiGet = apiGet; (line 335)
- window.apiPost = apiPost; (line 336)

전제 사실 (사전 검증으로 확인):
- sqm-core.js line 800-862에 동일 코드 + window 노출 (diff 빈 줄 = 100% 동일)
- sqm-core.js가 index.html line 390에서 먼저 로드 (sqm-inline.js는 line 410)
- 다른 파일들 (sqm-allocation.js, sqm-aux-modals.js, sqm-onestop-inbound.js 등)
  은 모두 window.apiCall 등 사용
- sqm-inline.js 내부 호출은 JavaScript 스코프 체인 통해 window.* 폴백

사용:
    python scripts/patch_remove_api_dupe_S6b.py --dry-run
    python scripts/patch_remove_api_dupe_S6b.py
    python scripts/patch_remove_api_dupe_S6b.py --rollback
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
CORE = ROOT / 'frontend' / 'js' / 'sqm-core.js'
SLICE_ID = 'S6b'

START_LINE = 275
END_LINE = 336
EXPECTED_DELETE_COUNT = END_LINE - START_LINE + 1  # 62줄

# 검증 시그니처
SIG_START_PREFIX = '  /* ==='  # 섹션 주석 시작
SIG_START_CONTENT_HINT = 'API CLIENT'  # line 275+3 영역에 있어야
SIG_END_LINE = '  window.apiPost = apiPost;'  # 정확한 끝 마커
SIG_OUTER_IIFE_CLOSE = '})();'

# sqm-core.js 안전망
CORE_REQUIRED_SIGNATURES = [
    '  function apiCall(method, path, body, opts) {',
    '  function apiGet(path, opts)',
    '  function apiPost(path, body, opts)',
    '  window.apiCall = apiCall;',
    '  window.apiGet  = apiGet;',
    '  window.apiPost = apiPost;',
]

IDEMPOTENCY_MARKER = '  function apiCall(method, path, body, opts) {'


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


def verify_core_safety_net():
    if not CORE.exists():
        return [f"안전망 파일 없음: {CORE}"]
    core_text = CORE.read_text(encoding='utf-8')
    errors = []
    for sig in CORE_REQUIRED_SIGNATURES:
        if sig not in core_text:
            errors.append(f"sqm-core.js에 필수 시그니처 없음: {sig!r}")
    return errors


def verify_inline_bounds(lines):
    errors = []
    if len(lines) < 5000:
        errors.append(f"sqm-inline.js 줄수 너무 적음: {len(lines)}")
        return errors

    lstart = lines[START_LINE - 1].rstrip()
    if not lstart.startswith(SIG_START_PREFIX):
        errors.append(f"line {START_LINE} 시작 시그니처 불일치: got {lstart[:50]!r}")

    block = ''.join(lines[START_LINE - 1:START_LINE + 3])
    if SIG_START_CONTENT_HINT not in block:
        errors.append(
            f"line {START_LINE}+3 영역에 '{SIG_START_CONTENT_HINT}' 힌트 없음"
        )

    lend = lines[END_LINE - 1].rstrip()
    if lend != SIG_END_LINE.rstrip():
        errors.append(f"line {END_LINE} 시그니처 불일치: got {lend!r}")

    last = lines[-1].rstrip()
    if last != SIG_OUTER_IIFE_CLOSE:
        errors.append(f"마지막 줄 outer IIFE 닫힘 손상: got {last!r}")

    return errors


def already_removed(lines):
    head = ''.join(lines[:500])
    return IDEMPOTENCY_MARKER not in head


def rollback():
    baks = sorted(INLINE.parent.glob(f'{INLINE.name}.bak_{SLICE_ID}_*'), reverse=True)
    if not baks:
        log(f'{SLICE_ID} 백업 못 찾음', 'ERR')
        return False
    shutil.copy2(baks[0], INLINE)
    log(f'복원: {INLINE.name} ← {baks[0].name}', 'OK')
    return True


def main():
    parser = argparse.ArgumentParser(description='S6b: apiCall 중복 제거')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--rollback', action='store_true')
    args = parser.parse_args()

    if args.rollback:
        log(f'=== Rollback {SLICE_ID} ===')
        return 0 if rollback() else 1

    mode = 'DRY-RUN' if args.dry_run else 'EXECUTE'
    log(f'=== S6b apiCall 중복 제거 ({mode}) ===')

    # 1. 안전망
    core_errors = verify_core_safety_net()
    if core_errors:
        log('안전망 검증 실패:', 'ERR')
        for e in core_errors:
            log(f'  - {e}', 'ERR')
        return 1
    log('sqm-core.js 안전망 검증 통과 (6개 시그니처)', 'OK')

    # 2. inline 로드
    inline_lines = read_lines(INLINE)
    log(f'입력 sqm-inline.js: {len(inline_lines)} 줄')

    # 3. Idempotency
    if already_removed(inline_lines):
        log('이미 제거됨 (function apiCall 없음). 무동작.', 'WARN')
        return 0

    # 4. 시그니처
    errors = verify_inline_bounds(inline_lines)
    if errors:
        log('사전 검증 실패:', 'ERR')
        for e in errors:
            log(f'  - {e}', 'ERR')
        return 1
    log(f'사전 검증 통과 (line {START_LINE} 섹션 주석, line {END_LINE} window 노출 끝)', 'OK')

    # 5. 삭제
    new_lines = inline_lines[:START_LINE - 1] + inline_lines[END_LINE:]
    expected_after = len(inline_lines) - EXPECTED_DELETE_COUNT
    if len(new_lines) != expected_after:
        log(f'줄수 계산 오류: 예상 {expected_after}, 실측 {len(new_lines)}', 'ERR')
        return 1

    if new_lines[-1].rstrip() != SIG_OUTER_IIFE_CLOSE:
        log(f'사후 outer IIFE 닫힘 손상: {new_lines[-1].rstrip()!r}', 'ERR')
        return 1
    log(f'사후 검증 통과 (예상 줄수 {expected_after}, outer IIFE 닫힘 유지)', 'OK')

    if args.dry_run:
        log('=== DRY-RUN 결과 (실제 변경 없음) ===', 'DRY')
        log(f'  sqm-inline.js: {len(inline_lines)} → {expected_after}', 'DRY')
        log(f'  삭제 줄수: {EXPECTED_DELETE_COUNT} (line {START_LINE}-{END_LINE})', 'DRY')
        log(f'  새 파일 생성: 없음', 'DRY')
        return 0

    log('=== 백업 ===')
    bak = backup(INLINE, SLICE_ID)
    log(f'  {bak.name}', 'OK')

    write_lines(INLINE, new_lines)
    log(f'수정: {INLINE.name} ({len(new_lines)} 줄)', 'OK')

    final = read_lines(INLINE)
    if final[-1].rstrip() != SIG_OUTER_IIFE_CLOSE:
        log(f'최종 outer IIFE 손상: {final[-1].rstrip()!r}', 'ERR')
        return 1
    log('최종 검증 통과', 'OK')
    log('=== 완료 ===')
    return 0


if __name__ == '__main__':
    sys.exit(main())
