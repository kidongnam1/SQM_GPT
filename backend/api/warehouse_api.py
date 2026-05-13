# -*- coding: utf-8 -*-
"""
SQM Warehouse API — 셀 상태 / 창고 점유 요약
=============================================

v8.6.8 — 창고 셀 상태 조회 (동적 계산 기반)

엔드포인트:
  GET /api/warehouse/cell-state?location=G5-04-01-07
      → 특정 셀의 EMPTY/OCCUPIED/HALF 상태 + 활성 톤백 목록
  GET /api/warehouse/summary
      → 창고 전체 셀 점유 요약 (대시보드용)
  GET /api/warehouse/validate-location?location=G5-04-01-07
      → 위치 형식 검증 (G{동}-{칸}-{열}-{층})
  GET /api/warehouse/cell-grid?dong=5&rack=4
      → 동·랙 평면 그리드

응답 포맷: 기존 SQM 컨벤션 (ok_response/err_response) 사용

작성자: Ruby (남기동)
버전: v8.6.8 (2026-05-13)
"""
from fastapi import APIRouter, HTTPException, Query
from datetime import datetime
import sqlite3
import logging

from backend.common.errors import ok_response, err_response

logger = logging.getLogger(__name__)
router = APIRouter(prefix='/api/warehouse', tags=['warehouse'])


def _db():
    """SQLite 연결 — 다른 API와 동일한 DB_PATH 사용."""
    from config import DB_PATH
    con = sqlite3.connect(str(DB_PATH))
    con.row_factory = sqlite3.Row
    return con


# ─────────────────────────────────────────────────────────────────────
# GET /api/warehouse/validate-location
# ─────────────────────────────────────────────────────────────────────
@router.get('/validate-location', summary='📍 위치 형식 검증')
def api_validate_location(location: str = Query(..., description='G5-04-01-07 형식')):
    """랙 위치 문자열을 검증."""
    try:
        from engine_modules.warehouse_cell_logic import validate_cell_location
        return ok_response(validate_cell_location(location))
    except Exception as e:
        logger.error('validate-location error: %s', e)
        return err_response(str(e))


# ─────────────────────────────────────────────────────────────────────
# GET /api/warehouse/cell-state
# ─────────────────────────────────────────────────────────────────────
@router.get('/cell-state', summary='🔍 특정 셀 상태 조회')
def api_cell_state(location: str = Query(..., description='G5-04-01-07 형식')):
    """
    한 셀의 현재 상태 (EMPTY/OCCUPIED/HALF/OVER/MIXED) 와
    그 셀에 있는 활성 톤백 목록을 반환.
    """
    try:
        from engine_modules.warehouse_cell_logic import (
            validate_cell_location, get_cell_state,
        )
        v = validate_cell_location(location)
        if not v.get('ok'):
            return err_response(v.get('reason') or '위치 형식 오류', detail=v)
        con = _db()
        try:
            state = get_cell_state(con, location)
        finally:
            con.close()
        state['validation'] = v
        return ok_response(state)
    except Exception as e:
        logger.error('cell-state error: %s', e)
        return err_response(str(e))


# ─────────────────────────────────────────────────────────────────────
# GET /api/warehouse/summary
# ─────────────────────────────────────────────────────────────────────
@router.get('/summary', summary='📊 창고 점유 요약')
def api_warehouse_summary():
    """대시보드용 셀 점유 요약 (5동/6동, EMPTY/OCCUPIED/HALF/...)."""
    try:
        from engine_modules.warehouse_cell_logic import (
            get_warehouse_summary, WAREHOUSE_TOTAL_CELLS,
        )
        con = _db()
        try:
            s = get_warehouse_summary(con)
        finally:
            con.close()
        s['total_cells_expected'] = WAREHOUSE_TOTAL_CELLS
        return ok_response(s)
    except Exception as e:
        logger.error('summary error: %s', e)
        return err_response(str(e))


