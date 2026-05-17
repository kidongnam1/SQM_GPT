import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from backend.api import actions3, allocation_api, queries
from parsers.allocation_parser import AllocationParser


def _memory_db():
    con = sqlite3.connect(":memory:")
    con.row_factory = sqlite3.Row
    return con


def test_revert_map_supports_sold_to_picked():
    assert allocation_api._REVERT_MAP["SOLD"] == ("SOLD", "PICKED")


def test_revert_step_updates_only_selected_sold_lot_and_tonbags(monkeypatch, tmp_path):
    db_path = tmp_path / "alloc.db"
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    con.executescript(
        """
        CREATE TABLE allocation_plan (
            lot_no TEXT,
            status TEXT,
            updated_at TEXT,
            cancelled_at TEXT
        );
        CREATE TABLE inventory (
            lot_no TEXT,
            status TEXT,
            sold_to TEXT,
            sale_ref TEXT
        );
        CREATE TABLE inventory_tonbag (
            lot_no TEXT,
            status TEXT
        );
        INSERT INTO allocation_plan VALUES ('LOT-1', 'SOLD', NULL, NULL);
        INSERT INTO allocation_plan VALUES ('LOT-2', 'SOLD', NULL, NULL);
        INSERT INTO inventory VALUES ('LOT-1', 'SOLD', 'A', 'S1');
        INSERT INTO inventory VALUES ('LOT-2', 'SOLD', 'B', 'S2');
        INSERT INTO inventory_tonbag VALUES ('LOT-1', 'SOLD');
        INSERT INTO inventory_tonbag VALUES ('LOT-2', 'SOLD');
        """
    )
    con.commit()
    con.close()

    def _open():
        db = sqlite3.connect(db_path)
        db.row_factory = sqlite3.Row
        return db

    monkeypatch.setattr(allocation_api, "_alloc_db", _open)

    res = allocation_api.revert_allocation_step({"from_status": "SOLD", "lot_nos": ["LOT-1"]})
    assert res["ok"] is True

    inspect = _open()
    assert inspect.execute("SELECT status FROM inventory WHERE lot_no='LOT-1'").fetchone()["status"] == "PICKED"
    assert inspect.execute("SELECT status FROM inventory WHERE lot_no='LOT-2'").fetchone()["status"] == "SOLD"
    assert inspect.execute("SELECT status FROM inventory_tonbag WHERE lot_no='LOT-1'").fetchone()["status"] == "PICKED"
    assert inspect.execute("SELECT status FROM inventory_tonbag WHERE lot_no='LOT-2'").fetchone()["status"] == "SOLD"
    inspect.close()


def test_return_create_updates_inventory_and_tonbags(monkeypatch, tmp_path):
    db_path = tmp_path / "return.db"
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    con.executescript(
        """
        CREATE TABLE inventory (
            id INTEGER PRIMARY KEY,
            lot_no TEXT,
            status TEXT,
            current_weight REAL,
            updated_at TEXT
        );
        CREATE TABLE inventory_tonbag (
            id INTEGER PRIMARY KEY,
            lot_no TEXT,
            status TEXT,
            updated_at TEXT
        );
        CREATE TABLE return_history (
            lot_no TEXT,
            sub_lt TEXT,
            reason TEXT,
            weight_kg REAL,
            return_date TEXT,
            remark TEXT,
            created_at TEXT
        );
        CREATE TABLE stock_movement (
            lot_no TEXT,
            movement_type TEXT,
            qty_kg REAL,
            source_type TEXT,
            actor TEXT,
            remarks TEXT,
            created_at TEXT
        );
        CREATE TABLE audit_log (
            event_type TEXT,
            event_data TEXT,
            user_note TEXT,
            created_by TEXT,
            created_at TEXT
        );
        INSERT INTO inventory (id, lot_no, status, current_weight) VALUES (1, 'LOT-1', 'SOLD', 1000);
        INSERT INTO inventory_tonbag (lot_no, status) VALUES ('LOT-1', 'SOLD'), ('LOT-1', 'SOLD');
        """
    )
    con.commit()
    con.close()

    def _open():
        db = sqlite3.connect(db_path)
        db.row_factory = sqlite3.Row
        return db

    monkeypatch.setattr(actions3, "_db", _open)

    res = actions3.return_create({"lot_no": "LOT-1", "reason": "고객요청", "weight_kg": 1000})
    assert res["ok"] is True
    inspect = _open()
    assert inspect.execute("SELECT status FROM inventory WHERE lot_no='LOT-1'").fetchone()["status"] == "RETURN"
    assert {
        row["status"]
        for row in inspect.execute("SELECT status FROM inventory_tonbag WHERE lot_no='LOT-1'").fetchall()
    } == {"RETURN"}
    inspect.close()


def test_picked_list_exposes_inbound_date(monkeypatch):
    con = _memory_db()
    con.executescript(
        """
        CREATE TABLE picking_table (
            lot_no TEXT,
            customer TEXT,
            picking_no TEXT,
            qty_kg REAL,
            picking_date TEXT,
            status TEXT
        );
        CREATE TABLE inventory (
            lot_no TEXT,
            product TEXT,
            mxbg_pallet INTEGER,
            inbound_date TEXT
        );
        CREATE TABLE inventory_tonbag (
            lot_no TEXT,
            status TEXT,
            is_sample INTEGER,
            weight REAL
        );
        INSERT INTO picking_table VALUES ('LOT-1', 'A', 'P-1', 1000, '2026-05-16', 'ACTIVE');
        INSERT INTO inventory VALUES ('LOT-1', 'P', 10, '2026-05-10');
        INSERT INTO inventory_tonbag VALUES ('LOT-1', 'PICKED', 0, 1000);
        """
    )

    monkeypatch.setattr(queries, "_db", lambda: con)

    body = queries.get_picked_list()
    row = body["data"]["items"][0]
    assert row["inbound_date"] == "2026-05-10"


def test_canonical_allocation_parser_handles_song_and_jakarta_samples():
    parser = AllocationParser()
    song = parser.parse(str(ROOT / "alloc_test_files" / "alloc_test_song_real.xlsx"))
    jakarta = parser.parse(str(ROOT / "alloc_test_files" / "alloc_test_v2_jakarta.xlsx"))

    assert song is not None and len(song.rows) > 0
    assert jakarta is not None and len(jakarta.rows) > 0
