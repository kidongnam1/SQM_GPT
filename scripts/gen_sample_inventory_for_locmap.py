# -*- coding: utf-8 -*-
"""
gen_sample_inventory_for_locmap.py — SQM v8.6.9
================================================
A 작업: 위치재고 Import(lot_location_map)와 LOT이 일치하는 샘플 재고 생성.

절차:
  1) DB 전체 백업 (data/db/sqm_inventory_pre_locmap_sample_<ts>.db)
  2) 재고 상태 파생 샘플 테이블 비우기
       inventory, inventory_tonbag, stock_movement,
       allocation_plan, allocation_import_batch, inventory_snapshot
     (lot_location_map / lot_location_import_batch 는 보존)
  3) lot_location_map 최신 batch 의 LOT 별로
       inventory 1행 + inventory_tonbag 10행 생성
     · 톤백 location 은 비움 — 위치 표시는 C(조회 JOIN)가 담당

작성: Ruby (남기동) / 2026-05-20
"""
import os
import sqlite3
from datetime import datetime

DB = r'D:\program\SQM_inventory\sqm_v869_clean\data\db\sqm_inventory.db'
TODAY = datetime.now().strftime('%Y-%m-%d')
NOW = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
TONBAGS_PER_LOT = 10
TONBAG_WEIGHT = 500.0  # kg, packing_type 'C' (500kg 2pack)

CLEAR_TABLES = [
    'inventory_tonbag',         # 자식 먼저
    'inventory',
    'stock_movement',
    'allocation_plan',
    'allocation_import_batch',
    'inventory_snapshot',
]


def backup_db() -> str:
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    dst = os.path.join(os.path.dirname(DB),
                       'sqm_inventory_pre_locmap_sample_%s.db' % ts)
    src = sqlite3.connect(DB)
    bak = sqlite3.connect(dst)
    with bak:
        src.backup(bak)
    bak.close()
    src.close()
    size = os.path.getsize(dst)
    if size < 1024:
        raise RuntimeError('백업 파일이 너무 작음 — 중단: %s' % dst)
    print('1) 백업 완료: %s (%.1f KB)' % (dst, size / 1024))
    return dst


def main():
    backup_db()

    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    con.execute('PRAGMA foreign_keys=OFF')

    # ── 최신 batch LOT 목록 ──
    batch = con.execute(
        'SELECT id FROM lot_location_import_batch ORDER BY id DESC LIMIT 1'
    ).fetchone()
    if not batch:
        raise RuntimeError('lot_location_import_batch 가 비어있음 — 먼저 위치재고 Import 필요')
    batch_id = batch['id']

    lots = con.execute(
        'SELECT lot_no, '
        '       MAX(product) AS product, '
        '       MAX(shipper) AS shipper, '
        '       MAX(sap_no)  AS sap_no '
        'FROM lot_location_map WHERE batch_id=? '
        'GROUP BY lot_no ORDER BY lot_no',
        (batch_id,),
    ).fetchall()
    print('2) lot_location_map batch#%s — LOT %d개' % (batch_id, len(lots)))

    # ── 비우기 ──
    print('3) 기존 샘플 테이블 비우기:')
    for t in CLEAR_TABLES:
        n = con.execute('SELECT COUNT(*) FROM %s' % t).fetchone()[0]
        con.execute('DELETE FROM %s' % t)
        print('   - %-24s %d행 삭제' % (t, n))

    # ── 생성 ──
    inv_n = tb_n = 0
    for lot in lots:
        lot_no = lot['lot_no']
        product_code = lot['product'] or ''
        sap_no = lot['sap_no'] or ''
        net = TONBAG_WEIGHT * TONBAGS_PER_LOT  # 5000kg

        cur = con.execute(
            'INSERT INTO inventory '
            '(lot_no, product, product_code, sap_no, net_weight, gross_weight, '
            ' initial_weight, current_weight, picked_weight, tonbag_count, '
            ' warehouse, status, stock_date, inbound_date, inbound_type, '
            ' packing_type, created_at, updated_at) '
            'VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
            (lot_no, 'LITHIUM CARBONATE', product_code, sap_no,
             net, net, net, net, 0, TONBAGS_PER_LOT,
             'GY', 'AVAILABLE', TODAY, TODAY, 'DIRECT',
             'C', NOW, NOW),
        )
        inv_id = cur.lastrowid
        inv_n += 1

        for i in range(1, TONBAGS_PER_LOT + 1):
            con.execute(
                'INSERT INTO inventory_tonbag '
                '(inventory_id, lot_no, sap_no, inbound_date, sub_lt, '
                ' tonbag_no, weight, is_sample, status, location, '
                ' created_at, updated_at) '
                'VALUES (?,?,?,?,?,?,?,?,?,?,?,?)',
                (inv_id, lot_no, sap_no, TODAY, i,
                 '%03d' % i, TONBAG_WEIGHT, 0, 'AVAILABLE', None,
                 NOW, NOW),
            )
            tb_n += 1

    con.commit()

    # ── 검증 ──
    inv_chk = con.execute('SELECT COUNT(*) FROM inventory').fetchone()[0]
    tb_chk = con.execute('SELECT COUNT(*) FROM inventory_tonbag').fetchone()[0]
    uid_dup = con.execute(
        'SELECT COUNT(*) FROM (SELECT tonbag_uid FROM inventory_tonbag '
        'GROUP BY tonbag_uid HAVING COUNT(*)>1)'
    ).fetchone()[0]
    matched = con.execute(
        'SELECT COUNT(DISTINCT t.lot_no) FROM inventory_tonbag t '
        'JOIN lot_location_map m ON t.lot_no=m.lot_no'
    ).fetchone()[0]
    con.close()

    print('4) 생성 완료: inventory %d행 / inventory_tonbag %d행' % (inv_n, tb_n))
    print('5) 검증:')
    print('   - inventory 행수      : %d' % inv_chk)
    print('   - inventory_tonbag 행수: %d' % tb_chk)
    print('   - tonbag_uid 중복     : %d (0 이어야 정상)' % uid_dup)
    print('   - 위치맵과 매칭되는 LOT: %d / %d' % (matched, len(lots)))
    if uid_dup == 0 and matched == len(lots):
        print('   ✅ A 작업 정상 완료')
    else:
        print('   ⚠️ 확인 필요')


if __name__ == '__main__':
    main()
