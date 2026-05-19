# -*- coding: utf-8 -*-
"""
patch_avail_rsv_tooltip.py
--------------------------
Avail/Rsv(MT) · AV/VR/AR · MXBG/Available/Reserved/Packed 컬럼에
설명 툴팁(title)을 추가한다. (헤더 + 데이터 셀)

대상 탭:
  - Available  (sqm-inventory.js / loadAvailablePage)  : Avail/Rsv(MT), MXBG, Avail
  - Inventory  (sqm-inventory.js / loadInventoryPage)   : MXBG~Remain Bags, AV/VR/AR
  - Allocation (sqm-allocation.js)                      : MXBG~Remain Bags, AV/VR/AR
  - Picked     (sqm-picked.js / 메인표 + 그룹표)         : MXBG~Remain Bags, AV/VR/AR

Rule 5: 위 3개 파일은 모두 IIFE `})();` 패턴 → Edit 툴 금지, 본 스크립트로만 처리.
"""
import os
import sys
import datetime

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

JS = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'js')

# ── 툴팁 문구 (title 속성 → " 금지, ' 금지) ──────────────────────────
T_COMBINED   = '앞=가용 중량(MT, 바로 배분 가능) / 뒤=예약(RESERVED) 중량.  예: 3.000/▲2.000 → 총 5MT 중 2MT 예약·3MT 배분 가능'
T_AV         = '가용 중량 AV (Available MT) — 아직 배정 안 된, 바로 배분 가능한 물량'
T_VR         = '예약 중량 VR (Reserved MT) — RESERVED 상태로 배정 잡힌 물량'
T_AR         = '피킹 중량 AR (Picked MT) — 출고 작업 중(PICKED)인 물량'
T_MXBG       = '총 톤백 개수 (MAXI BAG)'
T_BAG_AV     = '가용 톤백 수(개) — 바로 배분 가능한 톤백'
T_BAG_VR     = '예약 톤백 수(개) — 배정 잡힌 톤백'
T_BAG_AR     = '피킹/포장된 톤백 수(개)'
T_BAG_TOTAL  = '전체 톤백 수(개)'
T_BAG_REMAIN = '남은 톤백 수 = 전체 − 가용 − 예약 − 피킹'


def th(label, tip):
    """plain <th> → title 부착"""
    return ('<th>' + label + '</th>', '<th title="' + tip + '">' + label + '</th>')


def th_styled(style, label, tip):
    """<th style="..."> → title 부착"""
    src = '<th style="' + style + '">' + label + '</th>'
    dst = '<th title="' + tip + '" style="' + style + '">' + label + '</th>'
    return (src, dst)


def td(cell, tip):
    """<td ...> 로 시작하는 셀 문자열 → 첫 <td 뒤에 title 삽입"""
    return (cell, cell.replace('<td ', '<td title="' + tip + '" ', 1))


# ════════════════════════════════════════════════════════════════════
#  sqm-inventory.js
# ════════════════════════════════════════════════════════════════════
INV = [
    # ── Available 페이지 헤더 ──
    ('<th>Avail/Rsv(MT)</th>', '<th title="' + T_COMBINED + '">Avail/Rsv(MT)</th>'),
    ("'<th>MXBG</th><th>Avail</th><th>Invoice</th>'",
     "'<th title=\"" + T_MXBG + "\">MXBG</th>"
     "<th title=\"" + T_BAG_AV + "\">Avail</th><th>Invoice</th>'"),

    # ── Inventory 페이지 헤더 (MXBG~AR 한 줄) ──
    ("'<th>MXBG</th><th>Available</th><th>Reserved</th><th>Packed</th>"
     "<th>Total Bags</th><th>Remain Bags</th><th>AV</th><th>VR</th><th>AR</th><th>Invoice</th>'",
     "'<th title=\"" + T_MXBG + "\">MXBG</th>"
     "<th title=\"" + T_BAG_AV + "\">Available</th>"
     "<th title=\"" + T_BAG_VR + "\">Reserved</th>"
     "<th title=\"" + T_BAG_AR + "\">Packed</th>"
     "<th title=\"" + T_BAG_TOTAL + "\">Total Bags</th>"
     "<th title=\"" + T_BAG_REMAIN + "\">Remain Bags</th>"
     "<th title=\"" + T_AV + "\">AV</th>"
     "<th title=\"" + T_VR + "\">VR</th>"
     "<th title=\"" + T_AR + "\">AR</th><th>Invoice</th>'"),

    # ── Inventory 페이지 데이터 셀 ──
    td("'<td class=\"mono-cell\" style=\"text-align:center;padding:6px 10px;line-height:1.2\">' +", T_MXBG),
    td("'<td class=\"mono-cell\" style=\"text-align:center;color:#22c55e;font-weight:700\">'+availBags+'</td>'", T_BAG_AV),
    td("'<td class=\"mono-cell\" style=\"text-align:center;color:#3b82f6;font-weight:700\">'+reservedBags+'</td>'", T_BAG_VR),
    td("'<td class=\"mono-cell\" style=\"text-align:center;color:#f59e0b;font-weight:700\">'+packedBags+'</td>'", T_BAG_AR),
    td("'<td class=\"mono-cell\" style=\"text-align:center\">'+totalBags+'</td>'", T_BAG_TOTAL),
    td("'<td class=\"mono-cell\" style=\"text-align:center;font-weight:700\">'+remainBags+'</td>'", T_BAG_REMAIN),
    td("'<td class=\"mono-cell\" style=\"text-align:right;color:#22c55e;font-weight:700\">'+(r.avail_mt!=null?fmtN(r.avail_mt):'-')+'</td>'", T_AV),
    td("'<td class=\"mono-cell\" style=\"text-align:right;color:#3b82f6;font-weight:700\">'+(r.reserved_mt!=null?fmtN(r.reserved_mt):'-')+'</td>'", T_VR),
    td("'<td class=\"mono-cell\" style=\"text-align:right;color:#f59e0b;font-weight:700\">'+(r.picked_mt!=null?fmtN(r.picked_mt):'-')+'</td>'", T_AR),

    # ── Available 페이지 데이터 셀 (멀티라인) ──
    ("'<td class=\"mono-cell\" style=\"text-align:right\">'\n"
     "            + '<span style=\"color:#22c55e;font-weight:700\">'",
     "'<td title=\"" + T_COMBINED + "\" class=\"mono-cell\" style=\"text-align:right\">'\n"
     "            + '<span style=\"color:#22c55e;font-weight:700\">'"),
    ("'<td class=\"mono-cell\" style=\"text-align:center\">'\n"
     "            + (r.mxbg_pallet > 0",
     "'<td title=\"" + T_MXBG + "\" class=\"mono-cell\" style=\"text-align:center\">'\n"
     "            + (r.mxbg_pallet > 0"),
    td("'<td class=\"mono-cell\" style=\"text-align:center\">' + (r.avail_bags!=null?r.avail_bags:'-') + '</td>'", T_BAG_AV),
]

