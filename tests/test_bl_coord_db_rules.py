import os
import sqlite3
import sys
import types

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from parsers.document_parser_modular.bl_mixin import BLMixin


def _word(text, x_pct, y_pct, page=0, width=1000.0, height=1000.0):
    return {
        "text": text,
        "x0": x_pct / 100.0 * width,
        "x1": (x_pct + 1.0) / 100.0 * width,
        "top": y_pct / 100.0 * height,
        "bottom": (y_pct + 1.0) / 100.0 * height,
        "page": page,
        "width": width,
        "height": height,
    }


def _make_coord_db(path, rows):
    con = sqlite3.connect(path)
    con.execute(
        """
        CREATE TABLE carrier_field_coord (
            carrier_id TEXT,
            document_type TEXT,
            field_name TEXT,
            page_index INTEGER,
            x1_pct REAL,
            x2_pct REAL,
            y1_pct REAL,
            y2_pct REAL,
            is_active INTEGER,
            valid_from TEXT,
            valid_to TEXT
        )
        """
    )
    con.executemany(
        """
        INSERT INTO carrier_field_coord (
            carrier_id, document_type, field_name, page_index,
            x1_pct, x2_pct, y1_pct, y2_pct,
            is_active, valid_from, valid_to
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )
    con.commit()
    con.close()


def test_parse_by_coord_table_prefers_active_db_rules(monkeypatch, tmp_path):
    db_path = tmp_path / "coord_rules.sqlite"
    _make_coord_db(
        db_path,
        [
            (
                "MSC",
                "BL",
                "bl_no",
                0,
                10.0,
                20.0,
                10.0,
                12.0,
                1,
                None,
                None,
            )
        ],
    )
    monkeypatch.setitem(sys.modules, "config", types.SimpleNamespace(DB_PATH=str(db_path)))

    words = [
        _word("MEDUDB123456", 12.0, 10.5),
        _word("MEDUFALLBACK999", 70.0, 2.5),
    ]

    parsed = BLMixin()._parse_by_coord_table(words, "MSC")

    assert parsed["bl_no"] == "MEDUDB123456"


def test_parse_by_coord_table_treats_empty_valid_to_as_active(monkeypatch, tmp_path):
    db_path = tmp_path / "coord_rules.sqlite"
    _make_coord_db(
        db_path,
        [
            (
                "MSC",
                "BL",
                "bl_no",
                0,
                10.0,
                20.0,
                10.0,
                12.0,
                1,
                "2026-01-01",
                "",
            )
        ],
    )
    monkeypatch.setitem(sys.modules, "config", types.SimpleNamespace(DB_PATH=str(db_path)))

    words = [
        _word("MEDUDB123456", 12.0, 10.5),
        _word("MEDUFALLBACK999", 70.0, 2.5),
    ]

    parsed = BLMixin()._parse_by_coord_table(words, "MSC")

    assert parsed["bl_no"] == "MEDUDB123456"


def test_parse_by_coord_table_merges_partial_db_rules_with_code_table(monkeypatch, tmp_path):
    db_path = tmp_path / "coord_rules.sqlite"
    _make_coord_db(
        db_path,
        [
            (
                "MSC",
                "BL",
                "bl_no",
                0,
                10.0,
                20.0,
                10.0,
                12.0,
                1,
                None,
                None,
            )
        ],
    )
    monkeypatch.setitem(sys.modules, "config", types.SimpleNamespace(DB_PATH=str(db_path)))

    words = [
        _word("MEDUDB123456", 12.0, 10.5),
        _word("MANZANILLO", 4.0, 30.0),
        _word("EXPRESS", 10.0, 30.0),
    ]

    parsed = BLMixin()._parse_by_coord_table(words, "MSC")

    assert parsed["bl_no"] == "MEDUDB123456"
    assert parsed["vessel"] == "MANZANILLO EXPRESS"


def test_parse_by_coord_table_falls_back_to_code_table_when_db_empty(monkeypatch, tmp_path):
    db_path = tmp_path / "coord_rules.sqlite"
    _make_coord_db(db_path, [])
    monkeypatch.setitem(sys.modules, "config", types.SimpleNamespace(DB_PATH=str(db_path)))

    words = [_word("MEDUFALLBACK999", 70.0, 2.5)]

    parsed = BLMixin()._parse_by_coord_table(words, "MSC")

    assert parsed["bl_no"] == "MEDUFALLBACK999"


def test_parse_by_coord_table_falls_back_to_code_table_when_db_fails(monkeypatch):
    monkeypatch.setitem(sys.modules, "config", types.SimpleNamespace(DB_PATH="ignored.sqlite"))

    def raise_connect(*_args, **_kwargs):
        raise sqlite3.OperationalError("cannot open database")

    monkeypatch.setattr(sqlite3, "connect", raise_connect)
    words = [_word("MEDUFALLBACK999", 70.0, 2.5)]

    parsed = BLMixin()._parse_by_coord_table(words, "MSC")

    assert parsed["bl_no"] == "MEDUFALLBACK999"


def test_parse_by_coord_table_uses_db_page_index_for_gross_weight(monkeypatch, tmp_path):
    db_path = tmp_path / "coord_rules.sqlite"
    _make_coord_db(
        db_path,
        [
            (
                "ONE",
                "BL",
                "gross_weight_p1",
                1,
                10.0,
                20.0,
                10.0,
                12.0,
                1,
                None,
                None,
            )
        ],
    )
    monkeypatch.setitem(sys.modules, "config", types.SimpleNamespace(DB_PATH=str(db_path)))

    words = [
        _word("999,999", 12.0, 10.5, page=0),
        _word("102,625", 12.0, 10.5, page=1),
    ]

    parsed = BLMixin()._parse_by_coord_table(words, "ONE")

    assert parsed["gross_weight_coord"] == 102625.0
