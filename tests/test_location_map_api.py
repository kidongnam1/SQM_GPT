import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.api.location_map_api import _build_report, _ensure_tables, _error_help


def _lot(lot_no, tonbag_sum=10):
    return {
        "lot_no": lot_no,
        "row_num": 2,
        "tonbag_sum": tonbag_sum,
        "short_count": 0,
        "cells": [
            {
                "location": "G6-08-13-01",
                "tonbag_count": tonbag_sum,
                "valid": True,
                "dong": 6,
                "rack": 8,
                "col": 13,
                "level": 1,
            }
        ],
    }


def test_build_report_warns_when_excel_lot_is_not_available_or_pending_in_inventory():
    con = sqlite3.connect(":memory:")
    con.row_factory = sqlite3.Row
    _ensure_tables(con)
    con.execute(
        "CREATE TABLE inventory_tonbag (lot_no TEXT, status TEXT, is_sample INTEGER DEFAULT 0)"
    )
    con.executemany(
        "INSERT INTO inventory_tonbag (lot_no, status, is_sample) VALUES (?, ?, 0)",
        [
            ("LOT_AVAILABLE", "AVAILABLE"),
            ("LOT_PENDING", "PENDING"),
            ("LOT_SOLD", "SOLD"),
        ],
    )

    doc = {
        "source_file": "location.xlsx",
        "stats": {},
        "errors": [],
        "warnings": [],
        "lots": [
            _lot("LOT_AVAILABLE"),
            _lot("LOT_PENDING"),
            _lot("LOT_SOLD"),
            _lot("LOT_MISSING"),
        ],
    }

    report = _build_report(doc, con)

    warnings = "\n".join(report["warnings"])
    assert "LOT_SOLD" in warnings
    assert "LOT_MISSING" in warnings
    assert "AVAILABLE/PENDING" in warnings
    assert "LOT_AVAILABLE" not in warnings
    assert "LOT_PENDING" not in warnings


def test_error_help_includes_reason_and_resolution_steps():
    detail = _error_help(
        "VALIDATION_FAILED",
        causes=["위치 형식 오류가 있습니다"],
        actions=["엑셀의 위치 값을 G6-08-13-01 [2] 형식으로 수정하세요"],
    )

    assert detail["code"] == "VALIDATION_FAILED"
    assert "위치 형식 오류" in detail["causes"][0]
    assert "G6-08-13-01" in detail["actions"][0]