# ─────────────────────────────────────────────────────────────────────
# GET /api/warehouse/cell-grid
# ─────────────────────────────────────────────────────────────────────
@router.get('/cell-grid', summary='🧱 동/랙 평면 그리드')
def api_cell_grid(dong: int = Query(..., description='5 또는 6'),
                  rack: int = Query(..., description='1~16')):
    """
    동·랙 별 (열 × 층) 격자 — 평면도/대시보드용.
    각 셀에 대해 state, active_count, capacity 만 가벼운 형태로 반환.
    """
    try:
        from engine_modules.warehouse_cell_logic import (
            LEVEL_BY_RACK, format_cell_location, get_cell_state,
            WAREHOUSE_DONGS, RACK_RANGE, COL_RANGE,
        )
        if dong not in WAREHOUSE_DONGS:
            return err_response('동은 5 또는 6만 허용')
        if not (RACK_RANGE[0] <= rack <= RACK_RANGE[1]):
            return err_response(f'랙은 {RACK_RANGE[0]}~{RACK_RANGE[1]}')
        max_lv = LEVEL_BY_RACK.get(rack, 0)

        con = _db()
        try:
            cells = []
            for col in range(COL_RANGE[0], COL_RANGE[1] + 1):
                for lv in range(1, max_lv + 1):
                    loc = format_cell_location(dong, rack, col, lv)
                    st  = get_cell_state(con, loc)
                    cells.append({
                        'location':     loc,
                        'col':          col,
                        'level':        lv,
                        'state':        st['state'],
                        'active_count': st['active_count'],
                        'capacity':     st['capacity'],
                        'packing_type': st['packing_type'],
                    })
        finally:
            con.close()
        return ok_response({
            'dong': dong, 'rack': rack, 'max_level': max_lv,
            'col_range': list(COL_RANGE), 'cells': cells,
            'total': len(cells),
        })
    except Exception as e:
        logger.error('cell-grid error: %s', e)
        return err_response(str(e))


# ─────────────────────────────────────────────────────────────────────
# GET /api/warehouse/migrate-analyze
#   현재 DB 위치 형식 분포 (옛/신/INVALID/EMPTY)
# ─────────────────────────────────────────────────────────────────────
@router.get('/migrate-analyze', summary='📊 위치 형식 분포 분석 (마이그레이션 사전 점검)')
def api_migrate_analyze():
    """
    inventory_tonbag.location + inventory.location 의 형식 분포를 측정.
    옛 형식이 얼마나 남아있는지 파악해서 마이그레이션 진행 여부 판단.

    형식 분류:
      NEW    — v8.6.8 신규 (G5-04-01-07)
      OLD_3  — 3파트 (A-01-01)
      OLD_4  — 4파트 (A-01-01-10)
      EMPTY  — NULL/빈 문자열
      INVALID — 알 수 없는 형식
    """
    try:
        from engine_modules.warehouse_cell_logic import analyze_location_formats
        con = _db()
        try:
            data = analyze_location_formats(con)
        finally:
            con.close()
        return ok_response(data)
    except Exception as e:
        logger.error('migrate-analyze error: %s', e)
        return err_response(str(e))


# ─────────────────────────────────────────────────────────────────────
# GET /api/warehouse/half-cells
#   현재 HALF 상태인 모든 셀 + 잔여 톤백 목록
# ─────────────────────────────────────────────────────────────────────
@router.get('/half-cells', summary='🟨 HALF 셀 전체 목록 (CASE 3 누적)')
def api_half_cells():
    """
    출고 후 잔여 처리가 되지 않은 HALF 셀들을 모두 조회.
    작업자가 다이얼로그를 놓쳤거나 나중 처리로 미뤘을 경우 추적 용도.
    """
    try:
        from engine_modules.warehouse_cell_logic import (
            get_cell_state, ACTIVE_STATUSES, _capacity_for,
        )
        con = _db()
        try:
            # capacity 보다 적은 활성 톤백을 가진 location 후보 추출
            sql = """
                SELECT t.location,
                       COUNT(*) AS active_n,
                       MAX(COALESCE(i.packing_type, '')) AS any_pt
                  FROM inventory_tonbag t
                  LEFT JOIN inventory i ON i.lot_no = t.lot_no
                 WHERE t.location IS NOT NULL AND TRIM(t.location) != ''
                   AND COALESCE(t.is_sample, 0) = 0
                   AND t.status IN ({})
                 GROUP BY t.location
            """.format(','.join('?' * len(ACTIVE_STATUSES)))
            rows = con.execute(sql, ACTIVE_STATUSES).fetchall()

            half = []
            for r in rows:
                loc, active_n, any_pt = r[0], r[1], r[2]
                cap = _capacity_for(any_pt)
                if active_n < cap:
                    state = get_cell_state(con, loc)
                    if state['state'] == 'HALF':
                        half.append({
                            'location':     loc,
                            'packing_type': state['packing_type'],
                            'capacity':     state['capacity'],
                            'active_count': state['active_count'],
                            'remaining':    state['tonbags'],
                        })
            return ok_response({'half_cells': half, 'count': len(half)})
        finally:
            con.close()
    except Exception as e:
        logger.error('half-cells error: %s', e)
        return err_response(str(e))


