# -*- coding: utf-8 -*-
"""patch_version_bump.py — index.html JS 버전 쿼리스트링 업데이트 (캐시 무효화)"""
from pathlib import Path

f = Path('frontend/index.html')
src = f.read_text(encoding='utf-8')

# sqm-inventory.js 와 sqm-inline.js (sqm-onestop-inbound) 버전 업
OLD_INV = 'sqm-inventory.js?v=20260505a'
NEW_INV = 'sqm-inventory.js?v=20260512a'

OLD_CORE = 'sqm-core.js?v=20260505a'
NEW_CORE = 'sqm-core.js?v=20260512a'

changed = []
if OLD_INV in src:
    src = src.replace(OLD_INV, NEW_INV)
    changed.append('sqm-inventory.js')
if OLD_CORE in src:
    src = src.replace(OLD_CORE, NEW_CORE)
    changed.append('sqm-core.js')

if changed:
    f.write_text(src, encoding='utf-8')
    print("버전 업: " + ', '.join(changed))
else:
    print("이미 최신 버전이거나 패턴 없음")
    # 현재 버전 출력
    import re
    for m in re.finditer(r'sqm-[^"]+\.js\?v=[^"]+', src):
        print(" ", m.group())
