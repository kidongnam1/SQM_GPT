#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_pending_empty.py — Pending 빈 메시지 3배 크기 + 가운데 정렬
"""
import shutil
from pathlib import Path
from datetime import datetime

BASE = Path('/sessions/eloquent-amazing-ramanujan/mnt/SQM_v868_claan/frontend/js')
TARGET = BASE / 'sqm-inventory.js'

OLD = '<div class="empty" style="padding:60px;text-align:center;color:var(--text-muted)">⏳ 입고 대기 중인 화물 없음</div>'
NEW = '<div class="empty" style="padding:60px;text-align:center;color:var(--text-muted);font-size:3em;font-weight:600;line-height:1.4">⏳ 입고 대기 중인 화물 없음</div>'

def main():
    print(f'\n🔧 patch_pending_empty.py — {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    text = TARGET.read_text(encoding='utf-8')
    if OLD not in text:
        print('⚠️  패턴 없음 (이미 적용됐을 수 있음)')
        return
    bak = TARGET.with_suffix('.js.bak_pendingempty')
    if not bak.exists():
        shutil.copy2(TARGET, bak)
    new_text = text.replace(OLD, NEW, 1)
    TARGET.write_text(new_text, encoding='utf-8')
    print('✅ Pending 빈 메시지 font-size:3em 적용 완료')

if __name__ == '__main__':
    main()
