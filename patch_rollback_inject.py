# -*- coding: utf-8 -*-
"""patch_rollback_inject.py — evaluate_js revert 주입 코드 제거"""
from pathlib import Path

f = Path('main_webview.py')
src = f.read_text(encoding='utf-8')

START = "\n            # \u2500\u2500 revertToPending \ub7f0\ud0c0\uc784 \ud328\uce58 (\uce90\uc2dc \uc6b0\ud68c) \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500"
END = "            ''')\n\n        def on_closing():"
REPLACE_END = "\n\n        def on_closing():"

if '__SQM_REVERT_PATCHED__' not in src:
    print("\uc8fc\uc785 \ucf54\ub4dc \uc5c6\uc74c \u2014 \uc2a4\ud0b5")
else:
    # START ~ END 구간 제거 (END의 "def on_closing()" 부분은 유지)
    idx_start = src.find(START)
    # END 패턴 찾기
    idx_end = src.find("        def on_closing():", idx_start)
    if idx_start == -1 or idx_end == -1:
        print(f"\ub9c8\ucee4 \uc704\uce58 \uc2e4\ud328: start={idx_start}, end={idx_end}")
    else:
        src = src[:idx_start] + "\n\n" + src[idx_end:]
        f.write_text(src, encoding='utf-8')
        print("\ub864\ubc31 \uc644\ub8cc")
