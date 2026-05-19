# -*- coding: utf-8 -*-
"""
patch_avail_sample_row.py
-------------------------
Available 메뉴(loadAvailablePage)의 SAMPLE 행에서
Invoice ~ Location 8개 칸이 `<td colspan="8">—</td>` 하나로 비어 있던 것을
일반 행과 동일하게 실제 데이터로 채운다.

채우는 8개 컬럼 (헤더 순서대로):
  Invoice / Ship / Arrival / Con Return / Free / WH / Inbound(MT) / Location

- Invoice~WH, Location : LOT(r) 공유 정보 → 메인 행과 동일 값, 샘플 색(#94a3b8)
- Inbound(MT)          : 샘플 자체 중량 r.sample_weight_mt (샘플 색 #eab308)

Rule 5: sqm-inventory.js 는 1232줄 + IIFE `})();` → Edit 금지, 본 스크립트로만 처리.
"""
import os
import sys
import datetime

PATH = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'js', 'sqm-inventory.js')

OLD = "'<td colspan=\"8\" style=\"color:#555\">—</td>'"

NEW = (
    "'<td class=\"mono-cell\" style=\"color:#94a3b8\">' + escapeHtml(r.invoice_no||'') + '</td>' +\n"
    "            '<td class=\"mono-cell\" style=\"color:#94a3b8\">' + escapeHtml((r.ship_date||'').slice(0,10)) + '</td>' +\n"
    "            '<td class=\"mono-cell\" style=\"color:#94a3b8\">' + escapeHtml((r.arrival_date||'').slice(0,10)) + '</td>' +\n"
    "            '<td class=\"mono-cell\" style=\"color:#94a3b8\">' + escapeHtml((r.con_return||'').slice(0,10)) + '</td>' +\n"
    "            '<td class=\"mono-cell\" style=\"text-align:center;color:#94a3b8\">' + (r.free_time!=null?r.free_time:'-') + '</td>' +\n"
    "            '<td class=\"mono-cell\" style=\"color:#94a3b8\">' + escapeHtml(r.wh||'') + '</td>' +\n"
    "            '<td class=\"mono-cell\" style=\"text-align:right;color:#eab308\">' + fmtN(r.sample_weight_mt||0) + '</td>' +\n"
    "            '<td><span class=\"tag\" style=\"background:rgba(234,179,8,0.1);color:#94a3b8\">' + escapeHtml(r.location||'-') + '</span></td>'"
)


def main():
    print('=== Available SAMPLE 행 빈 칸 채우기 ===')
    with open(PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    orig = content

    n = content.count(OLD)
    if n != 1:
        print('[FAIL] 대상 패턴 발견 횟수 %d (기대 1) — 중단' % n)
        sys.exit(1)

    content = content.replace(OLD, NEW, 1)
    if content == orig:
        print('[SKIP] 변경 없음')
        sys.exit(0)

    ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    bak = PATH + '.bak_samplerow_' + ts
    with open(bak, 'w', encoding='utf-8') as f:
        f.write(orig)
    with open(PATH, 'w', encoding='utf-8') as f:
        f.write(content)
    print('[OK] sqm-inventory.js — SAMPLE 행에 8개 칸 추가  (백업: %s)' % os.path.basename(bak))


if __name__ == '__main__':
    main()
