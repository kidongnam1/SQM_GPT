# -*- coding: utf-8 -*-
"""
Phase B - Slices S2 + S3 + S4 묶음: 유틸리티 함수 3개 추출

S2: escapeHtml          (현 line 469-473)  + 별도 line 5333 잔재 제거
S3: enableTableSort     (현 line 224-261)
S4: dbg 디버그 패널     (현 line 133-198)  + 별도 line 210 잔재 제거

전제: S1 (Tooltip) 이미 적용되어 sqm-inline.js = 5503줄

전략:
- 단순 추출 불가 (각 함수가 sqm-inline.js 내부에서 호출됨)
  - escapeHtml: 161회 호출
  - enableTableSort: 2회 호출
  - dbgLog: 33회 호출
- 따라서 새 모듈에서 window.* 글로벌로 노출
- JavaScript 스코프 체인 덕에 sqm-inline.js의 호출 코드는 안 건드림
- Reverse line order (S2 → S3 → S4) 처리해서 라인 시프트 충돌 없음

설계 문서: docs/refactor/sqm-inline-split-plan.md
S1 참조: scripts/patch_split_tooltip_S1.py

사용:
    python scripts/patch_split_utility_S234.py --dry-run
    python scripts/patch_split_utility_S234.py
    python scripts/patch_split_utility_S234.py --rollback
"""

import argparse
import sys
import shutil
from datetime import datetime
from pathlib import Path

# Windows cp949 콘솔 인코딩 대응
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

ROOT = Path(__file__).resolve().parent.parent
INLINE = ROOT / 'frontend' / 'js' / 'sqm-inline.js'
HTML = ROOT / 'frontend' / 'index.html'

JS_DIR = ROOT / 'frontend' / 'js'
SLICE_ID = 'S234'

SIG_OUTER_IIFE_CLOSE = '})();'

# 슬라이스 정의 (reverse line order — 위쪽부터)
# 각 슬라이스: start_line, end_line, start_marker (검증용), end_marker (검증용),
#              residue_marker (추가 제거할 단일 라인 패턴 또는 None),
#              new_file, expose_var, idempotency_marker, slice_label
SLICES = [
    # S2: escapeHtml — 가장 아래 위치 (line 469-473)
    {
        'id': 'S2',
        'label': 'escapeHtml',
        'start_line': 469,
        'end_line': 473,
        'start_marker': '  function escapeHtml(s) {',
        'end_marker': '  }',
        'residue_marker': '  window.escapeHtml = escapeHtml;',
        'new_file': JS_DIR / 'sqm-util-escape.js',
        'expose_name': 'escapeHtml',
        'idempotency_marker': '__SQM_UTIL_ESCAPE_INSTALLED__',
        'header_title': 'sqm-util-escape.js — escapeHtml 글로벌 유틸',
        'source_note': 'sqm-inline.js (현 line 469-473) + window 노출 line 5333',
    },
    # S3: enableTableSort — 중간 (line 223-261)
    {
        'id': 'S3',
        'label': 'enableTableSort',
        'start_line': 223,
        'end_line': 261,
        'start_marker': '  /* ===================================================',
        'end_marker': '  _sortObserver.observe(document.documentElement, {childList:true, subtree:true});',
        'residue_marker': None,  # 별도 잔재 없음
        'new_file': JS_DIR / 'sqm-util-tablesort.js',
        'expose_name': 'enableTableSort',
        'idempotency_marker': '__SQM_UTIL_TABLESORT_INSTALLED__',
        'header_title': 'sqm-util-tablesort.js — 테이블 헤더 클릭 정렬',
        'source_note': 'sqm-inline.js (현 line 224-261)',
        'header_required': '1a. TABLE SORT',  # 시작 marker 다음 줄 검증용
    },
    # S4: dbg 디버그 패널 — 가장 위 (line 133-197)
    {
        'id': 'S4',
        'label': 'dbg',
        'start_line': 133,
        'end_line': 197,
        'start_marker': '  /* ===================================================',
        'end_marker': '  }',
        'residue_marker': '  window.dbgLog = dbgLog;',
        'new_file': JS_DIR / 'sqm-util-dbg.js',
        'expose_name': 'dbgLog',
        'idempotency_marker': '__SQM_UTIL_DBG_INSTALLED__',
        'header_title': 'sqm-util-dbg.js — 화면 우측 하단 디버그 로그 패널 (F8 토글)',
        'source_note': 'sqm-inline.js (현 line 133-198) + window 노출 line 210',
        'header_required': '0. ON-SCREEN DEBUG LOG PANEL',
    },
]

