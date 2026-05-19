# -*- coding: utf-8 -*-
"""
gen_test_picking_pdf.py
-----------------------
가상(테스트용) Picking List PDF 생성.

요건:
  - 현재 RESERVED 68개 LOT 전부 대상
  - 각 LOT RESERVED 톤백의 절반((R+1)//2)을 피킹 → Quantity N MT 라인
  - LOT마다 샘플 라인 1줄 (Quantity 1.00 KG)
  - SOLD TO / 고객 = PT LBM

PDF 형식: features/parsers/picking_list_parser.py 의 정규식이 인식하는 텍스트 라인.
  헤더 : Outbound ID / Sales order / Customer reference / Invoice account /
         Creation Date / Plan Loading Date / big bag 500 kgs
  배치 : "Quantity: N.NN MT Batch number: <lot> Storage location: 1001 GY logistics"
         "Quantity: 1.00 KG Batch number: <lot> Storage location: 1001 GY logistics"
"""
import os
import sys
import sqlite3

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DB_PATH = os.path.join(ROOT, 'data', 'db', 'sqm_inventory.db')
OUT_PATH = os.path.join(ROOT, 'test_picking_list_20260518.pdf')

TONBAG_MT = 0.5          # 정규 톤백 1개 = 0.5 MT
STORAGE = '1001 GY logistics'


def reserved_counts():
    db = sqlite3.connect(DB_PATH)
    rows = db.execute(
        "SELECT lot_no, COUNT(*) FROM inventory_tonbag "
        "WHERE status='RESERVED' AND COALESCE(is_sample,0)=0 "
        "GROUP BY lot_no ORDER BY lot_no"
    ).fetchall()
    db.close()
    return rows


def main():
    lots = reserved_counts()
    if not lots:
        print('[FAIL] RESERVED 톤백이 없습니다.')
        return

    lines = [
        'PICKING LIST',
        'Outbound ID: 80100501',
        'Sales order: 80007501',
        'Customer reference: PTLBM-PICK-2606',
        'Invoice account     PT LBM',
        'Creation Date: 18.05.2026',
        'Plan Loading Date: 25.05.2026',
        'Delivery terms: CIF Busan',
        'big bag 500 kgs net',
        '',
    ]
    total_picked_tb = 0
    total_mt = 0.0
    for lot_no, r in lots:
        picked = (r + 1) // 2          # RESERVED의 절반(반올림)
        mt = round(picked * TONBAG_MT, 2)
        total_picked_tb += picked
        total_mt += mt
        lines.append(
            f'Quantity: {mt:.2f} MT Batch number: {lot_no} '
            f'Storage location: {STORAGE}'
        )
        lines.append(
            f'Quantity: 1.00 KG Batch number: {lot_no} '
            f'Storage location: {STORAGE}'
        )

    # ── PDF 출력 (Courier 고정폭, 라인당 drawString 1회) ──
    c = canvas.Canvas(OUT_PATH, pagesize=A4)
    width, height = A4
    x, lh = 40, 11
    y = height - 50
    c.setFont('Courier', 9)
    for ln in lines:
        if y < 45:
            c.showPage()
            c.setFont('Courier', 9)
            y = height - 50
        if ln:
            c.drawString(x, y, ln)
        y -= lh
    c.save()

    print('=== Picking List PDF 생성 완료 ===')
    print(f'  파일       : {OUT_PATH}')
    print(f'  LOT 수     : {len(lots)}개 (RESERVED 전부)')
    print(f'  피킹 톤백  : {total_picked_tb}개 (LOT당 RESERVED의 절반)')
    print(f'  본품 합계  : {round(total_mt,2)} MT')
    print(f'  샘플 라인  : {len(lots)}줄 (각 1.00 KG)')
    print(f'  Picking No : PTLBM-PICK-2606  /  고객: PT LBM')


if __name__ == '__main__':
    main()
