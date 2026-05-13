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
# 8. 셀 상태 동적 계산 (DB 조회 기반)
# ─────────────────────────────────────────────────────────────────────
#
# 설계 원칙: 별도 cell_state 컬럼/테이블 없이 inventory_tonbag + inventory
#           조회 결과로 셀 상태를 매번 계산. Single Source of Truth.
#
# 셀 상태 판정 로직:
#   1) inventory_tonbag 에서 같은 location 의 활성 톤백 조회
#      (활성 = status IN ('AVAILABLE','PICKED','RESERVED','PENDING'))
#   2) inventory.packing_type 으로 capacity(1 또는 2) 결정
#   3) 활성 톤백 0개 → EMPTY
#      활성 톤백 == capacity → OCCUPIED
#      활성 톤백  < capacity → HALF
#      활성 톤백  > capacity → OVER (이상 상황)
#      packing_type 혼합 → MIXED (이상 상황)
# ─────────────────────────────────────────────────────────────────────

ACTIVE_STATUSES = ('AVAILABLE', 'PICKED', 'RESERVED', 'PENDING')


def _capacity_for(packing_type: str) -> int:
    """packing_type → 셀 최대 톤백 수."""
    spec = PACKING_SPEC.get((packing_type or '').upper())
    return spec['cell_per_pack'] if spec else 1


def get_cell_state(db, location: str) -> Dict:
    """
    특정 셀(location) 의 현재 상태 조회.

    Args:
      db:       SQMDatabase 인스턴스 (execute 메서드 보유)
      location: 위치 문자열 (예: 'G5-04-01-07')

    Returns:
      {
        'location':       str,
        'state':          'EMPTY'|'OCCUPIED'|'HALF'|'OVER'|'MIXED'|'UNKNOWN',
        'active_count':   int,   # 활성 톤백 수
        'capacity':       int,   # 셀 최대 톤백 수
        'packing_type':   str,   # 'A'|'B'|'C'|'' (혼합 시 'MIXED')
        'tonbags':        list,  # 활성 톤백 [{tonbag_uid, lot_no, sub_lt, weight_kg, status}, ...]
        'reason':         str,   # 상태 결정 사유 (디버깅용)
      }
    """
    loc = str(location or '').strip().upper()
    result = {
        'location': loc, 'state': 'UNKNOWN',
        'active_count': 0, 'capacity': 0,
        'packing_type': '', 'tonbags': [],
        'reason': '',
    }
    if not loc:
        result['reason'] = 'location 없음'
        return result

    # 1) 활성 톤백 + LOT 의 packing_type 함께 조회
    sql = """
        SELECT t.id, t.tonbag_uid, t.lot_no, t.sub_lt,
               COALESCE(t.weight_kg, 0) AS weight_kg,
               t.status, COALESCE(i.packing_type, '') AS packing_type
          FROM inventory_tonbag t
          LEFT JOIN inventory i ON i.lot_no = t.lot_no
         WHERE t.location = ?
           AND COALESCE(t.is_sample, 0) = 0
           AND t.status IN ({})
    """.format(','.join('?' * len(ACTIVE_STATUSES)))

    try:
        rows = db.execute(sql, (loc, *ACTIVE_STATUSES)).fetchall()
    except Exception as e:
        result['reason'] = f'DB 조회 실패: {e}'
        return result

    if not rows:
        result['state'] = 'EMPTY'
        result['reason'] = '활성 톤백 없음'
        return result

    # 2) packing_type 일관성 + capacity 결정
    pts = {(r[6] or '').upper() for r in rows}
    pts.discard('')
    if len(pts) > 1:
        result['state']        = 'MIXED'
        result['packing_type'] = 'MIXED'
        result['active_count'] = len(rows)
        result['capacity']     = _capacity_for(next(iter(pts)))
        result['reason']       = f'한 셀에 packing_type 혼합: {pts}'
        result['tonbags']      = [_row_to_tonbag(r) for r in rows]
        return result

    pt = next(iter(pts)) if pts else ''
    capacity = _capacity_for(pt)
    active   = len(rows)

    if active == 0:
        state = 'EMPTY'
    elif active == capacity:
        state = 'OCCUPIED'
    elif active < capacity:
        state = 'HALF'
    else:
        state = 'OVER'

    result.update({
        'state':        state,
        'active_count': active,
        'capacity':     capacity,
        'packing_type': pt,
        'tonbags':      [_row_to_tonbag(r) for r in rows],
        'reason':       f'active={active}, capacity={capacity}, pt={pt!r}',
    })
    return result


def _row_to_tonbag(r) -> Dict:
    return {
        'id':         r[0],
        'tonbag_uid': r[1],
        'lot_no':     r[2],
        'sub_lt':     r[3],
        'weight_kg':  r[4],
        'status':     r[5],
        'packing_type': r[6],
    }


