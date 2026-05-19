# -*- coding: utf-8 -*-
"""위치재고조회 엑셀 import 기능 검증 (1회성 테스트, 실DB 미사용).

location_map_api.py 는 importlib 로 단독 로드 — backend/api/__init__.py
(엔진 전체 초기화)를 트리거하지 않도록 우회한다.
"""
import sys, os, tempfile, sqlite3, copy, logging, importlib.util

sys.stdout.reconfigure(encoding='utf-8')
logging.disable(logging.CRITICAL)  # 엔진/파서 로그 소음 제거

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from features.parsers.location_inventory_parser import parse_location_inventory_excel

# location_map_api 단독 로드 (backend.api 패키지 __init__ 회피)
_spec = importlib.util.spec_from_file_location(
    'location_map_api_standalone',
    os.path.join(ROOT, 'backend', 'api', 'location_map_api.py'))
lma = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(lma)
_ensure_tables, _build_report = lma._ensure_tables, lma._build_report

XLSX = r'D:\program\SQM_inventory\위치재고조회_20260518_140004.xlsx'


def commit_to_db(con, doc, source):
    """commit 엔드포인트의 INSERT 로직 복제 (테스트용)."""
    from datetime import datetime
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    st = doc['stats']
    cur = con.execute(
        'INSERT INTO lot_location_import_batch '
        '(source_file,imported_at,total_lots,total_cells,total_tonbags,warning_count,note) '
        'VALUES (?,?,?,?,?,?,?)',
        (source, now, st['total_lots'], st['total_cells'], st['total_tonbags'],
         st['warning_count'], ''))
    bid = cur.lastrowid
    for lot in doc['lots']:
        for c in lot['cells']:
            if not c['valid']:
                continue
            con.execute(
                'INSERT INTO lot_location_map '
                '(batch_id,lot_no,location,dong,rack,col,level,tonbag_count,'
                ' product,shipper,sap_no,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)',
                (bid, lot['lot_no'], c['location'], c['dong'], c['rack'], c['col'],
                 c['level'], c['tonbag_count'], lot['product'], lot['shipper'],
                 lot['sap_no'], now))
    con.commit()
    return bid


print('=== 1. 파싱 ===')
doc = parse_location_inventory_excel(XLSX)
print('  ok:', doc['ok'], '| stats:', doc['stats'])
print('  errors:', len(doc['errors']), '| warnings:', len(doc['warnings']))
for w in doc['warnings'][:5]:
    print('   warn:', w)
for e in doc['errors'][:5]:
    print('   err :', e)

tmpdb = tempfile.NamedTemporaryFile(suffix='.db', delete=False).name
con = sqlite3.connect(tmpdb)
con.row_factory = sqlite3.Row
_ensure_tables(con)

print()
print('=== 2. 최초 import preview (직전 batch 없음) ===')
rep = _build_report(doc, con)
print('  can_commit:', rep['can_commit'], '| has_inbound_short:', rep['has_inbound_short'])
print('  diff: 신규 %d / 삭제 %d / 위치변경 %d / 수량변경 %d / 동일 %d' % (
    len(rep['diff']['new_lots']), len(rep['diff']['removed_lots']),
    len(rep['diff']['location_changed']), len(rep['diff']['count_changed']),
    rep['diff']['unchanged_count']))
print('  입고누락(inbound_short):', len(rep['inbound_short']), '건')
for s in rep['inbound_short']:
    mc = ', '.join('%s(%d개)' % (m['location'], m['tonbag_count']) for m in s['missing_cells'])
    print('   LOT %s 행%d: 톤백 %d/%d → 누락셀: %s' % (
        s['lot_no'], s['row_num'], s['tonbag_sum'], s['expected'], mc))

print()
print('=== 3. commit (temp DB) → batch 저장 ===')
bid = commit_to_db(con, doc, '위치재고조회_20260518_140004.xlsx')
n = con.execute('SELECT COUNT(*) FROM lot_location_map WHERE batch_id=?', (bid,)).fetchone()[0]
print('  batch_id:', bid, '| 저장된 매핑 행:', n)

print()
print('=== 4. 동일 파일 재import preview (diff = 변화 없음 기대) ===')
doc2 = parse_location_inventory_excel(XLSX)
rep2 = _build_report(doc2, con)
print('  diff: 신규 %d / 삭제 %d / 위치변경 %d / 수량변경 %d / 동일 %d' % (
    len(rep2['diff']['new_lots']), len(rep2['diff']['removed_lots']),
    len(rep2['diff']['location_changed']), len(rep2['diff']['count_changed']),
    rep2['diff']['unchanged_count']))
print('  inbound_short:', len(rep2['inbound_short']), '(기존 LOT이므로 0 기대)')

print()
print('=== 5. 변경 시뮬레이션 (한 LOT 톤백수 변경 + 한 LOT 삭제) ===')
doc3 = copy.deepcopy(doc)
ch_lot = doc3['lots'][0]['lot_no']
doc3['lots'][0]['cells'][0]['tonbag_count'] = 1   # [2]→[1] 출고 시뮬
rm_lot = doc3['lots'][-1]['lot_no']
doc3['lots'] = doc3['lots'][:-1]                  # 마지막 LOT 삭제
rep3 = _build_report(doc3, con)
print('  변경LOT=%s, 삭제LOT=%s' % (ch_lot, rm_lot))
print('  diff: 신규 %d / 삭제 %d / 위치변경 %d / 수량변경 %d / 동일 %d' % (
    len(rep3['diff']['new_lots']), len(rep3['diff']['removed_lots']),
    len(rep3['diff']['location_changed']), len(rep3['diff']['count_changed']),
    rep3['diff']['unchanged_count']))
print('  수량변경 상세:', [c['lot_no'] for c in rep3['diff']['count_changed']])
print('  삭제 상세:', rep3['diff']['removed_lots'])

con.close()
os.unlink(tmpdb)
print()
print('=== 테스트 완료 ===')
