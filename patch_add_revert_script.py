# -*- coding: utf-8 -*-
"""patch_add_revert_script.py — index.html에 sqm-revert.js 추가"""
from pathlib import Path

f = Path('frontend/index.html')
src = f.read_text(encoding='utf-8')

if 'sqm-revert.js' in src:
    print("\uc774\ubbf8 \ucd94\uac00\ub428 \u2014 \uc2a4\ud0b5")
else:
    OLD = '    <script src="js/sqm-onestop-inbound.js?v=20260504a"></script>'
    NEW = ('    <script src="js/sqm-onestop-inbound.js?v=20260504a"></script>\n'
           '    <script src="js/sqm-revert.js?v=20260512a"></script>')
    assert OLD in src, "marker not found"
    src = src.replace(OLD, NEW, 1)
    f.write_text(src, encoding='utf-8')
    print("\ucd94\uac00 \uc644\ub8cc")
