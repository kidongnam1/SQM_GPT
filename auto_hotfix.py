#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SQM auto_hotfix — pytest 실패 자동 핫픽스. H-7은 진단만."""
import re, sys, sqlite3
from pathlib import Path

PYTEST_OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('pytest_output.txt')
PROD_DB = Path('data/db/sqm_inventory.db')

RULES = {
    'H-1': r'KeyError.*inbound_date|inbound_date.*KeyError',
    'H-2': r'404.*confirm|confirm.*404',
    'H-3': r'NameError.*_db_execute_with_retry',
    'H-4': r'AssertionError.*AVAILABLE|AVAILABLE.*assert',
    'H-5': r'TypeError.*broadcast_event',
    'H-6': r'OperationalError.*port_date|port_date.*no such column',
}

def h7_diagnostic():
    print('[H-7] current_weight 정합성 진단 (READ ONLY)...')
    if not PROD_DB.exists():
        print('[H-7] DB 없음'); return
    try:
        conn = sqlite3.connect(str(PROD_DB))
        rows = conn.execute('''
            SELECT i.lot_no, i.current_weight,
                   COALESCE(SUM(CASE WHEN t.status IN ("AVAILABLE","RESERVED","RETURN") THEN t.weight ELSE 0 END),0) AS calc,
                   COALESCE(SUM(CASE WHEN t.status="PICKED" THEN t.weight ELSE 0 END),0) AS picked
            FROM inventory i LEFT JOIN inventory_tonbag t ON t.lot_no=i.lot_no
            WHERE i.status NOT IN ("SOLD")
            GROUP BY i.lot_no HAVING ABS(i.current_weight - calc) > 0.001
        ''').fetchall()
        conn.close()
        if not rows:
            print('[H-7] 불일치 없음 ✅')
        else:
            print(f'[H-7] 불일치 {len(rows)}건 (수동 확인 필요):')
            for r in rows:
                print(f'  {r[0]}: current={r[1]:.3f} calc={r[2]:.3f} diff={r[1]-r[2]:+.3f} picked={r[3]:.3f}')
    except Exception as e:
        print(f'[H-7] 오류: {e}')

def apply(code):
    if code == 'H-6':
        if not PROD_DB.exists(): return
        try:
            conn = sqlite3.connect(str(PROD_DB))
            conn.execute('ALTER TABLE inventory ADD COLUMN port_date TEXT')
            conn.commit(); conn.close()
            print(f'[{code}] port_date 컬럼 추가 완료')
        except sqlite3.OperationalError as e:
            print(f'[{code}] {"이미 존재" if "duplicate" in str(e).lower() else str(e)}')
    else:
        print(f'[{code}] 수동 확인 필요')

def main():
    if PYTEST_OUT.exists():
        text = PYTEST_OUT.read_text(encoding='utf-8', errors='ignore')
        found = [c for c, p in RULES.items() if re.search(p, text, re.I)]
        if not found:
            print('[auto_hotfix] 자동 처리 가능 패턴 없음')
        for c in found:
            apply(c)
    h7_diagnostic()

if __name__ == '__main__':
    main()
