# -*- coding: utf-8 -*-
"""
analyze_locations.py
====================

위치 형식 분포 분석 CLI 도구 — v8.6.8 마이그레이션 사전 점검용.

사용:
  cd D:/program/SQM_inventory/SQM_v868_claan
  python -X utf8 scripts/analyze_locations.py
  python -X utf8 scripts/analyze_locations.py --db custom.db
  python -X utf8 scripts/analyze_locations.py --samples 20

옛/신/EMPTY/INVALID 분류 카운트 + 옛 형식 샘플 목록 출력.
"""
import sys
import os
import argparse
import sqlite3

# 프로젝트 루트를 path에 추가
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)


def _default_db_path():
    """SQM 기본 DB 경로 — backend/api/scan_api.py 패턴과 동일."""
    p = os.path.join(ROOT, 'data', 'db', 'sqm_inventory.db')
    return p if os.path.exists(p) else None


def main():
    ap = argparse.ArgumentParser(description='SQM 위치 형식 분포 분석')
    ap.add_argument('--db',      default=None, help='DB 경로 (기본: data/db/sqm_inventory.db)')
    ap.add_argument('--samples', type=int, default=10, help='형식별 샘플 개수 (기본 10)')
    args = ap.parse_args()

    db_path = args.db or _default_db_path()
    if not db_path or not os.path.exists(db_path):
        print(f'❌ DB 파일 없음: {db_path}')
        sys.exit(1)

    from engine_modules.warehouse_cell_logic import analyze_location_formats

    print(f'📂 DB: {db_path}')
    print()
    con = sqlite3.connect(db_path)
    try:
        res = analyze_location_formats(con, sample_per_kind=args.samples)
    finally:
        con.close()

    def _print_kind_table(title, sec):
        print(f'─── {title} ─── (총 {sec["total"]:,}건)')
        kinds = ['NEW', 'OLD_3', 'OLD_4', 'EMPTY', 'INVALID']
        total = sec['total'] or 1
        for k in kinds:
            n = sec['by_kind'].get(k, 0)
            pct = (n / total * 100)
            bar = '█' * int(pct / 2)   # 0~50칸
            print(f'  {k:8s} {n:>6,} 건  {pct:5.1f}% {bar}')
        print()
        if sec['samples']:
            print('  샘플 (옛/INVALID):')
            for k, lst in sec['samples'].items():
                if not lst:
                    continue
                print(f'    {k}:')
                for s in lst:
                    print(f'      · {s}')
            print()

    _print_kind_table('inventory_tonbag', res['tonbag'])
    _print_kind_table('inventory',         res['inventory'])

    print(f'═══ unique 옛 형식 위치: {res["distinct_old_locations"]:,} 개')
    if res['distinct_old_examples']:
        print('   (최대 50개 미리보기)')
        for s in res['distinct_old_examples']:
            print(f'     · {s}')
    print()

    # 활성 톤백 중 옛 형식 (마이그레이션 시급도 지표)
    inv_st = res['tonbag'].get('invalid_status_breakdown', {})
    if inv_st:
        print('⚠️ 옛 형식 위치를 가진 활성/이력 톤백 status 분포:')
        for st, n in sorted(inv_st.items()):
            print(f'    {st:12s} {n:>5,} 건')
        print()

    # 권고
    tb_old = res['tonbag']['by_kind'].get('OLD_3', 0) + res['tonbag']['by_kind'].get('OLD_4', 0)
    tb_new = res['tonbag']['by_kind'].get('NEW', 0)
    tb_empty = res['tonbag']['by_kind'].get('EMPTY', 0)
    print('─── 마이그레이션 권고 ───')
    if tb_old == 0:
        print('  ✅ 옛 형식 데이터 없음 — 마이그레이션 불필요')
    elif tb_old < 50:
        print(f'  🟡 옛 형식 {tb_old}건 — 수동 매핑(엑셀 업로드 또는 직접 입력)으로 처리 가능')
    elif tb_old < 500:
        print(f'  🟠 옛 형식 {tb_old}건 — CSV 매핑표 + 일괄 UPDATE 스크립트 권장')
    else:
        print(f'  🔴 옛 형식 {tb_old}건 — 대규모 마이그레이션 필요, 전담 작업 권장')
    print(f'  (NEW: {tb_new}, EMPTY: {tb_empty}, OLD: {tb_old})')


if __name__ == '__main__':
    main()
