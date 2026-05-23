# -*- coding: utf-8 -*-
"""
Phase B - Slice S7b: ESC + 모달 Enter/Tab + Ctrl+숫자 단축키 제거

대상: sqm-inline.js (현 line 40-198, 159줄)
- 섹션 주석 1b. KEYBOARD SHORTCUTS (line 40-42)
- ESC 가드 (line 44-113, _escLastAt + keydown 핸들러)
- 모달 Enter/Tab 핸들러 (line 115-176)
- Ctrl+숫자 단축키 핸들러 (line 178-198)

전제 사실:
- sqm-core.js line 415-609에 동일 영역 + 신버전 코드
- 차이점:
  * sqm-inline.js: Ctrl+2 = allocation (옛 매핑)
  * sqm-core.js: Ctrl+2 = available, Ctrl+3 = allocation (신 매핑)
  * sqm-core.js만: Ctrl+A (전체 선택), Ctrl+Delete (선택 취소)
- 현재는 두 핸들러가 모두 등록되어 sqm-inline.js 옛 버전이 등록 순서상 마지막
  → 사용자에게 옛 매핑이 보임
- 제거 시 sqm-core.js의 신버전이 단독 동작 → 신단축키 활성화

사용자 동의 확인: ✓ (신버전으로 일원화 결정)

사용:
    python scripts/patch_remove_shortcuts_dupe_S7b.py --dry-run
    python scripts/patch_remove_shortcuts_dupe_S7b.py
    python scripts/patch_remove_shortcuts_dupe_S7b.py --rollback
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
SLICE_ID = 'S7b'

START_LINE = 40
END_LINE = 198
EXPECTED_DELETE_COUNT = END_LINE - START_LINE + 1  # 159줄

SIG_START_PREFIX = '  /* ==='
SIG_START_CONTENT_HINT = 'KEYBOARD SHORTCUTS'
SIG_END_LINE = '  });'  # 마지막 keydown 핸들러 닫힘
SIG_OUTER_IIFE_CLOSE = '})();'

# sqm-core.js 안전망 — 신버전 단축키 시그니처
CORE_REQUIRED_SIGNATURES = [
    '  var _escLastAt = 0;',
    "  document.addEventListener('keydown', function(e){",
    "      case 'C-r': case 'F5':",
    "      case 'C-1':",
    "      case 'C-a':",  # 신단축키 (전체 선택)
    "      case 'C-Delete':",  # 신단축키 (선택 취소)
]

IDEMPOTENCY_MARKER = '  var _escLastAt = 0;'


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
            errors.append(f"sqm-core.js에 시그니처 없음: {sig!r}")
    return errors


def verify_inline_bounds(lines):
    errors = []
    if len(lines) < 5000:
        errors.append(f"줄수 너무 적음: {len(lines)}")
        return errors

    lstart = lines[START_LINE - 1].rstrip()
    if not lstart.startswith(SIG_START_PREFIX):
        errors.append(f"line {START_LINE} 시작 시그니처 불일치: got {lstart[:60]!r}")

    block = ''.join(lines[START_LINE - 1:START_LINE + 3])
    if SIG_START_CONTENT_HINT not in block:
        errors.append(f"line {START_LINE}+3 영역에 '{SIG_START_CONTENT_HINT}' 힌트 없음")

    lend = lines[END_LINE - 1].rstrip()
    if lend != SIG_END_LINE.rstrip():
        errors.append(f"line {END_LINE} 끝 시그니처 불일치: got {lend!r}")

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
    parser = argparse.ArgumentParser(description='S7b: 단축키 중복 제거')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--rollback', action='store_true')
    args = parser.parse_args()

    if args.rollback:
        log(f'=== Rollback {SLICE_ID} ===')
        return 0 if rollback() else 1

    mode = 'DRY-RUN' if args.dry_run else 'EXECUTE'
    log(f'=== S7b 단축키 중복 제거 ({mode}) ===')

    core_errors = verify_core_safety_net()
    if core_errors:
        log('안전망 검증 실패:', 'ERR')
        for e in core_errors:
            log(f'  - {e}', 'ERR')
        return 1
    log('sqm-core.js 안전망 통과 (6개 시그니처, 신단축키 포함)', 'OK')

    inline_lines = read_lines(INLINE)
    log(f'입력 sqm-inline.js: {len(inline_lines)} 줄')

    if already_removed(inline_lines):
        log('이미 제거됨. 무동작.', 'WARN')
        return 0

    errors = verify_inline_bounds(inline_lines)
    if errors:
        log('사전 검증 실패:', 'ERR')
        for e in errors:
            log(f'  - {e}', 'ERR')
        return 1
    log(f'사전 검증 통과 (line {START_LINE} 섹션 주석, line {END_LINE} 핸들러 끝)', 'OK')

    new_lines = inline_lines[:START_LINE - 1] + inline_lines[END_LINE:]
    expected = len(inline_lines) - EXPECTED_DELETE_COUNT
    if len(new_lines) != expected:
        log(f'줄수 오류: 예상 {expected}, 실측 {len(new_lines)}', 'ERR')
        return 1
    if new_lines[-1].rstrip() != SIG_OUTER_IIFE_CLOSE:
        log('사후 outer IIFE 손상', 'ERR')
        return 1
    log(f'사후 검증 통과 (예상 {expected})', 'OK')

    if args.dry_run:
        log('=== DRY-RUN ===', 'DRY')
        log(f'  sqm-inline.js: {len(inline_lines)} → {expected}', 'DRY')
        log(f'  삭제 줄수: {EXPECTED_DELETE_COUNT} (line {START_LINE}-{END_LINE})', 'DRY')
        log(f'  동작 변화: Ctrl+2→AVAILABLE, Ctrl+3→배정, Ctrl+A/Delete 활성화', 'DRY')
        return 0

    bak = backup(INLINE, SLICE_ID)
    log(f'백업: {bak.name}', 'OK')

    write_lines(INLINE, new_lines)
    log(f'수정: {INLINE.name} ({len(new_lines)} 줄)', 'OK')

    final = read_lines(INLINE)
    if final[-1].rstrip() != SIG_OUTER_IIFE_CLOSE:
        log('최종 outer IIFE 손상', 'ERR')
        return 1
    log('최종 검증 통과', 'OK')
    log('=== 완료 ===')
    return 0


if __name__ == '__main__':
    sys.exit(main())