def get_warehouse_summary(db) -> Dict:
    """
    창고 전체 셀 점유 요약 (대시보드용).

    Returns:
      {
        'total_cells':       int,   # 6,572
        'occupied_cells':    int,   # 활성 톤백 있는 셀 수
        'half_cells':        int,
        'over_cells':        int,
        'mixed_cells':       int,
        'empty_cells':       int,   # = total_cells - 위 4개 합
        'occupancy_rate':    float, # (occupied + half) / total
        'active_tonbags':    int,   # 전체 활성 톤백 수
        'total_weight_kg':   float,
        'by_dong':           dict,  # {5: {...}, 6: {...}}
      }
    """
    summary = {
        'total_cells':      WAREHOUSE_TOTAL_CELLS,
        'occupied_cells':   0,
        'half_cells':       0,
        'over_cells':       0,
        'mixed_cells':      0,
        'empty_cells':      WAREHOUSE_TOTAL_CELLS,
        'occupancy_rate':   0.0,
        'active_tonbags':   0,
        'total_weight_kg':  0.0,
        'by_dong':          {5: {'occupied': 0, 'half': 0, 'over': 0, 'mixed': 0},
                             6: {'occupied': 0, 'half': 0, 'over': 0, 'mixed': 0}},
    }

    # location 별 활성 톤백 수 + packing_type 집계
    sql = """
        SELECT t.location,
               COUNT(*) AS active_n,
               SUM(COALESCE(t.weight_kg, 0)) AS sum_w,
               COUNT(DISTINCT COALESCE(i.packing_type, '')) AS pt_kinds,
               MAX(COALESCE(i.packing_type, '')) AS any_pt
          FROM inventory_tonbag t
          LEFT JOIN inventory i ON i.lot_no = t.lot_no
         WHERE t.location IS NOT NULL AND TRIM(t.location) != ''
           AND COALESCE(t.is_sample, 0) = 0
           AND t.status IN ({})
         GROUP BY t.location
    """.format(','.join('?' * len(ACTIVE_STATUSES)))

    try:
        rows = db.execute(sql, ACTIVE_STATUSES).fetchall()
    except Exception as e:
        logger.warning(f'[warehouse_summary] DB 조회 실패: {e}')
        return summary

    for loc, active_n, sum_w, pt_kinds, any_pt in rows:
        summary['active_tonbags']  += int(active_n or 0)
        summary['total_weight_kg'] += float(sum_w or 0)

        v = validate_cell_location(loc)
        dong = v.get('dong') if v.get('ok') else None

        capacity = _capacity_for(any_pt)
        if pt_kinds and pt_kinds > 1:
            state = 'mixed'
        elif active_n == capacity:
            state = 'occupied'
        elif active_n < capacity:
            state = 'half'
        else:
            state = 'over'

        if state == 'occupied': summary['occupied_cells'] += 1
        elif state == 'half':   summary['half_cells']     += 1
        elif state == 'over':   summary['over_cells']     += 1
        elif state == 'mixed':  summary['mixed_cells']    += 1

        if dong in summary['by_dong']:
            summary['by_dong'][dong][state] = summary['by_dong'][dong].get(state, 0) + 1

    used = summary['occupied_cells'] + summary['half_cells'] + summary['over_cells'] + summary['mixed_cells']
    summary['empty_cells']    = max(WAREHOUSE_TOTAL_CELLS - used, 0)
    summary['occupancy_rate'] = round(used / WAREHOUSE_TOTAL_CELLS * 100, 2) if WAREHOUSE_TOTAL_CELLS else 0.0
    return summary


class CellInvariantError(Exception):
    """셀 무결성 위반 — enforce=True 모드에서 트랜잭션 차단용."""
    def __init__(self, location: str, state: str, warnings: list):
        self.location  = location
        self.state     = state
        self.warnings  = warnings
        super().__init__(
            f"[CellInvariant] location={location} state={state} :: " + ' / '.join(warnings)
        )


def check_cell_invariants(db, location: str, enforce: bool = False) -> Dict:
    """
    셀 무결성 체크 (출고/이동/반품/입고 전후 검증용).

    OVER / MIXED 같은 이상 상황을 감지해서 경고 로그 + 결과 반환.

    Args:
      db:        SQMDatabase 인스턴스
      location:  위치 문자열
      enforce:   True 면 위반 발견 시 CellInvariantError 발생 (트랜잭션 차단).
                 False (기본, 비파괴/관찰자 모드) 면 경고 로그만 남기고 결과 반환.

    Returns:
      {'ok': bool, 'state': str, 'warnings': [str, ...], 'detail': dict}

    Raises:
      CellInvariantError: enforce=True 이고 OVER/MIXED 감지 시.

    운영 절차 (권장):
      Phase 1 (1주일): 모든 호출자가 enforce=False (현재) → 경고 로그 수집
      Phase 2:        로그 분석 + 데이터 정리
      Phase 3:        enforce=True 로 전환 (단일 진입점이라 한 줄 변경)
    """
    state = get_cell_state(db, location)
    warnings = []
    ok = True
    if state['state'] == 'OVER':
        warnings.append(
            f"OVER: location={location} 활성 톤백 {state['active_count']}개 > capacity {state['capacity']}"
        )
        ok = False
    elif state['state'] == 'MIXED':
        warnings.append(
            f"MIXED: location={location} packing_type 혼합 — 정책 위반"
        )
        ok = False
    if warnings:
        for w in warnings:
            logger.warning('[cell_invariant] ' + w)
    result = {'ok': ok, 'state': state['state'], 'warnings': warnings, 'detail': state}
    if enforce and not ok:
        raise CellInvariantError(location, state['state'], warnings)
    return result


