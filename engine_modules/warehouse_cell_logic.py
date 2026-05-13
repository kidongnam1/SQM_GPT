# -*- coding: utf-8 -*-
"""
SQM 창고 셀 점유 / 출고 케이스 분류 로직
==========================================

v8.6.8 — 광양 GY Logis 창고 규칙 확정판

핵심 데이터:
  - 컨테이너: 20ft (99.9%) / 40ft, 최대 20,000kg
  - 팔레트:   1팔레트 = 1톤 = 셀 1개
              · 1,000kg 1pack → 1팔레트 = 톤백 1개 (셀당 톤백 1)
              ·  500kg  2pack → 1팔레트 = 톤백 2개 (셀당 톤백 2)
              ·  500kg  1pack → 1팔레트 = 톤백 1개 (특수, 셀당 톤백 1)
  - LOT 셀 점유:
              · 1,000kg 1pack, mxbg=10 → 셀 10개
              ·   500kg 2pack, mxbg=10 → 셀  5개
              ·   500kg 1pack, mxbg=10 → 셀 10개 (특수)

랙 이름 규칙 (v8.6.8 확정):
  형식: G{동}-{칸}-{열}-{층}
    동:   5 | 6
    칸:   01~16
    열:   01~31
    층:   01~07 (랙별 가변)
          · 1~3랙   → 6층
          · 4~13랙  → 7층
          · 14~16랙 → 6층
  예: G5-04-01-07 = 5동 4번랙 1열 7층
      G5-16-31-06 = 5동 16번랙 31열 6층

총 셀 수:
  동당 = 3×31×6 + 10×31×7 + 3×31×6 = 3,286
  전체 = 5동 + 6동 = 6,572

출고 케이스:
  CASE 1: TYPE A 또는 B (1팔레트 1톤백) — 셀 통째 출고
  CASE 2: TYPE C 정상 출고 (2팩 동시) — 셀 통째 출고
  CASE 3: TYPE C 부분 출고 (1팩만)    — 잔여 1톤백 처리 분기 필요
            ├─ STAY: 원위치 유지 (HALF 상태)
            └─ MOVE: 다른 셀로 이동

작성자: Ruby (남기동)
버전: v8.6.8 (2026-05-13)
"""

from typing import Dict, List, Optional, Tuple
import re
import logging

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────
# 1. 창고 상수
# ─────────────────────────────────────────────────────────────────────
CONTAINER_MAX_KG = 20_000           # 20ft / 40ft 공통

WAREHOUSE_DONGS = (5, 6)            # 동 번호
RACK_RANGE      = (1, 16)            # 칸(랙) 번호 범위
COL_RANGE       = (1, 31)            # 열 범위
LEVEL_BY_RACK   = {
    # rack 번호 → 최대 층
    **{r: 6 for r in range(1, 4)},     # 1~3랙
    **{r: 7 for r in range(4, 14)},    # 4~13랙
    **{r: 6 for r in range(14, 17)},   # 14~16랙
}


def total_cells() -> int:
    """창고 전체 셀 수 계산."""
    per_dong = sum(31 * lv for lv in LEVEL_BY_RACK.values())   # 각 랙의 (열 × 층) 합
    return per_dong * len(WAREHOUSE_DONGS)


WAREHOUSE_TOTAL_CELLS = total_cells()    # 6,572


# ─────────────────────────────────────────────────────────────────────
# 2. Packing Type
# ─────────────────────────────────────────────────────────────────────
class PackingType:
    A = 'A'    # 1,000kg 1pack — 셀당 톤백 1
    B = 'B'    #   500kg 1pack — 셀당 톤백 1 (특수)
    C = 'C'    #   500kg 2pack — 셀당 톤백 2


PACKING_SPEC = {
    PackingType.A: {'unit_kg': 1000, 'cell_per_pack': 1, 'label': '1,000kg 1pack'},
    PackingType.B: {'unit_kg':  500, 'cell_per_pack': 1, 'label':   '500kg 1pack (특수)'},
    PackingType.C: {'unit_kg':  500, 'cell_per_pack': 2, 'label':   '500kg 2pack'},
}

UNIT_KG_TOLERANCE = 50    # ±50kg


def determine_packing_type(net_kg: float, mxbg: int) -> Dict:
    """
    PL 파싱 결과로부터 packing_type 자동 판별.

    Returns:
      {
        'type':       'A' | 'B' | 'C' | None,
        'unit_kg':    float,
        'confidence': 'high' | 'low' | 'unknown'
      }

    Note:
      - 500kg 자동 판별 결과는 'C(2pack)' 추정 (기본) — confidence='low'
      - 'B(500kg 1pack 특수)' 는 net_kg/mxbg 만으로 판별 불가 → 사용자 확인 필수
    """
    try:
        nk = float(net_kg or 0)
        mb = int(mxbg or 0)
    except (TypeError, ValueError):
        return {'type': None, 'unit_kg': 0.0, 'confidence': 'unknown'}

    if nk <= 0 or mb <= 0:
        return {'type': None, 'unit_kg': 0.0, 'confidence': 'unknown'}

    unit_kg = nk / mb

    if abs(unit_kg - 1000) <= UNIT_KG_TOLERANCE:
        return {'type': PackingType.A, 'unit_kg': unit_kg, 'confidence': 'high'}
    if abs(unit_kg -  500) <= UNIT_KG_TOLERANCE:
        return {'type': PackingType.C, 'unit_kg': unit_kg, 'confidence': 'low'}
    return {'type': None, 'unit_kg': unit_kg, 'confidence': 'unknown'}


