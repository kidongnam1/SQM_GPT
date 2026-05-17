# -*- coding: utf-8 -*-
"""patch_nocache.py — main_webview.py URL에 타임스탬프 추가 (index.html 캐시 무력화)"""
from pathlib import Path

f = Path('main_webview.py')
src = f.read_text(encoding='utf-8')

OLD = "        url = f'http://{API_HOST}:{API_PORT}/'"
NEW = (
    "        import time as _time\n"
    "        url = f'http://{API_HOST}:{API_PORT}/?_t={int(_time.time())}'"
)

if '_time.time()' in src:
    print("이미 적용됨 — 스킵")
elif OLD in src:
    src = src.replace(OLD, NEW, 1)
    f.write_text(src, encoding='utf-8')
    print("패치 완료: URL에 타임스탬프 추가")
else:
    print("마커를 찾지 못함")
    # 현재 url 줄 확인
    for i, line in enumerate(src.splitlines(), 1):
        if "API_HOST" in line and "API_PORT" in line and "url" in line:
            print(f"  line {i}: {line}")
