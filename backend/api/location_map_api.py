# -*- coding: utf-8 -*-
"""
SQM Location Map API — v8.6.9
================================
위치재고조회 엑셀(신형식 G{동}-{칸}-{열}-{층} [N]) import 기능.

엔드포인트:
  POST /api/location-map/preview  — 업로드 파싱 + 검증 + 직전 batch diff (DB 미반영)
  POST /api/location-map/commit   — 검증 통과분 DB 반영 (batch 스냅샷 저장)
  GET  /api/location-map/batches  — import 이력 목록
  GET  /api/location-map/latest   — 최신 batch 매핑 조회

DB 테이블 (최초 호출 시 자동 생성):
  lot_location_import_batch — import 1회 = 1 batch
  lot_location_map          — batch별 (LOT, 셀, 톤백수) 행

검증 규칙:
  - 치명적(errors, commit 차단): 위치 형식오류 / 셀 중복 / LOT 중복 / [N] 누락
  - 입고 누락(inbound_short): 신규 LOT인데 톤백 합 ≠ 10 → 경고 + 누락 셀 지목
                              (commit 시 force=true 아니면 차단)
  - diff: 직전 batch와 비교 — 신규/삭제/위치변경/수량변경 LOT 분류

작성자: Ruby (남기동)  /  버전: v8.6.9 (2026-05-19)
"""
import logging
import os
import sqlite3
import tempfile
from datetime import datetime

from fastapi import APIRouter, File, Query, UploadFile

from backend.common.errors import ok_response, err_response

logger = logging.getLogger(__name__)
router = APIRouter(prefix='/api/location-map', tags=['location-map'])


# ─────────────────────────────────────────────────────────────────────
# DB
# ─────────────────────────────────────────────────────────────────────
def _db() -> sqlite3.Connection:
    from config import DB_PATH
    con = sqlite3.connect(str(DB_PATH), timeout=10)
    con.row_factory = sqlite3.Row
    con.execute('PRAGMA journal_mode=WAL')
    con.execute('PRAGMA busy_timeout=5000')
    return con


def _ensure_tables(con: sqlite3.Connection) -> None:
    """lot_location_* 테이블 자동 생성 (최초 1회)."""
    con.executescript("""
        CREATE TABLE IF NOT EXISTS lot_location_import_batch (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            source_file   TEXT    DEFAULT '',
            imported_at   TEXT    NOT NULL,
            total_lots    INTEGER DEFAULT 0,
            total_cells   INTEGER DEFAULT 0,
            total_tonbags INTEGER DEFAULT 0,
            warning_count INTEGER DEFAULT 0,
            note          TEXT    DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS lot_location_map (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            batch_id     INTEGER NOT NULL,
            lot_no       TEXT    NOT NULL,
            location     TEXT    NOT NULL,
            dong         INTEGER,
            rack         INTEGER,
            col          INTEGER,
            level        INTEGER,
            tonbag_count INTEGER NOT NULL DEFAULT 0,
            product      TEXT    DEFAULT '',
            shipper      TEXT    DEFAULT '',
            sap_no       TEXT    DEFAULT '',
            created_at   TEXT    NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_llm_batch ON lot_location_map(batch_id);
        CREATE INDEX IF NOT EXISTS idx_llm_lot   ON lot_location_map(lot_no);
        CREATE INDEX IF NOT EXISTS idx_llm_loc   ON lot_location_map(location);
    """)
    con.commit()


def _load_latest_batch(con: sqlite3.Connection):
    """직전(최신) batch id + {lot_no: {location: tonbag_count}} 반환."""
    row = con.execute(
        'SELECT id FROM lot_location_import_batch ORDER BY id DESC LIMIT 1'
    ).fetchone()
    if not row:
        return None, {}
    batch_id = row['id']
    prev: dict = {}
    for r in con.execute(
        'SELECT lot_no, location, tonbag_count FROM lot_location_map WHERE batch_id=?',
        (batch_id,),
    ):
        prev.setdefault(r['lot_no'], {})[r['location']] = r['tonbag_count']
    return batch_id, prev


