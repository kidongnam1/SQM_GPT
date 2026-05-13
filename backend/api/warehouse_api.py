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
