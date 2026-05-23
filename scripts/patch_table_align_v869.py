# -*- coding: utf-8 -*-
"""
patch_table_align_v869.py — SQM v8.6.9
=======================================
테이블 헤더↔데이터 정렬 정합성 패치 (IIFE 파일 → Rule 5 준수 패치 스크립트).

item 1) sqm-listview.js  — LOT_COLS / TONBAG_COLS 컬럼에 align:'center' 추가
          (제품명·비고는 긴 텍스트 → 왼쪽 유지, 의도적 제외)
item 2) sqm-picked.js / sqm-inventory.js / sqm-logistics.js
          — LOT 컬럼 데이터셀 .cell-left / text-align:left → 가운데
            (헤더는 center 인데 데이터만 left 이던 불일치 해소)

작성: Ruby (남기동) / 2026-05-20
"""
import io
import os
import re

JS_DIR = r'D:\program\SQM_inventory\sqm_v869_clean\frontend\js'

# item 1 — sqm-listview.js 컬럼 정의에서 align 부여할 키
LISTVIEW_CENTER_KEYS = {
    'sap_no', 'bl_no', 'container_no', 'lot_no', 'lot_sqm', 'vessel', 'do_no',
    'tonbag_uid', 'location', 'sold_to', 'sale_ref',
}
# product / remarks 는 의도적으로 제외 (긴 텍스트 → 왼쪽 유지)

# item 2 — 단순 문자열 치환 (파일, old, new)
STR_REPLACEMENTS = [
    # sqm-picked.js — LOT No 데이터셀 cell-left 제거
    ('sqm-picked.js',
     '<td class="mono-cell cell-left" style="color:var(--accent);font-weight:600">\' + lot',
     '<td class="mono-cell" style="color:var(--accent);font-weight:600">\' + lot'),
    # sqm-inventory.js — 샘플행 LOT 셀 text-align:left → center
    ('sqm-inventory.js',
     'font-weight:700;text-align:left;padding:6px 10px;line-height:1.2">\'+lotKey+\'(SP)',
     'font-weight:700;text-align:center;padding:6px 10px;line-height:1.2">\'+lotKey+\'(SP)'),
    # sqm-inventory.js — 본행 LOT 셀 cell-left 제거
    ('sqm-inventory.js',
     '<td class="mono-cell cell-left" style="color:var(--accent);font-weight:600;padding:6px 10px;line-height:1.2">\'+lotKey',
     '<td class="mono-cell" style="color:var(--accent);font-weight:600;padding:6px 10px;line-height:1.2">\'+lotKey'),
    # sqm-logistics.js — 반품 샘플행 LOT 셀 cell-left 제거
    ('sqm-logistics.js',
     '<td class="mono-cell cell-left" style="color:#eab308;font-weight:700;padding:6px 10px">\' + lotKey',
     '<td class="mono-cell" style="color:#eab308;font-weight:700;padding:6px 10px">\' + lotKey'),
    # sqm-logistics.js — 반품 본행 LOT 셀 cell-left 제거
    ('sqm-logistics.js',
     '<td class="mono-cell cell-left" style="color:#a855f7;font-weight:600;padding:6px 10px">\' + lotKey',
     '<td class="mono-cell" style="color:#a855f7;font-weight:600;padding:6px 10px">\' + lotKey'),
]

# 컬럼정의 1줄: `{ k: 'xxx', ... }` 끝의 ` }` 앞에 align 삽입
_COL_RE = re.compile(r"^(\s*\{ k: '([a-z_]+)',.*?)\s*\},\s*$")


def _read(path):
    with io.open(path, 'r', encoding='utf-8') as f:
        return f.read()


def _write(path, text):
    with io.open(path, 'w', encoding='utf-8', newline='') as f:
        f.write(text)


def patch_listview():
    path = os.path.join(JS_DIR, 'sqm-listview.js')
    text = _read(path)
    out_lines = []
    changed = 0
    for line in text.split('\n'):
        m = _COL_RE.match(line)
        if m and m.group(2) in LISTVIEW_CENTER_KEYS and 'align:' not in line:
            line = m.group(1) + ", align: 'center' },"
            changed += 1
        out_lines.append(line)
    if changed != len(LISTVIEW_CENTER_KEYS) * 2:
        # LOT_COLS + TONBAG_COLS 각각 1번씩 = 11키 x 2 = 22
        print('  ⚠️ sqm-listview.js — 예상 22건, 실제 %d건' % changed)
    _write(path, '\n'.join(out_lines))
    print('  sqm-listview.js — align:center %d개 컬럼 추가' % changed)
    return changed


def patch_str_replacements():
    total = 0
    for fname, old, new in STR_REPLACEMENTS:
        path = os.path.join(JS_DIR, fname)
        text = _read(path)
        cnt = text.count(old)
        if cnt == 0:
            print('  ❌ %s — 대상 문자열 못 찾음 (수동 확인 필요)' % fname)
            continue
        if cnt > 1:
            print('  ⚠️ %s — 대상 %d건 (의도와 다를 수 있음)' % (fname, cnt))
        _write(path, text.replace(old, new))
        total += cnt
        print('  %s — %d건 치환' % (fname, cnt))
    return total


if __name__ == '__main__':
    print('item 1) sqm-listview.js 컬럼 정렬:')
    patch_listview()
    print('item 2) LOT 컬럼 데이터셀 정렬:')
    patch_str_replacements()
    print('완료.')