HTML_INSERT_BEFORE = '<script src="js/sqm-inline.js'


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


def verify_slice_bounds(lines, slice_def):
    """슬라이스 경계 시그니처 검증."""
    s = slice_def
    errors = []
    start_idx = s['start_line'] - 1
    end_idx = s['end_line'] - 1

    if start_idx < 0 or end_idx >= len(lines):
        errors.append(f"{s['id']} 줄번호 범위 벗어남")
        return errors

    start_line_content = lines[start_idx].rstrip()
    if not start_line_content.startswith(s['start_marker'].rstrip()):
        errors.append(
            f"{s['id']} 시작 시그니처 불일치 (line {s['start_line']}): "
            f"got {start_line_content[:60]!r}"
        )

    end_line_content = lines[end_idx].rstrip()
    if not end_line_content.startswith(s['end_marker'].rstrip()):
        errors.append(
            f"{s['id']} 끝 시그니처 불일치 (line {s['end_line']}): "
            f"got {end_line_content[:60]!r}"
        )

    # header_required 추가 검증
    if 'header_required' in s:
        block = ''.join(lines[start_idx:start_idx + 5])
        if s['header_required'] not in block:
            errors.append(
                f"{s['id']} 시작 영역 (line {s['start_line']}+5) 에 "
                f"'{s['header_required']}' 헤더 없음"
            )

    # residue_marker 검증
    if s['residue_marker']:
        found = any(
            line.rstrip().startswith(s['residue_marker'].rstrip())
            for line in lines
        )
        if not found:
            errors.append(
                f"{s['id']} 잔재 marker 못 찾음: {s['residue_marker']!r}"
            )

    return errors


def build_new_file(extracted_lines, slice_def):
    """추출된 줄들을 새 IIFE 모듈로 포장.

    핵심: 추출된 함수를 IIFE 안에서 정의하고 window.* 에 노출
    """
    s = slice_def
    today = datetime.now().strftime('%Y-%m-%d')

    header = (
        f'/* =======================================================================\n'
        f'   SQM Inventory - {s["header_title"]}\n'
        f'   Extracted from sqm-inline.js (Phase B-{s["id"]}) — {today}\n'
        f'   Source: {s["source_note"]}\n'
        f'   ======================================================================= */\n'
        f'(function () {{\n'
        f"  'use strict';\n"
        f'  if (window.{s["idempotency_marker"]}) return;\n'
        f'  window.{s["idempotency_marker"]} = true;\n'
        f'\n'
    )
    body = ''.join(extracted_lines)
    footer = (
        f'\n'
        f'  // 글로벌 노출 (sqm-inline.js 의 기존 호출 호환)\n'
        f'  window.{s["expose_name"]} = {s["expose_name"]};\n'
        f'}})();\n'
    )
    return header + body + footer


def remove_residue_line(lines, marker):
    """잔재 marker 줄을 정확히 1개만 제거."""
    found_idx = None
    for i, line in enumerate(lines):
        if line.rstrip().startswith(marker.rstrip()):
            if found_idx is not None:
                raise RuntimeError(f"잔재 marker가 여러 곳에 있음: {marker!r}")
            found_idx = i

    if found_idx is None:
        raise RuntimeError(f"잔재 marker 못 찾음: {marker!r}")

    new_lines = lines[:found_idx] + lines[found_idx + 1:]
    return new_lines, found_idx + 1  # 1-based 라인 번호


def apply_slice(lines, slice_def):
    """1개 슬라이스를 적용. (수정된 lines, 새 파일 텍스트, 정보 dict) 반환."""
    s = slice_def
    start_idx = s['start_line'] - 1
    end_idx = s['end_line'] - 1
    extracted = lines[start_idx:end_idx + 1]

    new_file_text = build_new_file(extracted, s)

    # 본문 제거
    new_lines = lines[:start_idx] + lines[end_idx + 1:]

    # 잔재 라인 제거
    residue_removed_at = None
    if s['residue_marker']:
        new_lines, residue_removed_at = remove_residue_line(new_lines, s['residue_marker'])

    info = {
        'slice_id': s['id'],
        'label': s['label'],
        'extracted_count': len(extracted),
        'residue_removed_at': residue_removed_at,
        'new_file_lines': new_file_text.count('\n'),
        'new_file_path': s['new_file'],
    }
    return new_lines, new_file_text, info