# ════════════════════════════════════════════════════════════════════
#  sqm-allocation.js
# ════════════════════════════════════════════════════════════════════
ALLOC = [
    # ── 헤더 (각 <th> 한 줄, 내부 4칸 들여쓰기) ──
    ("'    <th>MXBG</th>'",        "'    <th title=\"" + T_MXBG + "\">MXBG</th>'"),
    ("'    <th>Available</th>'",   "'    <th title=\"" + T_BAG_AV + "\">Available</th>'"),
    ("'    <th>Reserved</th>'",    "'    <th title=\"" + T_BAG_VR + "\">Reserved</th>'"),
    ("'    <th>Packed</th>'",      "'    <th title=\"" + T_BAG_AR + "\">Packed</th>'"),
    ("'    <th>Total Bags</th>'",  "'    <th title=\"" + T_BAG_TOTAL + "\">Total Bags</th>'"),
    ("'    <th>Remain Bags</th>'", "'    <th title=\"" + T_BAG_REMAIN + "\">Remain Bags</th>'"),
    ("'    <th>AV</th>'",          "'    <th title=\"" + T_AV + "\">AV</th>'"),
    ("'    <th>VR</th>'",          "'    <th title=\"" + T_VR + "\">VR</th>'"),
    ("'    <th>AR</th>'",          "'    <th title=\"" + T_AR + "\">AR</th>'"),

    # ── 데이터 셀 ──
    td("'<td class=\"mono-cell\" style=\"text-align:center\">' + (r.mxbg_pallet != null ? r.mxbg_pallet : '-') + '</td>' +", T_MXBG),
    td("'<td class=\"mono-cell\" style=\"text-align:center;color:#22c55e;font-weight:700\">' + availBags + '</td>' +", T_BAG_AV),
    td("'<td class=\"mono-cell\" style=\"text-align:center;color:#3b82f6;font-weight:700\">' + reservedBags + '</td>' +", T_BAG_VR),
    td("'<td class=\"mono-cell\" style=\"text-align:center;color:#f59e0b;font-weight:700\">' + packedBags + '</td>' +", T_BAG_AR),
    td("'<td class=\"mono-cell\" style=\"text-align:center\">' + totalBags + '</td>' +", T_BAG_TOTAL),
    td("'<td class=\"mono-cell\" style=\"text-align:center;font-weight:700\">' + remainBags + '</td>' +", T_BAG_REMAIN),
    td("'<td class=\"mono-cell\" style=\"text-align:right;color:#22c55e;font-weight:700\">' + (availMt ? availMt.toFixed(3) : '0') + '</td>' +", T_AV),
    td("'<td class=\"mono-cell\" style=\"text-align:right;color:#3b82f6;font-weight:700\">' + (reservedMt ? reservedMt.toFixed(3) : '0') + '</td>' +", T_VR),
    td("'<td class=\"mono-cell\" style=\"text-align:right;color:#f59e0b;font-weight:700\">' + (pickedMt ? pickedMt.toFixed(3) : '0') + '</td>' +", T_AR),
]