# ─────────────────────────────────────────────────────────────────────
# 9. 단독 실행 — 셀 수 / 자동 판별 / 위치 검증 테스트
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
    print()

    # v8.6.8: 셀 상태 동적 계산 — In-memory mock DB 로 단독 검증
    print('[셀 상태 동적 계산 테스트]')
    import sqlite3 as _sq
    _con = _sq.connect(':memory:')
    _con.executescript('''
        CREATE TABLE inventory (
            lot_no TEXT PRIMARY KEY, packing_type TEXT DEFAULT ''
        );
        CREATE TABLE inventory_tonbag (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tonbag_uid TEXT, lot_no TEXT, sub_lt INTEGER,
            weight_kg REAL, status TEXT, location TEXT, is_sample INTEGER DEFAULT 0
        );
        INSERT INTO inventory VALUES ('L_A_001', 'A'), ('L_B_001', 'B'), ('L_C_001', 'C');
        -- A: 1pack -> capacity 1, 1톤백 점유 -> OCCUPIED
        INSERT INTO inventory_tonbag (tonbag_uid, lot_no, sub_lt, weight_kg, status, location)
          VALUES ('uid-A1', 'L_A_001', 1, 1000, 'AVAILABLE', 'G5-04-01-07');
        -- C: 2pack -> capacity 2, 2톤백 점유 -> OCCUPIED
        INSERT INTO inventory_tonbag (tonbag_uid, lot_no, sub_lt, weight_kg, status, location)
          VALUES ('uid-C1', 'L_C_001', 1, 500, 'AVAILABLE', 'G5-04-02-07'),
                 ('uid-C2', 'L_C_001', 2, 500, 'AVAILABLE', 'G5-04-02-07');
        -- C: 2pack인데 1톤백만 남음 -> HALF
        INSERT INTO inventory_tonbag (tonbag_uid, lot_no, sub_lt, weight_kg, status, location)
          VALUES ('uid-C3', 'L_C_001', 3, 500, 'AVAILABLE', 'G5-04-03-07'),
                 ('uid-C4', 'L_C_001', 4, 500, 'SOLD',      'G5-04-03-07');
        -- 빈 셀 (톤백 없음) -> EMPTY
        -- B + A 혼합 -> MIXED
        INSERT INTO inventory_tonbag (tonbag_uid, lot_no, sub_lt, weight_kg, status, location)
          VALUES ('uid-B1', 'L_B_001', 1, 500, 'AVAILABLE', 'G5-04-04-07'),
                 ('uid-A2', 'L_A_001', 2, 1000,'AVAILABLE', 'G5-04-04-07');
    ''')
    for loc, expect in [
        ('G5-04-01-07', 'OCCUPIED'),    # A 1pack
        ('G5-04-02-07', 'OCCUPIED'),    # C 2pack full
        ('G5-04-03-07', 'HALF'),         # C 2pack 중 1 남음
        ('G5-04-05-07', 'EMPTY'),        # 비어있음
        ('G5-04-04-07', 'MIXED'),        # 혼합
    ]:
        st = get_cell_state(_con, loc)
        ok = 'OK' if st['state'] == expect else '*MISMATCH*'
        print(f'  {loc} -> state={st["state"]:8s} (active={st["active_count"]}, cap={st["capacity"]}, pt={st["packing_type"]!r}) [{ok}]')
    print()

    print('[창고 요약 (모의 DB)]')
    s = get_warehouse_summary(_con)
    print(f'  total={s["total_cells"]}, occupied={s["occupied_cells"]}, '
          f'half={s["half_cells"]}, mixed={s["mixed_cells"]}, '
          f'empty={s["empty_cells"]}, rate={s["occupancy_rate"]}%')
    print(f'  active_tonbags={s["active_tonbags"]}, '
          f'weight={s["total_weight_kg"]}kg')
    print()

    print('[enforce=False — 비파괴 모드 (현재 운영)]')
    rep = check_cell_invariants(_con, 'G5-04-04-07', enforce=False)
    print(f'  MIXED 셀 검증: ok={rep["ok"]}, warnings={len(rep["warnings"])}건')
    print()

    print('[enforce=True — 강제 차단 모드 테스트]')
    try:
        check_cell_invariants(_con, 'G5-04-04-07', enforce=True)
        print('  *MISMATCH* — 예외가 발생해야 하는데 통과됨')
    except CellInvariantError as e:
        print(f'  CellInvariantError 정상 발생: state={e.state}')
    _con.close()
