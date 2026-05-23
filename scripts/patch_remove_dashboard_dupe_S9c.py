# -*- coding: utf-8 -*-
"""
Phase B - Slice S9c: 대시보드 함수들 중복 제거

S9b 패턴 — sqm-inline.js가 옛 버전을 window 노출 (window.loadKpi line 4081)
sqm-core.js 신버전 활성화.

대상 (3개 묶음):
1. 상단 dashboard 영역 line 169-408 (240줄)
   - loadDashboard, loadKpi, startKpiPolling, loadDashboardTables
   - fmtN, fmtW (sqm-core.js의 window.fmtN 폴백)
   - renderStatusCards, renderProductMatrix, renderIntegrity
   - window._runIntegrityDiagnostic
2. 하단 dashboard 영역 line 3446-3484 (39줄)
   - loadAlerts, loadStatusbar, refreshStatusbar
3. window.loadKpi 노출 line 4081 (1줄)

신버전 위치 (sqm-core.js):
- loadDashboard:        line 1038
- loadKpi:              line 1045 + window 노출 line 1018
- startKpiPolling:      line 1074
- loadDashboardTables:  line 1166
- loadAlerts:           line 1180
- renderStatusCards:    line 1223
- renderProductMatrix:  line 1278
- renderIntegrity:      line 1461

주의:
- fmtN/fmtW도 sqm-core.js에 있지만 fmtW는 window 노출 없음
- fmtW는 renderIntegrity 안에서만 사용 → 같이 제거 OK
- fmtN은 인벤토리 헬퍼 (line 1275, 1276)에서도 호출 → window.fmtN 폴백
- _runIntegrityDiagnostic은 sqm-core.js에 없음 — "진단 실행" 링크는 안 보일 가능성

사용:
    python scripts/patch_remove_dashboard_dupe_S9c.py --dry-run
    python scripts/patch_remove_dashboard_dupe_S9c.py
    python scripts/patch_remove_dashboard_dupe_S9c.py --rollback
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
SLICE_ID = 'S9c'

SIG_OUTER_IIFE_CLOSE = '})();'

# Reverse line order
REMOVALS = [
    {
        'label': 'window.loadKpi 노출',
        'start': 4081,
        'end': 4081,
        'expected_content': '  window.loadKpi = loadKpi;',
    },
    {
        'label': '하단 dashboard 함수들 (loadAlerts/loadStatusbar/refreshStatusbar)',
        'start': 3446,
        'end': 3484,
        'expected_start': '  function loadAlerts() {',
        'expected_end': '  }',
    },
    {
        'label': '상단 dashboard 영역',
        'start': 169,
        'end': 408,
        'expected_start': '  function loadDashboard() {',
        'expected_end': '  };',
    },
]

CORE_REQUIRED = [
    '  function loadDashboard() {',
    '  function loadKpi() {',
    '  function loadDashboardTables() {',
    '  function loadAlerts() {',
    '  function renderStatusCards(summary) {',
    '  function renderProductMatrix(rows) {',
    '  function renderIntegrity(data, lotW) {',
    '  window.loadKpi                = loadKpi;',
    '  window.fmtN                   = fmtN;',
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


def verify_core_safety_net():
    if not CORE.exists():
        return [f"안전망 없음: {CORE}"]
    text = CORE.read_text(encoding='utf-8')
    errors = []
    for sig in CORE_REQUIRED:
        if sig not in text:
            errors.append(f"sqm-core.js에 시그니처 없음: {sig!r}")
    return errors


def verify_inline(lines):
    errors = []
    last = lines[-1].rstrip()
    if last != SIG_OUTER_IIFE_CLOSE:
        errors.append(f"outer IIFE 손상: {last!r}")

    for r in REMOVALS:
        start_idx = r['start'] - 1
        end_idx = r['end'] - 1
        if end_idx >= len(lines):
            errors.append(f"{r['label']} 범위 벗어남")
            continue

        if r['start'] == r['end']:
            line = lines[start_idx].rstrip()
            if line != r['expected_content'].rstrip():
                errors.append(f"{r['label']} line {r['start']}: got {line[:60]!r}")
        else:
            sline = lines[start_idx].rstrip()
            if sline != r['expected_start'].rstrip():
                errors.append(f"{r['label']} 시작 line {r['start']}: got {sline[:60]!r}")
            eline = lines[end_idx].rstrip()
            if eline != r['expected_end'].rstrip():
                errors.append(f"{r['label']} 끝 line {r['end']}: got {eline[:60]!r}")

    return errors


def already_removed(lines):
    text = ''.join(lines[:500])
    return '  function loadDashboard() {' not in text


def rollback():
    baks = sorted(INLINE.parent.glob(f'{INLINE.name}.bak_{SLICE_ID}_*'), reverse=True)
    if not baks:
        log(f'{SLICE_ID} 백업 없음', 'ERR')
        return False
    shutil.copy2(baks[0], INLINE)
    log(f'복원: {INLINE.name}', 'OK')
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
    log(f'=== S9c 대시보드 중복 제거 ({mode}) ===')

    sn_errors = verify_core_safety_net()
    if sn_errors:
        for e in sn_errors:
            log(f'  - {e}', 'ERR')
        return 1
    log('sqm-core.js 안전망 통과 (9개 시그니처)', 'OK')

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
    log('사전 검증 통과 (3개 영역 시그니처)', 'OK')

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