# ─────────────────────────────────────────────────────────────────────
# POST /api/warehouse/case3-resolve
#   CASE 3 잔여 톤백 처리 결정 (STAY 또는 MOVE)
# ─────────────────────────────────────────────────────────────────────
@router.post('/case3-resolve', summary='🔁 CASE 3 잔여 톤백 STAY/MOVE 처리')
def api_case3_resolve(payload: dict):
    """
    Payload:
      {
        "tonbag_id":      int,       # 잔여 톤백 inventory_tonbag.id (필수)
        "resolution":     'STAY' | 'MOVE',
        "to_location":    str,       # MOVE 일 때만 (G5-04-01-07 형식)
        "operator":       str,       # 작업자 (선택, audit_log 용)
        "note":           str,       # 비고 (선택)
      }

    STAY: location 변경 없음, audit_log 만 기록
    MOVE: location 변경 + stock_movement(RELOCATE) + audit_log
    """
    try:
        from engine_modules.warehouse_cell_logic import (
            validate_cell_location, check_cell_invariants,
        )

        tonbag_id  = payload.get('tonbag_id')
        resolution = (payload.get('resolution') or '').upper()
        to_loc     = (payload.get('to_location') or '').strip().upper()
        operator   = (payload.get('operator') or 'user').strip()
        note       = (payload.get('note') or '').strip()

        if not tonbag_id:
            return err_response('tonbag_id 필수')
        if resolution not in ('STAY', 'MOVE'):
            return err_response("resolution 은 'STAY' 또는 'MOVE'")
        if resolution == 'MOVE':
            if not to_loc:
                return err_response('MOVE 시 to_location 필수')
            v = validate_cell_location(to_loc)
            if not v.get('ok'):
                return err_response(f"to_location 형식 오류: {v.get('reason')}")

        con = _db()
        ts  = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        try:
            row = con.execute(
                "SELECT id, lot_no, sub_lt, COALESCE(weight_kg,0) AS w, "
                "       COALESCE(location,'') AS loc "
                "  FROM inventory_tonbag WHERE id=?",
                (tonbag_id,)
            ).fetchone()
            if not row:
                return err_response(f'톤백 id={tonbag_id} 없음')
            from_loc = (row['loc'] or '').strip().upper()

            cell_warnings = []
            if resolution == 'STAY':
                # 위치 변경 없음 — audit_log 만
                con.execute("""
                    INSERT INTO audit_log
                        (event_type, event_data, user_note, created_by, created_at)
                    VALUES ('CASE3_STAY', ?, ?, ?, ?)
                """, (
                    f'{{"tonbag_id":{tonbag_id},"lot_no":"{row["lot_no"]}",'
                    f'"sub_lt":{row["sub_lt"]},"location":"{from_loc}"}}',
                    note or 'CASE 3 잔여 톤백 원위치 유지',
                    operator, ts
                ))
                con.commit()
                # 비파괴 검증 (셀이 여전히 HALF 인 게 정상)
                rep = check_cell_invariants(con, from_loc)
                if not rep['ok']:
                    cell_warnings = rep['warnings']
                return ok_response({
                    'tonbag_id':     tonbag_id,
                    'resolution':    'STAY',
                    'location':      from_loc,
                    'cell_warnings': cell_warnings,
                    'message':       f"톤백 {tonbag_id} 원위치({from_loc}) 유지",
                })

            # MOVE
            con.execute("""
                UPDATE inventory_tonbag
                   SET location=?, location_updated_at=?, updated_at=?
                 WHERE id=?
            """, (to_loc, ts, ts, tonbag_id))
            # stock_movement (RELOCATE)
            con.execute("""
                INSERT INTO stock_movement
                    (lot_no, sub_lt, movement_type, qty_kg,
                     from_location, to_location,
                     reason_code, operator, remarks, created_at)
                VALUES (?, ?, 'RELOCATE', ?, ?, ?, 'CASE3_MOVE', ?, ?, ?)
            """, (row['lot_no'], row['sub_lt'], row['w'],
                  from_loc, to_loc, operator,
                  note or 'CASE 3 잔여 톤백 이동', ts))
            # audit_log
            con.execute("""
                INSERT INTO audit_log
                    (event_type, event_data, user_note, created_by, created_at)
                VALUES ('CASE3_MOVE', ?, ?, ?, ?)
            """, (
                f'{{"tonbag_id":{tonbag_id},"lot_no":"{row["lot_no"]}",'
                f'"from":"{from_loc}","to":"{to_loc}"}}',
                note or 'CASE 3 잔여 톤백 이동', operator, ts
            ))
            con.commit()
            # from/to 셀 모두 비파괴 검증
            for chk in {from_loc, to_loc}:
                if not chk:
                    continue
                rep = check_cell_invariants(con, chk)
                if not rep['ok']:
                    cell_warnings.extend(rep['warnings'])
            return ok_response({
                'tonbag_id':     tonbag_id,
                'resolution':    'MOVE',
                'from_location': from_loc,
                'to_location':   to_loc,
                'cell_warnings': cell_warnings,
                'message':       f"톤백 {tonbag_id} {from_loc} → {to_loc} 이동",
            })
        finally:
            con.close()
    except Exception as e:
        logger.error('case3-resolve error: %s', e)
        return err_response(str(e))
