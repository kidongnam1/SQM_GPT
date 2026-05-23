# -*- coding: utf-8 -*-
"""
Phase B - Slice S9b: loadInventoryPage + loadAllocationPage override 제거

S7b와 동일 패턴 — sqm-inline.js가 옛 버전을 window에 노출해서
다른 파일의 신버전을 덮어쓰고 있음. 제거 시 신버전이 활성화됨.

대상:
- loadInventoryPage  본문 line 414-553  (140줄)
- loadAllocationPage 본문 line 870-945  (76줄)
- window.loadAllocationPage 노출 line 163 (1줄)
- window.loadInventoryPage  노출 line 4298 (1줄)

신버전 위치:
- loadInventoryPage  → sqm-inventory.js:19 (sumUnsold/sumSold 등 통계 항목 추가)
- loadAllocationPage → sqm-allocation.js:35

동작 변화 (사용자 사전 동의):
- 재고 페이지: 신규 통계 항목 활성화
- 배정 페이지: 신버전 UI/동작

페이지 사이의 헬퍼 함수들 (window.invApplyFilter, window._allocViewMode 등)
은 그대로 유지 (다음 슬라이스에서 별도 검토).

전략: reverse line order (가장 아래 line 4298부터 위로 차례로 제거)

사용:
    python scripts/patch_remove_inv_alloc_override_S9b.py --dry-run
    python scripts/patch_remove_inv_alloc_override_S9b.py
    python scripts/patch_remove_inv_alloc_override_S9b.py --rollback
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
JS_DIR = ROOT / 'frontend' / 'js'
SLICE_ID = 'S9b'

SIG_OUTER_IIFE_CLOSE = '})();'

# 제거 영역 (reverse line order)
REMOVALS = [
    {
        'label': 'window.loadInventoryPage 노출',
        'start': 4298,
        'end': 4298,
        'expected_content': '  window.loadInventoryPage = loadInventoryPage;',
    },
    {
        'label': 'loadAllocationPage 함수 본문',
        'start': 870,
        'end': 945,
        'expected_start': '  function loadAllocationPage() {',
        'expected_end': '  }',
    },
    {
        'label': 'loadInventoryPage 함수 본문',
        'start': 414,
        'end': 553,
        'expected_start': '  function loadInventoryPage() {',
        'expected_end': '  }',
    },
    {
        'label': 'window.loadAllocationPage 노출',
        'start': 163,
        'end': 163,
        'expected_content': '  window.loadAllocationPage = loadAllocationPage;',
    },
]

# 안전망 (신버전이 다른 파일에 존재해야)
SAFETY_NETS = [
    ('sqm-inventory.js', '  function loadInventoryPage() {'),
    ('sqm-inventory.js', '  window.loadInventoryPage  = loadInventoryPage;'),
    ('sqm-allocation.js', '  function loadAllocationPage() {'),
    ('sqm-allocation.js', '  window.loadAllocationPage = loadAllocationPage;'),
]


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


def verify_safety_nets():
    errors = []
    for fname, sig in SAFETY_NETS:
        f = JS_DIR / fname
        if not f.exists():
            errors.append(f"{fname} 없음")
            continue
        text = f.read_text(encoding='utf-8')
        if sig not in text:
            errors.append(f"{fname}에 시그니처 없음: {sig!r}")
    return errors


def verify_inline(lines):
    errors = []
    last = lines[-1].rstrip()
    if last != SIG_OUTER_IIFE_CLOSE:
        errors.append(f"마지막 줄 outer IIFE 손상: {last!r}")

    for r in REMOVALS:
        start_idx = r['start'] - 1
        end_idx = r['end'] - 1
        if end_idx >= len(lines):
            errors.append(f"{r['label']} 라인 {r['end']} 범위 벗어남")
            continue

        if r['start'] == r['end']:
            # 단일 라인 (window 노출)
            line = lines[start_idx].rstrip()
            if line != r['expected_content'].rstrip():
                errors.append(
                    f"{r['label']} line {r['start']} 시그니처 불일치: got {line[:60]!r}"
                )
        else:
            # 함수 본문 (시작/끝 검증)
            sline = lines[start_idx].rstrip()
            if sline != r['expected_start'].rstrip():
                errors.append(
                    f"{r['label']} 시작 line {r['start']} 시그니처 불일치: got {sline[:60]!r}"
                )
            eline = lines[end_idx].rstrip()
            if eline != r['expected_end'].rstrip():
                errors.append(
                    f"{r['label']} 끝 line {r['end']} 시그니처 불일치: got {eline[:60]!r}"
                )

    return errors


def already_removed(lines):
    """함수 정의가 없으면 이미 제거됨"""
    text = ''.join(lines[:1000])
    return '  function loadInventoryPage() {' not in text


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
    log(f'=== S9b loadInventoryPage + loadAllocationPage override 제거 ({mode}) ===')

    sn_errors = verify_safety_nets()
    if sn_errors:
        for e in sn_errors:
            log(f'  - {e}', 'ERR')
        return 1
    log('안전망 검증 통과 (sqm-inventory.js + sqm-allocation.js 신버전 + window 노출)', 'OK')

    inline_lines = read_lines(INLINE)
    log(f'입력 sqm-inline.js: {len(inline_lines)} 줄')

    if already_removed(inline_lines):
        log('이미 제거됨', 'WARN')
        return 0

    errors = verify_inline(inline_lines)
    if errors:
        for e in errors:
            log(f'  - {e}', 'ERR')
        return 1
    log('사전 검증 통과 (4개 영역 시그니처 일치)', 'OK')

    # Reverse line order 처리 (REMOVALS 이미 reverse 정렬됨)
    current = list(inline_lines)
    total_removed = 0
    for r in REMOVALS:
        start_idx = r['start'] - 1
        end_idx = r['end']
        removed = end_idx - start_idx
        current = current[:start_idx] + current[end_idx:]
        total_removed += removed
        log(f'  {r["label"]}: line {r["start"]}-{r["end"]} ({removed}줄)', 'OK')

    expected = len(inline_lines) - total_removed
    if len(current) != expected:
        log(f'줄수 오류: 예상 {expected}, 실측 {len(current)}', 'ERR')
        return 1
    if current[-1].rstrip() != SIG_OUTER_IIFE_CLOSE:
        log('사후 outer IIFE 손상', 'ERR')
        return 1
    log(f'사후 검증 통과 ({len(inline_lines)} → {expected}, 총 -{total_removed}줄)', 'OK')

    if args.dry_run:
        log('DRY-RUN: 변경 없음', 'DRY')
        return 0

    bak = backup(INLINE, SLICE_ID)
    log(f'백업: {bak.name}', 'OK')

    write_lines(INLINE, current)
    log(f'수정: {INLINE.name} ({len(current)}줄)', 'OK')

    final = read_lines(INLINE)
    if final[-1].rstrip() != SIG_OUTER_IIFE_CLOSE:
        log('최종 outer IIFE 손상', 'ERR')
        return 1
    log('=== 완료 ===')
    return 0


if __name__ == '__main__':
    sys.exit(main())