# ─────────────────────────────────────────────────────────────────────
# 3. 셀 점유 계산
# ─────────────────────────────────────────────────────────────────────
def calc_cell_occupancy(packing_type: str, mxbg: int) -> Dict:
    """LOT 한 건이 차지하는 셀 / 팔레트 수 계산."""
    spec = PACKING_SPEC.get(packing_type)
    try:
        mb = int(mxbg or 0)
    except (TypeError, ValueError):
        mb = 0
    if not spec or mb <= 0:
        return {'cells': 0, 'pallets': 0}
    cells = -(-mb // spec['cell_per_pack'])    # 올림 나눗셈
    return {'cells': cells, 'pallets': cells}


def calc_container_capacity(packing_type: str, mxbg_per_lot: int) -> int:
    """컨테이너 1대(20톤)에 적재 가능한 LOT 수."""
    spec = PACKING_SPEC.get(packing_type)
    try:
        mb = int(mxbg_per_lot or 0)
    except (TypeError, ValueError):
        mb = 0
    if not spec or mb <= 0:
        return 0
    lot_weight = spec['unit_kg'] * mb
    if lot_weight <= 0:
        return 0
    return CONTAINER_MAX_KG // lot_weight


# ─────────────────────────────────────────────────────────────────────
# 4. 랙 위치(Cell) 검증
# ─────────────────────────────────────────────────────────────────────
CELL_RE = re.compile(r'^G([56])-(\d{2})-(\d{2})-(\d{2})$')


def max_level_for_rack(rack_no: int) -> int:
    """주어진 랙 번호의 최대 층."""
    return LEVEL_BY_RACK.get(int(rack_no or 0), 0)


def validate_cell_location(loc: str) -> Dict:
    """
    창고 위치 형식 검증.

    Returns:
      {ok: bool, dong, rack, col, level, reason?}
    """
    s = str(loc or '').strip().upper()
    m = CELL_RE.match(s)
    if not m:
        return {'ok': False, 'reason': '형식 오류 (예: G5-04-01-07)'}

    dong  = int(m.group(1))
    rack  = int(m.group(2))
    col   = int(m.group(3))
    level = int(m.group(4))

    if dong not in WAREHOUSE_DONGS:
        return {'ok': False, 'reason': '동은 5 또는 6만 허용'}
    if not (RACK_RANGE[0] <= rack <= RACK_RANGE[1]):
        return {'ok': False, 'reason': f'칸(랙)은 {RACK_RANGE[0]:02d}~{RACK_RANGE[1]:02d}'}
    if not (COL_RANGE[0] <= col <= COL_RANGE[1]):
        return {'ok': False, 'reason': f'열은 {COL_RANGE[0]:02d}~{COL_RANGE[1]:02d}'}

    max_lv = max_level_for_rack(rack)
    if not (1 <= level <= max_lv):
        return {'ok': False, 'reason': f'층은 01~{max_lv:02d} (랙 {rack}번 기준)'}

    return {'ok': True, 'dong': dong, 'rack': rack, 'col': col, 'level': level}


def format_cell_location(dong: int, rack: int, col: int, level: int) -> str:
    """4-tuple → G5-04-01-07 형식 문자열."""
    return f'G{dong}-{rack:02d}-{col:02d}-{level:02d}'


# ─────────────────────────────────────────────────────────────────────
# 5. 셀 상태 enum
# ─────────────────────────────────────────────────────────────────────
class CellState:
    EMPTY    = 'EMPTY'      # 빈 셀
    OCCUPIED = 'OCCUPIED'   # 정상 점유 (1pack 또는 2pack 가득)
    HALF     = 'HALF'       # 반점유 (TYPE C 부분 출고 잔여)
    SOLD     = 'SOLD'       # 출고 완료 → 곧 EMPTY


# ─────────────────────────────────────────────────────────────────────
# 6. 출고 케이스 분류
# ─────────────────────────────────────────────────────────────────────
class PickCase:
    CASE_1 = 'CASE_1'   # TYPE A/B — 1pack 통째 출고 → 셀 비움
    CASE_2 = 'CASE_2'   # TYPE C  — 2pack 동시 출고 → 셀 비움
    CASE_3 = 'CASE_3'   # TYPE C  — 2pack 중 1pack 부분 출고 → 잔여 처리 분기


def classify_pick_case(packing_type: str, scanned_count: int,
                       cell_pack_count: int = None) -> str:
    """
    출고 케이스 분류.

    Args:
      packing_type:    'A' | 'B' | 'C'
      scanned_count:   바코드 스캔 수 (팔레트 단위)
      cell_pack_count: 해당 셀의 현재 톤백 수 (None 이면 packing_type 기본값 사용)

    Returns:
      'CASE_1' | 'CASE_2' | 'CASE_3' | ''  (불명)
    """
    spec = PACKING_SPEC.get(packing_type)
    if not spec:
        return ''
    expected = spec['cell_per_pack']    # A/B=1, C=2
    if cell_pack_count is None:
        cell_pack_count = expected

    sc = max(int(scanned_count or 0), 0)
    if sc <= 0:
        return ''

    if packing_type in (PackingType.A, PackingType.B):
        return PickCase.CASE_1

    # TYPE C
    if sc >= cell_pack_count:
        return PickCase.CASE_2    # 2팩 동시
    return PickCase.CASE_3        # 1팩만 → 잔여 처리 필요


class PickResolution:
    """CASE 3 잔여 톤백 처리 분기."""
    STAY = 'STAY'   # 원위치 유지 (셀 → HALF 상태)
    MOVE = 'MOVE'   # 다른 셀로 이동


# ─────────────────────────────────────────────────────────────────────
# 7. 헬퍼: LOT row → 셀 점유 요약
# ─────────────────────────────────────────────────────────────────────
def summarize_lot(packing_type: str, net_kg: float, mxbg: int) -> Dict:
    """
    LOT 한 건의 셀 점유 / 컨테이너 수 / 자동판별 결과 통합 요약.

    Returns:
      {
        type, unit_kg, confidence,
        cells, pallets,
        lot_kg, lots_per_container, container_count_for_1lot,
      }
    """
    det = determine_packing_type(net_kg, mxbg) if not packing_type else \
          {'type': packing_type, 'unit_kg': (PACKING_SPEC.get(packing_type) or {}).get('unit_kg', 0),
           'confidence': 'user'}
    pt = packing_type or det['type']
    occ = calc_cell_occupancy(pt, mxbg) if pt else {'cells': 0, 'pallets': 0}
    cap = calc_container_capacity(pt, mxbg) if pt else 0
    try:
        mb = int(mxbg or 0)
    except (TypeError, ValueError):
        mb = 0
    lot_kg = (PACKING_SPEC.get(pt) or {}).get('unit_kg', 0) * mb if pt else 0.0
    return {
        'type':                     pt,
        'unit_kg':                  det.get('unit_kg', 0),
        'confidence':               det.get('confidence', 'unknown'),
        'cells':                    occ['cells'],
        'pallets':                  occ['pallets'],
        'lot_kg':                   lot_kg,
        'lots_per_container':       cap,
        'container_count_for_1lot': 1 if cap > 0 else 0,
    }


# ─────────────────────────────────────────────────────────────────────
# 8. 단독 실행 — 셀 수 / 자동 판별 / 위치 검증 테스트
# ─────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    print('[GY Logis 창고 셀 수]')
    print(f'  동당: {WAREHOUSE_TOTAL_CELLS // len(WAREHOUSE_DONGS)} 셀')
    print(f'  전체: {WAREHOUSE_TOTAL_CELLS} 셀')
    print()

    print('[자동 판별 테스트]')
    for net, mb, desc in [
        (10_000, 10, '1,000kg × 10  → A'),
        ( 5_000, 10,   '500kg × 10  → C'),
        ( 5_000, 20,   '500kg × 20  → 1pack(B) 특수, 자동은 C 추정'),
        (   100,  1, '비정상'),
    ]:
        r = determine_packing_type(net, mb)
        print(f'  {desc:40s} → {r}')
    print()

    print('[셀 점유 테스트]')
    for pt, mb in [('A', 10), ('B', 10), ('C', 10), ('A', 20)]:
        occ = calc_cell_occupancy(pt, mb)
        print(f'  {pt} × mxbg={mb:>3d} → 셀 {occ["cells"]} 개')
    print()

    print('[위치 검증 테스트]')
    for loc, expect_ok in [
        ('G5-04-01-07', True),     # 4 rack (max 7) col 1 lv 7 — OK
        ('G5-16-31-06', True),     # 16 rack (max 6) col 31 lv 6 — OK
        ('G5-01-01-07', False),    # 1 rack (max 6) but lv 7 — NG
        ('G7-01-01-01', False),    # dong 7 not exist — NG
        ('A-01-01-10',  False),    # old format — NG
        ('G6-13-31-07', True),     # 13 rack (max 7) — OK
    ]:
        r = validate_cell_location(loc)
        ok = 'OK' if r['ok'] == expect_ok else '*MISMATCH*'
        print(f'  {loc:14s} -> {r}  [{ok}]')
