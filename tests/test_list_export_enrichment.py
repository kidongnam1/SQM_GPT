import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.api import actions, actions2


def _make_conn():
    con = sqlite3.connect(":memory:")
    con.row_factory = sqlite3.Row
    con.executescript(
        """
        CREATE TABLE inventory (
            id INTEGER PRIMARY KEY,
            sap_no TEXT, bl_no TEXT, container_no TEXT, product TEXT,
            lot_no TEXT, lot_sqm TEXT,
            net_weight REAL, current_weight REAL, tonbag_count INTEGER,
            status TEXT, inbound_date TEXT, stock_date TEXT, arrival_date TEXT,
            warehouse TEXT, vessel TEXT, do_no TEXT, remarks TEXT,
            location TEXT
        );
        CREATE TABLE inventory_tonbag (
            id INTEGER PRIMARY KEY,
            inventory_id INTEGER, lot_no TEXT, sap_no TEXT, bl_no TEXT,
            tonbag_uid TEXT, sub_lt INTEGER, tonbag_no TEXT, weight REAL,
            status TEXT, location TEXT, inbound_date TEXT,
            picked_to TEXT, sale_ref TEXT, remarks TEXT
        );
        CREATE TABLE document_do (
            id INTEGER PRIMARY KEY,
            lot_no TEXT, do_no TEXT, bl_no TEXT, sap_no TEXT,
            vessel TEXT, arrival_date TEXT
        );
        CREATE TABLE document_bl (
            id INTEGER PRIMARY KEY,
            lot_no TEXT, bl_no TEXT, sap_no TEXT, vessel TEXT
        );
        CREATE TABLE document_pl (
            id INTEGER PRIMARY KEY,
            lot_no TEXT, bl_no TEXT, sap_no TEXT, vessel TEXT,
            arrival_date TEXT, footer_note TEXT
        );
        CREATE TABLE container_info (
            id INTEGER PRIMARY KEY,
            lot_no TEXT, container_no TEXT
        );
        CREATE TABLE lot_location_import_batch (
            id INTEGER PRIMARY KEY,
            imported_at TEXT
        );
        CREATE TABLE lot_location_map (
            id INTEGER PRIMARY KEY,
            batch_id INTEGER, lot_no TEXT, location TEXT,
            dong TEXT, rack TEXT, col TEXT, level TEXT, tonbag_count INTEGER
        );
        """
    )
    con.execute(
        """
        INSERT INTO inventory
        (id, sap_no, bl_no, container_no, product, lot_no, lot_sqm,
         net_weight, current_weight, tonbag_count, status, inbound_date,
         stock_date, arrival_date, warehouse, vessel, do_no, remarks, location)
        VALUES
        (1, '', '', '', '제품A', 'LOT-1', 'SQM-DELETE',
         1000, 900, 2, 'AVAILABLE', '', '', '', '6동', '', '', '', '')
        """
    )
    con.execute(
        """
        INSERT INTO inventory_tonbag
        (inventory_id, lot_no, sap_no, bl_no, tonbag_uid, sub_lt, tonbag_no,
         weight, status, location, inbound_date, picked_to, sale_ref, remarks)
        VALUES
        (1, 'LOT-1', '', '', 'TB-1', 1, '1', 500, 'AVAILABLE', '', '', '', '', '')
        """
    )
    con.execute(
        """
        INSERT INTO document_do
        (lot_no, do_no, bl_no, sap_no, vessel, arrival_date)
        VALUES ('LOT-1', 'DO-1', 'BL-FROM-DO', 'SAP-FROM-DO', 'VESSEL-DO', '2026-05-18')
        """
    )
    con.execute("INSERT INTO container_info (lot_no, container_no) VALUES ('LOT-1', 'CONT-1')")
    con.execute("INSERT INTO container_info (lot_no, container_no) VALUES ('LOT-1', 'CONT-2')")
    con.execute("INSERT INTO lot_location_import_batch (id, imported_at) VALUES (1, '2026-05-20')")
    con.execute(
        """
        INSERT INTO lot_location_map
        (batch_id, lot_no, location, dong, rack, col, level, tonbag_count)
        VALUES (1, 'LOT-1', 'G6-08-13-01', 'G6', '08', '13', '01', 1)
        """
    )
    return con


def test_lot_list_uses_document_values_and_replaces_candidate_summary_with_check():
    con = _make_conn()

    rows = con.execute(actions._LOT_LIST_EXCEL_SQL).fetchall()
    rows = actions._append_lot_candidate_summary(rows, con)

    row = rows[0]
    assert row[0] == "SAP-FROM-DO"
    assert row[1] == "BL-FROM-DO"
    assert row[2] == "CONT-1, CONT-2"
    assert row[4] == "LOT-1"
    assert row[5] == 1000
    assert row[10] == "2026-05-18"
    assert row[-1] == "\u2713"


def test_tonbag_list_uses_document_bl_and_container_values():
    con = _make_conn()
    sql, params = actions2._tonbag_sql(None)

    rows = con.execute(sql, params).fetchall()
    rows = actions2._append_tonbag_rack_candidates(rows, con)

    row = rows[0]
    assert row[0] == "SAP-FROM-DO"
    assert row[1] == "BL-FROM-DO"
    assert row[2] == "CONT-1, CONT-2"
    assert row[9] == ""
    assert row[10] == "G6-08-13-01"
