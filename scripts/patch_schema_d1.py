#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_schema_d1.py — Phase 3 D1: STATUS 색상/라벨 상수 단일화

  D1-a: window.SQM_STATUS_MAP 글로벌 상수 → sqm-core.js 에 추가
  D1-b: sqm-inline.js 의 중복 statusColor/statusFg 삼항 체인 2곳 → 상수 조회로 교체

현재 중복 패턴 (sqm-inline.js 1479-1480, 1653-1654):
  var statusColor = status === 'SOLD' ? '#66bb6a' : status === 'PICKED' ? '#42a5f5' : 'var(--warning)';
  var statusFg = status === 'RESERVED' ? '#000' : '#fff';

교체 후:
  var _sm = (window.SQM_STATUS_MAP||{})[status]||{}; var statusColor = _sm.color||'var(--warning)'; var statusFg = _sm.fg||'#fff';
"""

import shutil
import sys
from pathlib import Path
from datetime import datetime

BASE = Path('/sessions/eloquent-amazing-ramanujan/mnt/SQM_v868_claan/frontend/js')

# SQM_STATUS_MAP 글로벌 상수 블록
STATUS_MAP_INJECTION = '''\
/* -----------------------------------------------------------------------
   SQM_STATUS_MAP — STATUS 색상·라벨 단일 정본 (D1 구조 단일화)
   향후 design-tokens.css 변수로 전환 시 이 블록만 수정
   ----------------------------------------------------------------------- */
window.SQM_STATUS_MAP = window.SQM_STATUS_MAP || {
  PENDING:   { color: '#90a4ae',          fg: '#fff',  label: '입고대기' },
  AVAILABLE: { color: 'var(--success)',   fg: '#fff',  label: '재고'    },
  RESERVED:  { color: 'var(--warning)',   fg: '#000',  label: '배정'    },
  PICKED:    { color: '#42a5f5',          fg: '#fff',  label: '피킹'    },
  SOLD:      { color: '#66bb6a',          fg: '#fff',  label: '출고'    },
  RETURN:    { color: '#ef5350',          fg: '#fff',  label: '반품'    },
};

'''

# 교체 대상 (완전 일치 문자열)
OLD_STATUS_PAIR = (
    "      var statusColor = status === 'SOLD' ? '#66bb6a' : status === 'PICKED' ? '#42a5f5' : 'var(--warning)';\n"
    "      var statusFg = status === 'RESERVED' ? '#000' : '#fff';"
)
NEW_STATUS_PAIR = (
    "      var _sm = (window.SQM_STATUS_MAP||{})[status]||{}; "
    "var statusColor = _sm.color||'var(--warning)'; var statusFg = _sm.fg||'#fff';"
)


def backup(fp):
    bak = fp.with_suffix(fp.suffix + '.bak_schemad1')
    if not bak.exists():
        shutil.copy2(fp, bak)


def patch_core(fp):
    """D1-a: SQM_STATUS_MAP 추가"""
    text = fp.read_text(encoding='utf-8')
    if 'SQM_STATUS_MAP' in text:
        print(f'  ℹ️  D1-a 이미 존재: {fp.name}')
        return True
    # sqmConfirm 블록 바로 뒤에 삽입 (sqmConfirm이 있으면 그 뒤, 없으면 IIFE 앞)
    anchor = 'window.sqmConfirm = window.sqmConfirm ||'
    iife_anchor = '(function () {'
    if anchor in text:
        # sqmConfirm 블록 끝 다음 줄에 삽입
        insert_after = '  return window.confirm(msg);\n};\n'
        new_text = text.replace(insert_after, insert_after + '\n' + STATUS_MAP_INJECTION, 1)
    elif iife_anchor in text:
        new_text = text.replace(iife_anchor, STATUS_MAP_INJECTION + iife_anchor, 1)
    else:
        print(f'  ❌ D1-a 삽입 앵커 없음: {fp.name}')
        return False
    backup(fp)
    fp.write_text(new_text, encoding='utf-8')
    print(f'  ✅ D1-a SQM_STATUS_MAP 추가 → {fp.name}')
    return True


def patch_inline(fp):
    """D1-b: sqm-inline.js statusColor/statusFg 삼항 → 상수 조회"""
    text = fp.read_text(encoding='utf-8')
    count = text.count(OLD_STATUS_PAIR)
    if count == 0:
        print(f'  ⚠️  D1-b 패턴 없음: {fp.name} (이미 적용됐을 수 있음)')
        return True
    new_text = text.replace(OLD_STATUS_PAIR, NEW_STATUS_PAIR)
    backup(fp)
    fp.write_text(new_text, encoding='utf-8')
    print(f'  ✅ D1-b statusColor 삼항→상수 조회 {count}곳: {fp.name}')
    return True


def main():
    print(f'\n🔧 patch_schema_d1.py 시작 — {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    ok = True

    print('\n[D1-a] SQM_STATUS_MAP 글로벌 상수 추가')
    ok = patch_core(BASE / 'sqm-core.js') and ok

    print('\n[D1-b] sqm-inline.js 중복 statusColor 삼항 교체')
    ok = patch_inline(BASE / 'sqm-inline.js') and ok

    print()
    if ok:
        print('✅ Phase 3 D1 패치 완료')
    else:
        print('❌ 일부 실패')
        sys.exit(1)


if __name__ == '__main__':
    main()