# ─────────────────────────────────────────────────────────────────────
# 분석 (diff + 입고 검증)
# ─────────────────────────────────────────────────────────────────────
def _new_map_from_lots(lots: list) -> dict:
    """파싱 lots → {lot_no: {location: tonbag_count}} (유효 셀만)."""
    out: dict = {}
    for lot in lots:
        out[lot['lot_no']] = {
            c['location']: c['tonbag_count']
            for c in lot['cells'] if c.get('valid')
        }
    return out


def _compute_diff(prev_map: dict, new_map: dict) -> dict:
    """직전 batch와 신규 파일 비교 → 신규/삭제/위치변경/수량변경 분류."""
    prev_ids, new_ids = set(prev_map), set(new_map)
    new_lots = sorted(new_ids - prev_ids)
    removed_lots = sorted(prev_ids - new_ids)
    location_changed, count_changed = [], []
    unchanged = 0
    for lot in sorted(new_ids & prev_ids):
        pv, nv = prev_map[lot], new_map[lot]
        if set(pv) != set(nv):
            location_changed.append({
                'lot_no': lot,
                'before': sorted(pv), 'after': sorted(nv),
            })
        elif pv != nv:
            count_changed.append({
                'lot_no': lot,
                'before': pv, 'after': nv,
            })
        else:
            unchanged += 1
    return {
        'new_lots':         new_lots,
        'removed_lots':     removed_lots,
        'location_changed': location_changed,
        'count_changed':    count_changed,
        'unchanged_count':  unchanged,
    }


def _inbound_short_check(lots: list, new_lot_ids: set) -> list:
    """신규(입고) LOT 중 톤백 합 ≠ 10 인 건 → 누락 셀 지목."""
    from features.parsers.location_inventory_parser import (
        EXPECTED_TONBAGS_PER_LOT, find_missing_cells,
    )
    short = []
    for lot in lots:
        if lot['lot_no'] not in new_lot_ids:
            continue  # 기존 LOT은 입고 검증 대상 아님 (출고 감소는 정상)
        if lot['tonbag_sum'] == EXPECTED_TONBAGS_PER_LOT:
            continue
        short.append({
            'lot_no':        lot['lot_no'],
            'row_num':       lot['row_num'],
            'tonbag_sum':    lot['tonbag_sum'],
            'expected':      EXPECTED_TONBAGS_PER_LOT,
            'short_count':   lot['short_count'],
            'missing_cells': find_missing_cells(lot),
        })
    return short


def _build_report(doc: dict, con: sqlite3.Connection) -> dict:
    """파싱 doc + DB → preview/commit 공용 분석 리포트."""
    prev_batch_id, prev_map = _load_latest_batch(con)
    new_map = _new_map_from_lots(doc['lots'])
    diff = _compute_diff(prev_map, new_map)
    inbound_short = _inbound_short_check(doc['lots'], set(diff['new_lots']))

    fatal = list(doc['errors'])              # 형식/셀중복/LOT중복 — commit 차단
    can_commit = (len(fatal) == 0 and len(doc['lots']) > 0)

    return {
        'source_file':   doc['source_file'],
        'stats':         doc['stats'],
        'errors':        fatal,
        'warnings':      list(doc['warnings']),
        'inbound_short': inbound_short,
        'diff': {
            'prev_batch_id': prev_batch_id,
            **diff,
        },
        'can_commit':       can_commit,
        'has_inbound_short': len(inbound_short) > 0,
    }


