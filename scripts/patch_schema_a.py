#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_schema_a.py — Sprint A 4개 항목 일괄 패치
  A-1: showToast('warn', → showToast('warning',   (sqm-inventory.js)
  A-2: class="sqm-table" → class="data-table"     (sqm-core.js, sqm-inline.js)
  A-3: <th ...width:32px → width:36px             (sqm-allocation.js, sqm-inline.js, sqm-inventory.js)
  A-4: English empty messages → Korean             (sqm-inline.js, sqm-logistics.js, sqm-tonbag.js)

Rule 5: 모든 대상 파일이 IIFE / 1000줄 이상 → Edit 툴 금지, 이 스크립트로만 처리
"""

import re
import sys
import shutil
from pathlib import Path
from datetime import datetime

BASE = Path('/sessions/eloquent-amazing-ramanujan/mnt/SQM_v868_claan/frontend/js')

# ── 패치 정의 ─────────────────────────────────────────────────────────────
patches = [
    # A-1: showToast warn → warning (sqm-inventory.js, 단순 문자열 치환)
    {
        'file': 'sqm-inventory.js',
        'label': 'A-1 showToast warn→warning',
        'mode': 'simple',
        'old': "showToast('warn',",
        'new': "showToast('warning',",
    },

    # A-2: sqm-table → data-table (class 속성만)
    {
        'file': 'sqm-core.js',
        'label': 'A-2 sqm-table→data-table (core)',
        'mode': 'simple',
        'old': 'class="sqm-table"',
        'new': 'class="data-table"',
    },
    {
        'file': 'sqm-inline.js',
        'label': 'A-2 sqm-table→data-table (inline)',
        'mode': 'simple',
        'old': 'class="sqm-table"',
        'new': 'class="data-table"',
    },

    # A-3: <th ...width:32px → width:36px  (th 태그 안에서만)
    {
        'file': 'sqm-inventory.js',
        'label': 'A-3 width:32px→36px in <th (inventory)',
        'mode': 'th_width',
    },
    {
        'file': 'sqm-allocation.js',
        'label': 'A-3 width:32px→36px in <th (allocation)',
        'mode': 'th_width',
    },
    {
        'file': 'sqm-inline.js',
        'label': 'A-3 width:32px→36px in <th (inline)',
        'mode': 'th_width',
    },

    # A-4: 영어 빈 메시지 → 한국어
    {
        'file': 'sqm-inline.js',
        'label': 'A-4 empty msgs Korean (inline)',
        'mode': 'multi',
        'replacements': [
            ('No movement history', '이동 이력 없음'),
            ('No logs',             '로그 없음'),
            ('No tonbag data',      '톤백 데이터 없음'),
        ],
    },
    {
        'file': 'sqm-logistics.js',
        'label': 'A-4 empty msgs Korean (logistics)',
        'mode': 'multi',
        'replacements': [
            ('No movement history', '이동 이력 없음'),
            ('No logs',             '로그 없음'),
        ],
    },
    {
        'file': 'sqm-tonbag.js',
        'label': 'A-4 empty msgs Korean (tonbag)',
        'mode': 'multi',
        'replacements': [
            ('No tonbag data', '톤백 데이터 없음'),
        ],
    },
]


def apply_patch(patch):
    fp = BASE / patch['file']
    if not fp.exists():
        print(f'  ❌ 파일 없음: {fp}')
        return False

    original = fp.read_text(encoding='utf-8')
    mode = patch['mode']
    changed = 0

    if mode == 'simple':
        count = original.count(patch['old'])
        if count == 0:
            print(f'  ⚠️  매치 없음: {patch["label"]}')
            return True  # 이미 적용됐을 수 있음
        new_text = original.replace(patch['old'], patch['new'])
        changed = count

    elif mode == 'th_width':
        # <th 태그 안에서만 width:32px → width:36px
        # 정규식: <th ... style="...width:32px..." 에서만 치환
        # 줄 단위로 처리: 해당 줄에 <th 가 있고 width:32px 가 있으면 치환
        lines = original.split('\n')
        new_lines = []
        for line in lines:
            if '<th' in line and 'width:32px' in line:
                new_line = line.replace('width:32px', 'width:36px')
                new_lines.append(new_line)
                changed += 1
            else:
                new_lines.append(line)
        new_text = '\n'.join(new_lines)

    elif mode == 'multi':
        new_text = original
        for old, new in patch['replacements']:
            count = new_text.count(old)
            if count == 0:
                print(f'  ⚠️  매치 없음: "{old}" in {patch["file"]}')
            else:
                new_text = new_text.replace(old, new)
                changed += count
    else:
        print(f'  ❌ 알 수 없는 mode: {mode}')
        return False

    if new_text != original:
        # 백업
        bak = fp.with_suffix(fp.suffix + '.bak_schemaa')
        shutil.copy2(fp, bak)
        fp.write_text(new_text, encoding='utf-8')
        print(f'  ✅ {patch["label"]} — {changed}곳 치환, 백업: {bak.name}')
    else:
        print(f'  ℹ️  변경 없음 (이미 적용?): {patch["label"]}')

    return True


def main():
    print(f'\n🔧 patch_schema_a.py 시작 — {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print(f'   대상 폴더: {BASE}\n')

    ok = True
    for p in patches:
        ok = apply_patch(p) and ok

    print()
    if ok:
        print('✅ 패치 완료')
    else:
        print('❌ 일부 패치 실패 — 위 로그 확인')
        sys.exit(1)


if __name__ == '__main__':
    main()
