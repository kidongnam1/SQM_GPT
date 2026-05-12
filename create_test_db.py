#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SQM 테스트 전용 DB 생성. 실행: python create_test_db.py"""
import shutil, sqlite3, sys
from pathlib import Path

PROD_DB = Path('data/db/sqm_inventory.db')
TEST_DB = Path('data/db/sqm_inventory_test.db')

def main():
    if not PROD_DB.exists():
        print(f'[ERROR] 운영 DB 없음: {PROD_DB}')
        sys.exit(1)
    TEST_DB.parent.mkdir(parents=True, exist_ok=True)
    if TEST_DB.exists():
        shutil.copy2(TEST_DB, str(TEST_DB) + '.bak')
        print(f'[INFO] 기존 백업: {TEST_DB}.bak')
    src = sqlite3.connect(str(PROD_DB))
    dst = sqlite3.connect(str(TEST_DB))
    try:
        schema = '\n'.join(
            r[0] for r in src.execute(
                "SELECT sql FROM sqlite_master WHERE sql IS NOT NULL "
                "AND type IN ('table','index','trigger','view') ORDER BY rootpage"
            )
        )
        dst.executescript(schema)
        dst.commit()
        cnt = dst.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'").fetchone()[0]
        print(f'[OK] 테스트 DB 생성 완료: {TEST_DB} (테이블 {cnt}개)')
    finally:
        src.close(); dst.close()

if __name__ == '__main__':
    main()
