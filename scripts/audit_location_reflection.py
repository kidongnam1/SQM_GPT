# -*- coding: utf-8 -*-
"""위치 정보 반영 전수검사 — lot_location_map import 가 어디까지 반영됐나."""
import sqlite3

DB = r'D:\program\SQM_inventory\sqm_v869_clean\data\db\sqm_inventory.db'
con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row

print('=== 1) location 류 컬럼 보유 테이블 전수조사 ===')
for t in con.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"):
    tn = t['name']
    cols = [c['name'] for c in con.execute('PRAGMA table_info(%s)' % tn)]
    loc = [c for c in cols if 'location' in c.lower()
           or c.lower() in ('loc', 'dong', 'rack', 'col', 'level')]
    if loc:
        try:
            cnt = con.execute('SELECT COUNT(*) FROM %s' % tn).fetchone()[0]
        except Exception:
            cnt = '?'
        print('  %-28s 행 %7s | 위치컬럼: %s' % (tn, cnt, loc))

print()
print('=== 2) lot_location_map (위치재고 Import 저장처) ===')
try:
    for r in con.execute('SELECT id, source_file, imported_at, total_lots, '
                          'total_cells FROM lot_location_import_batch '
                          'ORDER BY id DESC LIMIT 5'):
        print('  batch#%s | %s | %s | LOT %s 셀 %s'
              % (r['id'], r['source_file'], r['imported_at'],
                 r['total_lots'], r['total_cells']))
    n = con.execute('SELECT COUNT(*) FROM lot_location_map').fetchone()[0]
    print('  lot_location_map 총 행:', n)
except Exception as e:
    print('  (테이블 없음/오류):', e)

print()
print('=== 3) inventory_tonbag.location 채움 현황 ===')
tot = con.execute('SELECT COUNT(*) FROM inventory_tonbag').fetchone()[0]
filled = con.execute("SELECT COUNT(*) FROM inventory_tonbag "
                     "WHERE location IS NOT NULL AND TRIM(location)<>''").fetchone()[0]
print('  전체 %s / location 채워짐 %s / 빈칸 %s' % (tot, filled, tot - filled))

print()
print('=== 4) inventory.location 채움 현황 ===')
try:
    tot2 = con.execute('SELECT COUNT(*) FROM inventory').fetchone()[0]
    f2 = con.execute("SELECT COUNT(*) FROM inventory "
                     "WHERE location IS NOT NULL AND TRIM(location)<>''").fetchone()[0]
    print('  전체 %s / location 채워짐 %s' % (tot2, f2))
except Exception as e:
    print('  (오류):', e)

print()
print('=== 5) lot_location_map 의 LOT 이 inventory 에 존재하나 ===')
try:
    rows = con.execute(
        'SELECT DISTINCT lot_no FROM lot_location_map').fetchall()
    map_lots = {r['lot_no'] for r in rows}
    inv_lots = {r['lot_no'] for r in con.execute(
        'SELECT DISTINCT lot_no FROM inventory_tonbag')}
    matched = map_lots & inv_lots
    print('  lot_location_map LOT 수:', len(map_lots))
    print('  inventory_tonbag  LOT 수:', len(inv_lots))
    print('  교집합(매칭 가능):', len(matched))
    print('  import 됐지만 재고에 없는 LOT:', len(map_lots - inv_lots))
except Exception as e:
    print('  (오류):', e)

con.close()
