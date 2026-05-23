# -*- coding: utf-8 -*-
"""
Phase B - Slice S5: 다운로드 헬퍼 중복 제거

원래 계획: sqm-inline.js의 다운로드 헬퍼 4개를 새 파일 sqm-util-download.js로 추출
실제 발견: 동일 함수 4개가 이미 sqm-core.js (line 175-286)에 정의 + window 노출 중
변경된 작업: 추출이 아니라 **중복 제거** (delete duplicate)

대상: sqm-inline.js (현 line 11-131, 121줄)
- function sqmShouldOpenXlsxAfterSave (line 20)
- window.sqmSetOpenXlsxAfterSave (line 29)
- function sqmSuggestedXlsxName (line 35)
- function sqmDownloadFileUrl (line 49)

전제 사실:
- sqm-core.js가 index.html line 390에서 먼저 로드 (sqm-inline.js는 line 410)
- sqm-core.js line 1023-1024: window.sqmDownloadFileUrl, window.sqmShouldOpenXlsxAfterSave 노출
- 4개 함수 모두 sqm-core.js와 sqm-inline.js의 정의 100% 동일 (이미 diff 확인됨)
- 다른 JS 파일들 (sqm-listview.js, sqm-tonbag.js 등) 은 모두 window.* 사용
- sqm-inline.js 내부 12회 호출 → window.* 폴백으로 자동 동작

안전장치:
1. sqm-core.js 존재 + 함수 정의 + window 노출 사전 검증
2. sqm-inline.js의 line 11/131 시그니처 검증
3. outer IIFE 닫힘 (마지막 줄 `})();`) 검증
4. 타임스탬프 백업
5. Idempotent (이미 제거됐는지 함수 정의 grep)
6. --dry-run 지원

사용:
    python scripts/patch_remove_download_dupe_S5.py --dry-run
    python scripts/patch_remove_download_dupe_S5.py
    python scripts/patch_remove_download_dupe_S5.py --rollback
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
SLICE_ID = 'S5'

# 추출 경계 (1-based, 현 sqm-inline.js 기준 = S1-S4 후)
START_LINE = 14
END_LINE = 131
EXPECTED_DELETE_COUNT = END_LINE - START_LINE + 1  # 118줄

# 검증 시그니처
SIG_START_PREFIX = '  /**'  # JSDoc 시작 (Excel/FileResponse 주석)
SIG_START_CONTENT_HINT = 'Excel/FileResponse'
SIG_END_LINE = '  }'  # sqmDownloadFileUrl 닫힘
SIG_END_MINUS_1 = '      });'  # fetch 체인 끝
SIG_OUTER_IIFE_CLOSE = '})();'

# sqm-core.js 검증용 (이게 있어야 sqm-inline.js의 사본을 삭제해도 안전)
CORE_REQUIRED_SIGNATURES = [
    '  function sqmShouldOpenXlsxAfterSave',
    '  function sqmDownloadFileUrl',
    '  window.sqmDownloadFileUrl     = sqmDownloadFileUrl;',
    '  window.sqmShouldOpenXlsxAfterSave = sqmShouldOpenXlsxAfterSave;',
]

# Idempotency: 이미 제거됐는지 감지 (function sqmDownloadFileUrl 없으면 제거됨)
IDEMPOTENCY_MARKER = '  function sqmDownloadFileUrl'


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
    """sqm-core.js에 다운로드 헬퍼 함수 + window 노출이 있는지 확인.

    이게 있어야 sqm-inline.js의 사본을 삭제해도 동작이 보존됨.
    """
    if not CORE.exists():
        return [f"안전망 파일 없음: {CORE}"]

    core_text = CORE.read_text(encoding='utf-8')
    errors = []
    for sig in CORE_REQUIRED_SIGNATURES:
        if sig not in core_text:
            errors.append(f"sqm-core.js에 필수 시그니처 없음: {sig!r}")
    return errors


def verify_inline_bounds(lines):
    """sqm-inline.js의 추출 영역 검증."""
    errors = []

    # 줄수
    if len(lines) < 5000:
        errors.append(f"sqm-inline.js 줄수 너무 적음: {len(lines)}")
        return errors

    # 시작 마커 (JSDoc)
    lstart = lines[START_LINE - 1].rstrip()
    if not lstart.startswith(SIG_START_PREFIX):
        errors.append(
            f"line {START_LINE} 시작 시그니처 불일치: got {lstart[:50]!r}"
        )

    # 시작 근처에 'Excel/FileResponse' 힌트
    block = ''.join(lines[START_LINE - 1:START_LINE + 3])
    if SIG_START_CONTENT_HINT not in block:
        errors.append(
            f"line {START_LINE}+3 영역에 '{SIG_START_CONTENT_HINT}' 힌트 없음"
        )

    # 끝 직전 (fetch chain end)
    lpre = lines[END_LINE - 2].rstrip()
    if lpre != SIG_END_MINUS_1.rstrip():
        errors.append(
            f"line {END_LINE - 1} 시그니처 불일치: got {lpre!r}"
        )

    # 끝 (sqmDownloadFileUrl 닫힘)
    lend = lines[END_LINE - 1].rstrip()
    if lend != SIG_END_LINE.rstrip():
        errors.append(
            f"line {END_LINE} 시그니처 불일치: got {lend!r}"
        )

    # outer IIFE 닫힘
    last = lines[-1].rstrip()
    if last != SIG_OUTER_IIFE_CLOSE:
        errors.append(f"마지막 줄 outer IIFE 닫힘 손상: got {last!r}")

    return errors


def already_removed(lines):
    head = ''.join(lines[:200])
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
    parser = argparse.ArgumentParser(description='S5: 다운로드 헬퍼 중복 제거')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--rollback', action='store_true')
    args = parser.parse_args()

    if args.rollback:
        log(f'=== Rollback {SLICE_ID} ===')
        return 0 if rollback() else 1

    mode = 'DRY-RUN' if args.dry_run else 'EXECUTE'
    log(f'=== S5 다운로드 헬퍼 중복 제거 ({mode}) ===')

    # 1. 안전망 검증 — sqm-core.js에 정의 있어야 함
    core_errors = verify_core_safety_net()
    if core_errors:
        log('안전망 검증 실패 — sqm-core.js에 필요한 정의가 없음:', 'ERR')
        for e in core_errors:
            log(f'  - {e}', 'ERR')
        log('이 상태로 sqm-inline.js의 사본을 지우면 다운로드 기능 깨짐. 중단.', 'ERR')
        return 1
    log('sqm-core.js 안전망 검증 통과 (4개 시그니처 모두 존재)', 'OK')

    # 2. sqm-inline.js 로드
    inline_lines = read_lines(INLINE)
    log(f'입력 sqm-inline.js: {len(inline_lines)} 줄')

    # 3. Idempotency
    if already_removed(inline_lines):
        log('이미 제거됨 (function sqmDownloadFileUrl 없음). 무동작.', 'WARN')
        return 0

    # 4. 시그니처 검증
    errors = verify_inline_bounds(inline_lines)
    if errors:
        log('사전 검증 실패:', 'ERR')
        for e in errors:
            log(f'  - {e}', 'ERR')
        return 1
    log(f'사전 검증 통과 (line {START_LINE} 주석, line {END_LINE} 닫힘, outer IIFE 닫힘)', 'OK')

    # 5. 삭제 시뮬레이션
    new_lines = inline_lines[:START_LINE - 1] + inline_lines[END_LINE:]
    expected_after = len(inline_lines) - EXPECTED_DELETE_COUNT
    if len(new_lines) != expected_after:
        log(f'줄수 계산 오류: 예상 {expected_after}, 실측 {len(new_lines)}', 'ERR')
        return 1

    # 6. 사후 outer IIFE 검증
    if new_lines[-1].rstrip() != SIG_OUTER_IIFE_CLOSE:
        log(f'사후 outer IIFE 닫힘 손상: 마지막 줄 = {new_lines[-1].rstrip()!r}', 'ERR')
        return 1
    log(f'사후 검증 통과 (예상 줄수 {expected_after}, outer IIFE 닫힘 유지)', 'OK')

    # 7. DRY-RUN
    if args.dry_run:
        log('=== DRY-RUN 결과 (실제 변경 없음) ===', 'DRY')
        log(f'  sqm-inline.js: {len(inline_lines)} → {expected_after} 줄', 'DRY')
        log(f'  삭제 줄수: {EXPECTED_DELETE_COUNT} (line {START_LINE}-{END_LINE})', 'DRY')
        log(f'  새 파일 생성: 없음 (sqm-core.js 가 이미 정의/노출)', 'DRY')
        log(f'  index.html 변경: 없음', 'DRY')
        return 0

    # 8. 백업
    log('=== 백업 생성 ===')
    bak = backup(INLINE, SLICE_ID)
    log(f'  {bak.name}', 'OK')

    # 9. 쓰기
    write_lines(INLINE, new_lines)
    log(f'수정: {INLINE.name} ({len(new_lines)} 줄)', 'OK')

    # 10. 최종 검증
    final = read_lines(INLINE)
    if final[-1].rstrip() != SIG_OUTER_IIFE_CLOSE:
        log(f'최종 outer IIFE 손상: {final[-1].rstrip()!r}', 'ERR')
        log('  → 즉시 --rollback', 'ERR')
        return 1
    log(f'최종 검증 통과: outer IIFE 닫힘 유지', 'OK')

    log('=== 완료 ===')
    log('다음: node --check, 앱 실행 (다운로드 메뉴 테스트)', 'INFO')
    return 0


if __name__ == '__main__':
    sys.exit(main())