# ════════════════════════════════════════════════════════════════════
#  sqm-picked.js
# ════════════════════════════════════════════════════════════════════
PICKED = [
    # ── 메인표 헤더 (MXBG~AR 한 줄) ──
    ("<th>MXBG</th><th>Available</th><th>Reserved</th><th>Packed</th>"
     "<th>Total Bags</th><th>Remain Bags</th><th>AV</th><th>VR</th><th>AR</th>",
     "<th title=\"" + T_MXBG + "\">MXBG</th>"
     "<th title=\"" + T_BAG_AV + "\">Available</th>"
     "<th title=\"" + T_BAG_VR + "\">Reserved</th>"
     "<th title=\"" + T_BAG_AR + "\">Packed</th>"
     "<th title=\"" + T_BAG_TOTAL + "\">Total Bags</th>"
     "<th title=\"" + T_BAG_REMAIN + "\">Remain Bags</th>"
     "<th title=\"" + T_AV + "\">AV</th>"
     "<th title=\"" + T_VR + "\">VR</th>"
     "<th title=\"" + T_AR + "\">AR</th>"),

    # ── 그룹표 헤더 ──
    th_styled('text-align:center', 'MXBG', T_MXBG),
    th_styled('text-align:center', 'Available', T_BAG_AV),
    th_styled('text-align:center', 'Reserved', T_BAG_VR),
    th_styled('text-align:center', 'Packed', T_BAG_AR),

    # ── 메인표 데이터 셀 ──
    td("'<td class=\"mono-cell\" style=\"text-align:center\">'+(r.mxbg_pallet!=null?r.mxbg_pallet:'-')+'</td>'", T_MXBG),
    td("'<td class=\"mono-cell\" style=\"text-align:center;color:#22c55e;font-weight:700\">'+availBags+'</td>'", T_BAG_AV),
    td("'<td class=\"mono-cell\" style=\"text-align:center;color:#3b82f6;font-weight:700\">'+reservedBags+'</td>'", T_BAG_VR),
    td("'<td class=\"mono-cell\" style=\"text-align:center;color:#f59e0b;font-weight:700\">'+packedBags+'</td>'", T_BAG_AR),
    td("'<td class=\"mono-cell\" style=\"text-align:center\">'+totalBags+'</td>'", T_BAG_TOTAL),
    td("'<td class=\"mono-cell\" style=\"text-align:center;font-weight:700\">'+remainBags+'</td>'", T_BAG_REMAIN),
    td("'<td class=\"mono-cell\" style=\"text-align:right;color:#22c55e;font-weight:700\">'+(availMt ? availMt.toFixed(3) : '0')+'</td>'", T_AV),
    td("'<td class=\"mono-cell\" style=\"text-align:right;color:#3b82f6;font-weight:700\">'+(reservedMt ? reservedMt.toFixed(3) : '0')+'</td>'", T_VR),
    td("'<td class=\"mono-cell\" style=\"text-align:right;color:#f59e0b;font-weight:700\">'+(pickedMt ? pickedMt.toFixed(3) : '0')+'</td>'", T_AR),

    # ── 그룹표 데이터 셀 ──
    td("'<td class=\"mono-cell\" style=\"text-align:center\">' + (r.mxbg_pallet != null ? r.mxbg_pallet : '-') + '</td>'", T_MXBG),
    td("'<td class=\"mono-cell\" style=\"text-align:center;color:#22c55e;font-weight:700\">' + availBags + '</td>'", T_BAG_AV),
    td("'<td class=\"mono-cell\" style=\"text-align:center;color:#3b82f6;font-weight:700\">' + reservedBags + '</td>'", T_BAG_VR),
    td("'<td class=\"mono-cell\" style=\"text-align:center;color:#f59e0b;font-weight:700\">' + packedBags + '</td>'", T_BAG_AR),
]

TARGETS = [
    ('sqm-inventory.js',  INV),
    ('sqm-allocation.js', ALLOC),
    ('sqm-picked.js',     PICKED),
]


def apply(fname, repls):
    path = os.path.join(JS, fname)
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    orig = content

    # 사전 검증: 모든 old 가 정확히 1회 등장 + title 미부착 확인
    errors = []
    for i, (old, new) in enumerate(repls):
        n = content.count(old)
        if n != 1:
            errors.append('  [%d] 발견 횟수 %d (기대 1):\n      %s' % (i, n, old[:90]))
        if 'title="' in old:
            errors.append('  [%d] old 에 이미 title 존재' % i)
    if errors:
        print('[FAIL] %s — 패턴 불일치:' % fname)
        print('\n'.join(errors))
        return False

    for old, new in repls:
        content = content.replace(old, new, 1)

    if content == orig:
        print('[SKIP] %s — 변경 없음' % fname)
        return True

    ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    bak = path + '.bak_tooltip_' + ts
    with open(bak, 'w', encoding='utf-8') as f:
        f.write(orig)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print('[OK]   %s — %d개 치환  (백업: %s)' % (fname, len(repls), os.path.basename(bak)))
    return True


def main():
    print('=== Avail/Rsv 툴팁 패치 시작 ===')
    ok = True
    for fname, repls in TARGETS:
        if not apply(fname, repls):
            ok = False
    print('=== %s ===' % ('완료' if ok else '실패 (변경 없음 — 위 로그 확인)'))
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
