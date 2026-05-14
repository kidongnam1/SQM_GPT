import os
import sys


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from utils.sqm_legacy_excel import build_inventory_column_map, resolve_legacy_inventory_key


LEGACY_HEADERS_IN = [
    "순번", "입고일", "출고일", "품명", "SAP NO", "M B/L", "화물관리번호",
    "Cont's NO", "LOT NO", "출고갯수\nNET", "출고갯수\nGW", "출고갯수\nPLT",
    "Salar Invoice no.", "위치", "운송사", "Salar Invoice no.",
    "포장갯수\nNET", "포장갯수\nGW", "포장갯수\nPLT", "REMARK",
]


LEGACY_HEADERS_SOLD = [
    "순번", "입고일", "출고일", "품명", "SAP NO", "M B/L", "화물관리번호",
    "Cont's NO", "LOT NO", "출고갯수\nNET", "출고갯수\nGW", "출고갯수\nPLT",
    "Salar Invoice no.", "위치", "운송사", "SALE REF",
    "포장갯수\nNET", "포장갯수\nGW", "포장갯수\nPLT", "REMARK",
]


def test_in_column_16_is_not_sale_ref():
    key = resolve_legacy_inventory_key("Salar Invoice no.", sheet_name="IN", column_index_1based=16)
    assert key == "salar_invoice_no_duplicate"

    mapped = build_inventory_column_map(LEGACY_HEADERS_IN, sheet_name="IN", include_sale_ref=True)
    assert "sale_ref" not in mapped
    assert mapped["salar_invoice_no"] == "Salar Invoice no."


def test_unsold_and_sold_column_16_are_sale_ref():
    assert resolve_legacy_inventory_key("SALE REF", sheet_name="UNSOLD", column_index_1based=16) == "sale_ref"
    assert resolve_legacy_inventory_key("SALE REF", sheet_name="SOLD", column_index_1based=16) == "sale_ref"

    mapped = build_inventory_column_map(LEGACY_HEADERS_SOLD, sheet_name="SOLD", include_sale_ref=True)
    assert mapped["sale_ref"] == "SALE REF"
    assert mapped["salar_invoice_no"] == "Salar Invoice no."


def test_inbound_import_mapping_excludes_sale_ref_even_if_present():
    mapped = build_inventory_column_map(LEGACY_HEADERS_SOLD, sheet_name="SOLD", include_sale_ref=False)
    assert "sale_ref" not in mapped