async def _save_upload(file: UploadFile) -> str:
    """업로드 파일 → 임시 .xlsx 경로."""
    ext = os.path.splitext(file.filename or '')[1].lower()
    if ext not in ('.xlsx', '.xls'):
        raise ValueError(f'Excel 파일만 지원 (.xlsx/.xls). 받은 파일: {file.filename}')
    content = await file.read()
    if not content:
        raise ValueError('빈 파일입니다')
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        tmp.write(content)
        return tmp.name


# ─────────────────────────────────────────────────────────────────────
# POST /api/location-map/preview
# ─────────────────────────────────────────────────────────────────────
@router.post('/preview', summary='📋 위치 매핑 엑셀 미리보기 (검증 + diff, DB 미반영)')
async def preview_location_map(file: UploadFile = File(...)):
    """업로드 엑셀을 파싱·검증하고 직전 batch와 diff 만 반환 (DB 안 건드림)."""
    from features.parsers.location_inventory_parser import parse_location_inventory_excel

    tmp_path = None
    try:
        tmp_path = await _save_upload(file)
        doc = parse_location_inventory_excel(tmp_path)
        con = _db()
        try:
            _ensure_tables(con)
            report = _build_report(doc, con)
        finally:
            con.close()
        report['filename'] = file.filename
        return ok_response(report)
    except ValueError as ve:
        return err_response(str(ve))
    except Exception as e:  # noqa: BLE001
        logger.exception('[location-map/preview] error: %s', e)
        return err_response(f'미리보기 실패: {e}')
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError:
                pass


# ─────────────────────────────────────────────────────────────────────
# POST /api/location-map/commit
# ─────────────────────────────────────────────────────────────────────
@router.post('/commit', summary='💾 위치 매핑 엑셀 DB 반영 (batch 스냅샷 저장)')
async def commit_location_map(
    file: UploadFile = File(...),
    force: bool = Query(False, description='입고 누락(10개 미만) 경고를 무시하고 강제 반영'),
):
    """
    검증 통과분을 lot_location_map 에 새 batch 로 저장.
    - 치명적 에러(형식/셀중복/LOT중복) 있으면 항상 차단
    - 입고 누락(신규 LOT 10개 미만)은 force=true 가 아니면 차단
    """
    from features.parsers.location_inventory_parser import parse_location_inventory_excel

    tmp_path = None
    try:
        tmp_path = await _save_upload(file)
        doc = parse_location_inventory_excel(tmp_path)
        con = _db()
        try:
            _ensure_tables(con)
            report = _build_report(doc, con)

            # 1) 치명적 에러 → 항상 차단
            if not report['can_commit']:
                return {
                    'ok': False,
                    'error': '검증 실패 — 치명적 에러가 있어 반영할 수 없습니다',
                    'error_code': 'VALIDATION_FAILED',
                    'data': report,
                }
            # 2) 입고 누락 → force 아니면 차단
            if report['has_inbound_short'] and not force:
                return {
                    'ok': False,
                    'error': (
                        '신규 입고 LOT 중 톤백이 10개가 안 되는 건이 있습니다 — '
                        '바코드 스캔 누락일 수 있으니 현장 확인 후 수정하거나, '
                        '확인했다면 강제 반영(force)으로 진행하세요'
                    ),
                    'error_code': 'INBOUND_SHORT',
                    'data': report,
                }

            # 3) 반영
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            st = doc['stats']
            cur = con.execute(
                'INSERT INTO lot_location_import_batch '
                '(source_file, imported_at, total_lots, total_cells, '
                ' total_tonbags, warning_count, note) VALUES (?,?,?,?,?,?,?)',
                (file.filename or doc['source_file'], now,
                 st['total_lots'], st['total_cells'], st['total_tonbags'],
                 st['warning_count'],
                 'force' if force else ''),
            )
            batch_id = cur.lastrowid
            rows = 0
            for lot in doc['lots']:
                for c in lot['cells']:
                    if not c.get('valid'):
                        continue
                    con.execute(
                        'INSERT INTO lot_location_map '
                        '(batch_id, lot_no, location, dong, rack, col, level, '
                        ' tonbag_count, product, shipper, sap_no, created_at) '
                        'VALUES (?,?,?,?,?,?,?,?,?,?,?,?)',
                        (batch_id, lot['lot_no'], c['location'],
                         c['dong'], c['rack'], c['col'], c['level'],
                         c['tonbag_count'], lot['product'], lot['shipper'],
                         lot['sap_no'], now),
                    )
                    rows += 1
            con.commit()
        finally:
            con.close()

        logger.info('[location-map/commit] batch=%s rows=%s file=%s force=%s',
                    batch_id, rows, file.filename, force)
        report['batch_id'] = batch_id
        report['committed_rows'] = rows
        return ok_response(report,
                           message=f'배치 #{batch_id} 반영 완료 — {rows}개 셀 매핑 저장')
    except ValueError as ve:
        return err_response(str(ve))
    except Exception as e:  # noqa: BLE001
        logger.exception('[location-map/commit] error: %s', e)
        return err_response(f'반영 실패: {e}')
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError:
                pass


