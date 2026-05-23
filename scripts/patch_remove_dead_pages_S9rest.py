# -*- coding: utf-8 -*-
"""
Phase B - Slice S9-rest: 8개 dead duplicate 페이지 일괄 제거

S9-log (loadLogPage) 시범 통과 후 나머지 8개 페이지를 묶음 처리.

대상 (모두 sqm-inline.js에 window 노출 없음 → dead duplicate):
- loadStubPage     line 159-162   (4줄)   → sqm-core.js:1001
- loadPickedPage   line 1424-1475 (52줄)  → sqm-picked.js:143 + window 노출
- loadInboundPage  line 1586-1643 (58줄)  → sqm-logistics.js:78
- loadOutboundPage line 1655-1711 (57줄)  → sqm-logistics.js:361
- loadReturnPage   line 1759-1784 (26줄)  → sqm-logistics.js:530
- loadMovePage     line 1800-1845 (46줄)  → sqm-logistics.js:633
- loadScanPage     line 1863-1911 (49줄)  → sqm-logistics.js:780
- loadTonbagPage   line 1995-2034 (40줄)  → sqm-tonbag.js:30 + window 노출

페이지 사이의 헬퍼 함수 (window.togglePickedDetail 등) 는 그대로 유지.
(다음 슬라이스에서 별도 검토)

전략: reverse line order 처리 (가장 아래쪽 페이지부터 삭제 → 라인 시프트 없음)

사용:
    python scripts/patch_remove_dead_pages_S9rest.py --dry-run
    python scripts/patch_remove_dead_pages_S9rest.py
    python scripts/patch_remove_dead_pages_S9rest.py --rollback
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
SLICE_ID = 'S9rest'

SIG_OUTER_IIFE_CLOSE = '})();'

# reverse line order (큰 라인부터 작은 라인 순)
PAGES = [
    {
        'name': 'loadTonbagPage',
        'start': 1995,
        'end': 2034,
        'safety_file': 'sqm-tonbag.js',
        'safety_sig': '  function loadTonbagPage() {',
    },
    {
        'name': 'loadScanPage',
        'start': 1863,
        'end': 1911,
        'safety_file': 'sqm-logistics.js',
        'safety_sig': '  function loadScanPage() {',
    },
    {
        'name': 'loadMovePage',
        'start': 1800,
        'end': 1845,
        'safety_file': 'sqm-logistics.js',
        'safety_sig': '  function loadMovePage() {',
    },
    {
        'name': 'loadReturnPage',
        'start': 1759,
        'end': 1784,
        'safety_file': 'sqm-logistics.js',
        'safety_sig': '  function loadReturnPage() {',
    },
    {
        'name': 'loadOutboundPage',
        'start': 1655,
        'end': 1711,
        'safety_file': 'sqm-logistics.js',
        'safety_sig': '  function loadOutboundPage() {',
    },
    {
        'name': 'loadInboundPage',
        'start': 1586,
        'end': 1643,
        'safety_file': 'sqm-logistics.js',
        'safety_sig': '  function loadInboundPage() {',
    },
    {
        'name': 'loadPickedPage',
        'start': 1424,
        'end': 1475,
        'safety_file': 'sqm-picked.js',
        'safety_sig': '  function loadPickedPage() {',
    },
    {
        'name': 'loadStubPage',
        'start': 159,
        'end': 162,
        'safety_file': 'sqm-core.js',
        'safety_sig': '  function loadStubPage(route) {',
    },
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
    for p in PAGES:
        f = JS_DIR / p['safety_file']
        if not f.exists():
            errors.append(f"{p['safety_file']} 없음")
            continue
        text = f.read_text(encoding='utf-8')
        if p['safety_sig'] not in text:
            errors.append(f"{p['safety_file']}에 {p['name']} 정의 없음")
    return errors


def verify_inline(lines):
    errors = []
    last = lines[-1].rstrip()
    if last != SIG_OUTER_IIFE_CLOSE:
        errors.append(f"마지막 줄 outer IIFE 손상: {last!r}")

    # 각 페이지의 시작 라인이 정의 시작인지 확인
    for p in PAGES:
        start_idx = p['start'] - 1
        if start_idx >= len(lines):
            errors.append(f"{p['name']} 시작 라인 {p['start']} 범위 벗어남")
            continue
        line = lines[start_idx].rstrip()
        if 'function ' + p['name'] not in line:
            errors.append(
                f"{p['name']} line {p['start']}이 함수 정의 아님: got {line[:60]!r}"
            )

        # 끝 라인이 `  }` 인지 확인
        end_idx = p['end'] - 1
        if end_idx >= len(lines):
            errors.append(f"{p['name']} 끝 라인 {p['end']} 범위 벗어남")
            continue
        end_line = lines[end_idx].rstrip()
        if end_line != '  }':
            errors.append(
                f"{p['name']} line {p['end']} 끝 아님: got {end_line[:60]!r}"
            )

    # sqm-inline.js가 이 페이지들을 window 노출하지 않는지 (dead 검증)
    text = ''.join(lines)
    for p in PAGES:
        if f'window.{p["name"]}' in text:
            errors.append(f"{p['name']}이 sqm-inline.js에서 window 노출 — dead 가정 무효")

    return errors


def already_removed(lines):
    """가장 위 (loadStubPage)가 없으면 이미 제거됨"""
    if PAGES[-1]['start'] >= len(lines):
        return True
    line = lines[PAGES[-1]['start'] - 1]
    return 'function loadStubPage' not in line


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
    log(f'=== S9-rest 8개 dead 페이지 일괄 제거 ({mode}) ===')

    sn_errors = verify_safety_nets()
    if sn_errors:
        for e in sn_errors:
            log(f'  - {e}', 'ERR')
        return 1
    log(f'안전망 검증 통과 ({len(PAGES)}개 페이지 모두 다른 파일에 정의 존재)', 'OK')

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
    log('사전 검증 통과 (8개 페이지 시작/끝 + dead 확인)', 'OK')

    # Reverse line order로 삭제
    current = list(inline_lines)
    total_removed = 0
    for p in PAGES:  # 이미 reverse order로 정렬됨
        start_idx = p['start'] - 1
        end_idx = p['end']
        removed = end_idx - start_idx
        current = current[:start_idx] + current[end_idx:]
        total_removed += removed
        log(f'  {p["name"]} 제거: line {p["start"]}-{p["end"]} ({removed}줄)', 'OK')

    expected = len(inline_lines) - total_removed
    if len(current) != expected:
        log(f'줄수 오류: 예상 {expected}, 실측 {len(current)}', 'ERR')
        return 1
    if current[-1].rstrip() != SIG_OUTER_IIFE_CLOSE:
        log('사후 outer IIFE 손상', 'ERR')
        return 1
    log(f'사후 검증 통과 ({len(inline_lines)} → {expected}, 총 -{total_removed}줄)', 'OK')

    if args.dry_run:
        log(f'DRY-RUN: 변경 없음', 'DRY')
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