def update_index_html_batch(html_lines, slices_to_add):
    """index.html에 새 script 태그들을 sqm-inline.js 앞에 한 번에 삽입."""
    # 이미 있는지 검사
    existing = set()
    for s in slices_to_add:
        for line in html_lines:
            if s['new_file'].name in line:
                existing.add(s['id'])

    # sqm-inline.js 줄 찾기
    inline_idx = None
    for i, line in enumerate(html_lines):
        if HTML_INSERT_BEFORE in line:
            inline_idx = i
            break

    if inline_idx is None:
        raise RuntimeError(f"index.html에서 '{HTML_INSERT_BEFORE}' 못 찾음")

    today_v = datetime.now().strftime('%Y%m%d') + 'a'
    new_tags = []
    inserted = []
    for s in slices_to_add:
        if s['id'] in existing:
            continue
        tag = f'    <script src="js/{s["new_file"].name}?v={today_v}"></script>\n'
        new_tags.append(tag)
        inserted.append((s['id'], s['new_file'].name))

    if not new_tags:
        return html_lines, [], inline_idx + 1

    new_html_lines = (
        html_lines[:inline_idx]
        + new_tags
        + html_lines[inline_idx:]
    )
    return new_html_lines, inserted, inline_idx + 1


def rollback():
    """가장 최근 S234 백업으로부터 복원."""
    paths_to_restore = [INLINE, HTML]
    candidates = []
    for p in paths_to_restore:
        baks = sorted(p.parent.glob(f'{p.name}.bak_{SLICE_ID}_*'), reverse=True)
        if baks:
            candidates.append((p, baks[0]))

    if not candidates:
        log(f'{SLICE_ID} 백업 파일을 찾지 못함', 'ERR')
        return False

    for target, bak in candidates:
        shutil.copy2(bak, target)
        log(f'복원: {target.name} ← {bak.name}', 'OK')

    # 생성된 파일들 삭제
    for s in SLICES:
        if s['new_file'].exists():
            s['new_file'].unlink()
            log(f'생성 파일 삭제: {s["new_file"].name}', 'OK')

    return True