# ─────────────────────────────────────────────────────────────────────
# GET /api/location-map/batches
# ─────────────────────────────────────────────────────────────────────
@router.get('/batches', summary='📚 위치 매핑 import 이력')
def list_batches(limit: int = Query(50, ge=1, le=500)):
    """import batch 목록 (최신순)."""
    try:
        con = _db()
        try:
            _ensure_tables(con)
            rows = con.execute(
                'SELECT id, source_file, imported_at, total_lots, total_cells, '
                '       total_tonbags, warning_count, note '
                'FROM lot_location_import_batch ORDER BY id DESC LIMIT ?',
                (limit,),
            ).fetchall()
        finally:
            con.close()
        return ok_response({
            'batches': [dict(r) for r in rows],
            'count': len(rows),
        })
    except Exception as e:  # noqa: BLE001
        logger.exception('[location-map/batches] error: %s', e)
        return err_response(str(e))


# ─────────────────────────────────────────────────────────────────────
# GET /api/location-map/latest
# ─────────────────────────────────────────────────────────────────────
@router.get('/latest', summary='📍 최신 batch 위치 매핑')
def latest_map(batch_id: int = Query(None, description='지정 시 해당 batch, 미지정 시 최신')):
    """최신(또는 지정) batch 의 LOT↔셀 매핑 전체 반환."""
    try:
        con = _db()
        try:
            _ensure_tables(con)
            if batch_id is None:
                row = con.execute(
                    'SELECT id FROM lot_location_import_batch ORDER BY id DESC LIMIT 1'
                ).fetchone()
                if not row:
                    return ok_response({'batch_id': None, 'lots': [], 'count': 0})
                batch_id = row['id']
            rows = con.execute(
                'SELECT lot_no, location, dong, rack, col, level, tonbag_count, '
                '       product, shipper, sap_no '
                'FROM lot_location_map WHERE batch_id=? ORDER BY lot_no, location',
                (batch_id,),
            ).fetchall()
        finally:
            con.close()
        # LOT별로 묶기
        lots: dict = {}
        for r in rows:
            d = lots.setdefault(r['lot_no'], {
                'lot_no': r['lot_no'], 'product': r['product'],
                'shipper': r['shipper'], 'sap_no': r['sap_no'],
                'cells': [], 'tonbag_sum': 0,
            })
            d['cells'].append({
                'location': r['location'], 'dong': r['dong'], 'rack': r['rack'],
                'col': r['col'], 'level': r['level'],
                'tonbag_count': r['tonbag_count'],
            })
            d['tonbag_sum'] += r['tonbag_count']
        return ok_response({
            'batch_id': batch_id,
            'lots': list(lots.values()),
            'count': len(lots),
        })
    except Exception as e:  # noqa: BLE001
        logger.exception('[location-map/latest] error: %s', e)
        return err_response(str(e))
