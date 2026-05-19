# -*- coding: utf-8 -*-
"""
patch_locmap_import_menu.py — v8.6.9

frontend/js/sqm-inline.js (IIFE, 5600+줄)에 위치재고 엑셀 import 메뉴 액션 연결.
Rule 5: IIFE/대용량 파일은 Edit 금지 → 본 패치 스크립트로 처리.

추가 항목 (2곳):
  1) ENDPOINTS 맵:        'onLocationMapImport' → {m:'JS', u:'location-map-import'}
  2) JS_ACTION_HANDLERS:  'location-map-import' → window.showLocationMapImportModal()

라인 기반 삽입 (공백 민감도 회피) + 멱등성 보장.
"""
import io
import os
import shutil
import sys
from datetime import datetime

TARGET = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'frontend', 'js', 'sqm-inline.js',
)

ENDPOINT_LINES = [
    "    /* v8.6.9: 위치재고조회 엑셀 import */\n",
    "    'onLocationMapImport':{m:'JS', u:'location-map-import', lbl:'📥 위치재고 엑셀 Import'},\n",
]
HANDLER_LINE = (
    "    'location-map-import': function(){ "
    "if (typeof window.showLocationMapImportModal === 'function') "
    "{ window.showLocationMapImportModal(); } "
    "else { showToast('error', '위치재고 import 모듈 미로드'); } },\n"
)


def main() -> int:
    if not os.path.isfile(TARGET):
        print('FAIL: 대상 파일 없음:', TARGET)
        return 1

    with io.open(TARGET, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # 멱등성 — 이미 패치됨?
    if any("'onLocationMapImport'" in ln for ln in lines):
        print('SKIP: 이미 패치됨 (onLocationMapImport 존재)')
        return 0

    # 앵커 탐색
    ep_idx = next((i for i, ln in enumerate(lines)
                   if "'onWarehouseDashboard'" in ln), None)
    hd_idx = next((i for i, ln in enumerate(lines)
                   if "'warehouse-dashboard': function()" in ln), None)
    if ep_idx is None:
        print("FAIL: ENDPOINTS 앵커('onWarehouseDashboard') 미발견")
        return 1
    if hd_idx is None:
        print("FAIL: JS_ACTION_HANDLERS 앵커('warehouse-dashboard') 미발견")
        return 1

    # 백업
    bak = TARGET + '.bak_locmap_' + datetime.now().strftime('%Y%m%d_%H%M%S')
    shutil.copy2(TARGET, bak)

    # 핸들러 먼저 삽입 (뒤쪽 인덱스부터 — 앞쪽 인덱스 보존)
    lines.insert(hd_idx + 1, HANDLER_LINE)
    for off, ln in enumerate(ENDPOINT_LINES):
        lines.insert(ep_idx + 1 + off, ln)

    with io.open(TARGET, 'w', encoding='utf-8', newline='') as f:
        f.writelines(lines)

    print('OK: sqm-inline.js 패치 완료')
    print('  ENDPOINTS  삽입: 라인', ep_idx + 2)
    print('  HANDLER    삽입: 라인', hd_idx + 2 + len(ENDPOINT_LINES))
    print('  백업:', os.path.basename(bak))
    return 0


if __name__ == '__main__':
    sys.exit(main())