def main():
    parser = argparse.ArgumentParser(description='S234 묶음: util 3개 추출')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--rollback', action='store_true')
    args = parser.parse_args()

    if args.rollback:
        log(f'=== Rollback {SLICE_ID} ===')
        return 0 if rollback() else 1

    mode = 'DRY-RUN' if args.dry_run else 'EXECUTE'
    log(f'=== S2+S3+S4 묶음 추출 ({mode}) ===')

    # 1. 입력 로드
    inline_lines = read_lines(INLINE)
    html_lines = read_lines(HTML)
    log(f'입력 sqm-inline.js: {len(inline_lines)} 줄')
    log(f'입력 index.html: {len(html_lines)} 줄')

    # 2. 마지막 줄 outer IIFE 닫힘 확인
    last = inline_lines[-1].rstrip()
    if last != SIG_OUTER_IIFE_CLOSE:
        log(f'outer IIFE 닫힘 손상 (이미): 마지막 줄 = {last!r}', 'ERR')
        return 1
    log(f'outer IIFE 닫힘 확인: 마지막 줄 = {last!r}', 'OK')

    # 3. Idempotency
    skip = []
    for s in SLICES:
        if s['new_file'].exists():
            skip.append(s['id'])
    if skip:
        log(f'이미 추출된 슬라이스: {skip}', 'WARN')
        log('아무것도 하지 않음. 모두 새로 하려면 --rollback 후 재시도.', 'INFO')
        return 0

    # 4. 모든 슬라이스 사전 검증
    all_errors = []
    for s in SLICES:
        errs = verify_slice_bounds(inline_lines, s)
        if errs:
            log(f"{s['id']} 사전 검증 실패:", 'ERR')
            for e in errs:
                log(f'  - {e}', 'ERR')
            all_errors.extend(errs)
        else:
            log(f"{s['id']} ({s['label']}) 사전 검증 통과", 'OK')

    if all_errors:
        log('하나 이상 사전 검증 실패. 중단.', 'ERR')
        return 1

    # 5. Reverse line order로 슬라이스 적용
    # SLICES 는 이미 reverse line order (S2가 가장 아래 line, S4가 가장 위 line)
    current_lines = list(inline_lines)
    new_files_to_create = []
    apply_info_list = []
    for s in SLICES:
        current_lines, new_file_text, info = apply_slice(current_lines, s)
        new_files_to_create.append((s['new_file'], new_file_text))
        apply_info_list.append(info)
        log(
            f"{info['slice_id']} ({info['label']}): "
            f"{info['extracted_count']}줄 추출, "
            f"잔재 line@{info['residue_removed_at']}, "
            f"새 파일 {info['new_file_lines']}줄",
            'OK',
        )

    # 6. 사후 검증: 줄수 + outer IIFE 닫힘
    total_extracted = sum(i['extracted_count'] for i in apply_info_list)
    total_residue = sum(1 for i in apply_info_list if i['residue_removed_at'])
    expected_lines = len(inline_lines) - total_extracted - total_residue
    if len(current_lines) != expected_lines:
        log(
            f'줄수 불일치: 예상 {expected_lines}, 실측 {len(current_lines)}',
            'ERR',
        )
        return 1
    log(
        f'사후 줄수 정확: {len(inline_lines)} → {len(current_lines)} '
        f'(-{total_extracted}-{total_residue})',
        'OK',
    )

    last_after = current_lines[-1].rstrip()
    if last_after != SIG_OUTER_IIFE_CLOSE:
        log(f'outer IIFE 닫힘 손상: 마지막 줄 = {last_after!r}', 'ERR')
        return 1
    log(f'outer IIFE 닫힘 유지: 마지막 줄 = {last_after!r}', 'OK')

    # 7. index.html 업데이트
    new_html_lines, inserted, insert_at = update_index_html_batch(html_lines, SLICES)
    log(f'index.html line {insert_at} 앞에 {len(inserted)}개 script 태그 삽입 예정', 'OK')
    for sid, fname in inserted:
        log(f'  + {sid}: {fname}', 'INFO')

    # 8. DRY-RUN 종료
    if args.dry_run:
        log('=== DRY-RUN 결과 (실제 변경 없음) ===', 'DRY')
        log(f'  sqm-inline.js: {len(inline_lines)} → {len(current_lines)}', 'DRY')
        log(f'  index.html: {len(html_lines)} → {len(new_html_lines)}', 'DRY')
        for fpath, text in new_files_to_create:
            log(f'  생성: {fpath.name} ({text.count(chr(10))} 줄)', 'DRY')
        return 0

    # 9. 실제 적용 — 백업 먼저
    log('=== 백업 생성 ===')
    bak_inline = backup(INLINE, SLICE_ID)
    log(f'  {bak_inline.name}', 'OK')
    bak_html = backup(HTML, SLICE_ID)
    log(f'  {bak_html.name}', 'OK')

    # 10. 파일 쓰기
    log('=== 파일 쓰기 ===')
    for fpath, text in new_files_to_create:
        write_text(fpath, text)
        log(f'  새 파일: {fpath.name} ({text.count(chr(10))} 줄)', 'OK')
    write_lines(INLINE, current_lines)
    log(f'  수정: {INLINE.name} ({len(current_lines)} 줄)', 'OK')
    write_lines(HTML, new_html_lines)
    log(f'  수정: {HTML.name} ({len(new_html_lines)} 줄)', 'OK')

    # 11. 최종 검증 (디스크에서 재로딩)
    log('=== 최종 검증 ===')
    final_inline = read_lines(INLINE)
    final_last = final_inline[-1].rstrip()
    if final_last == SIG_OUTER_IIFE_CLOSE:
        log(f'  outer IIFE 닫힘 유지: 마지막 줄 = {final_last!r}', 'OK')
    else:
        log(f'  outer IIFE 닫힘 손상: 마지막 줄 = {final_last!r}', 'ERR')
        log('  → 즉시 --rollback 권장', 'ERR')
        return 1

    log('=== 완료 ===')
    log('다음: node --check 모든 파일, 앱 실행 검증', 'INFO')
    return 0


if __name__ == '__main__':
    sys.exit(main())
