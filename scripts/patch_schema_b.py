#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_schema_b.py — Sprint B 패치
  B-1: sqmConfirm() 유틸 sqm-core.js 에 추가 (글로벌 선언)
  B-2: confirm( → sqmConfirm(  (전체 JS 파일)
  B-3: 영문 "Loading..." → 한글 "⏳ 로딩 중..."

Rule 5: IIFE / 1000줄 이상 파일 전부 → 이 스크립트로만 처리
"""

import re
import sys
import shutil
from pathlib import Path
from datetime import datetime

BASE = Path('/sessions/eloquent-amazing-ramanujan/mnt/SQM_v868_claan/frontend/js')

CONFIRM_FILES = [
    'sqm-inline.js',
    'sqm-tonbag.js',
    'sqm-allocation.js',
    'sqm-onestop-inbound.js',
    'sqm-logistics.js',
    'sqm-inventory.js',
    'sqm-picked.js',
    'sqm-core.js',
]

LOADING_FILES = [
    'sqm-inline.js',
    'sqm-logistics.js',
    'sqm-tonbag.js',
]

SQMCONFIRM_INJECTION = '''\
/* -----------------------------------------------------------------------
   sqmConfirm — 브라우저 기본 confirm() 추상화 래퍼
   향후 커스텀 모달(비동기)로 교체할 때 이 함수만 변경하면 됨
   사용법: if (!sqmConfirm('정말 삭제할까요?')) return;
   ----------------------------------------------------------------------- */
window.sqmConfirm = window.sqmConfirm || function (msg) {
  return window.confirm(msg);
};

'''


def backup(fp):
    """백업 파일이 없으면 생성."""
    bak = fp.with_suffix(fp.suffix + '.bak_schemab')
    if not bak.exists():
        shutil.copy2(fp, bak)


# ── B-1: sqmConfirm 글로벌 함수 추가 ──────────────────────────────────────
def inject_sqmconfirm(fp):
    text = fp.read_text(encoding='utf-8')
    if 'window.sqmConfirm' in text:
        print(f'  ℹ️  B-1 이미 존재: {fp.name}')
        return True
    target = '(function () {'
    if target not in text:
        print(f'  ❌ B-1 IIFE 패턴 없음: {fp.name}')
        return False
    new_text = text.replace(target, SQMCONFIRM_INJECTION + target, 1)
    backup(fp)
    fp.write_text(new_text, encoding='utf-8')
    print(f'  ✅ B-1 sqmConfirm 추가 → {fp.name}')
    return True


# ── B-2: confirm( → sqmConfirm( ────────────────────────────────────────────
def patch_confirm(fp):
    text = fp.read_text(encoding='utf-8')
    # \bconfirm\( : 단어 경계 → executePendingConfirm( 등 보호
    matches = re.findall(r'\bconfirm\(', text)
    if not matches:
        print(f'  ⚠️  B-2 매치 없음: {fp.name}')
        return True
    new_text = re.sub(r'\bconfirm\(', 'sqmConfirm(', text)
    backup(fp)
    fp.write_text(new_text, encoding='utf-8')
    print(f'  ✅ B-2 confirm→sqmConfirm — {len(matches)}곳: {fp.name}')
    return True


# ── B-3: Loading... → 로딩 중... ──────────────────────────────────────────
def patch_loading(fp):
    original = fp.read_text(encoding='utf-8')
    text = original
    changed = 0

    # 케이스 1: "⏳ Loading..." → "⏳ 로딩 중..."
    c1 = text.count('⏳ Loading...')
    if c1:
        text = text.replace('⏳ Loading...', '⏳ 로딩 중...')
        changed += c1

    # 케이스 2: ">Loading...</" → ">⏳ 로딩 중...</"  (섹션 로딩 div)
    c2 = text.count('>Loading...</')
    if c2:
        text = text.replace('>Loading...</', '>⏳ 로딩 중...</')
        changed += c2

    # 케이스 3: 나머지 "Loading..." (class="empty" 내부 등)
    c3 = text.count('Loading...')
    if c3:
        text = text.replace('Loading...', '로딩 중...')
        changed += c3

    if changed == 0:
        print(f'  ⚠️  B-3 매치 없음: {fp.name}')
        return True

    backup(fp)
    fp.write_text(text, encoding='utf-8')
    print(f'  ✅ B-3 Loading→로딩중 — {changed}곳: {fp.name}')
    return True


def main():
    print(f'\n🔧 patch_schema_b.py 시작 — {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    ok = True

    print('\n[B-1] sqmConfirm 유틸 추가')
    ok = inject_sqmconfirm(BASE / 'sqm-core.js') and ok

    print('\n[B-2] confirm → sqmConfirm 전체 치환')
    for fname in CONFIRM_FILES:
        fp = BASE / fname
        if not fp.exists():
            print(f'  ❌ 없음: {fname}')
            continue
        ok = patch_confirm(fp) and ok

    print('\n[B-3] Loading... → 로딩 중...')
    for fname in LOADING_FILES:
        fp = BASE / fname
        if not fp.exists():
            print(f'  ❌ 없음: {fname}')
            continue
        ok = patch_loading(fp) and ok

    print()
    if ok:
        print('✅ Sprint B 패치 완료')
    else:
        print('❌ 일부 실패 — 위 로그 확인')
        sys.exit(1)


if __name__ == '__main__':
    main()
