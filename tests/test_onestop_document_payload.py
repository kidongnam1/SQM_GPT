from dataclasses import dataclass
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from backend.api.inbound import (
    _doc_to_payload,
    _persist_onestop_document_payload,
    _safe_attr,
)


@dataclass
class _Container:
    container_no: str
    free_time_date: str = ""


@dataclass
class _Doc:
    bl_no: str
    containers: list
    raw_text: str = "should not be sent"


def test_safe_attr_reads_dict_and_object_values():
    assert _safe_attr({"container": "MSMU5531984"}, "container_no", "container") == "MSMU5531984"
    assert _safe_attr(_Container("HAMU2723596"), "container_no") == "HAMU2723596"


def test_doc_to_payload_preserves_nested_document_lists_without_raw_text():
    payload = _doc_to_payload(_Doc("HLCUSCL260148627", [_Container("HAMU2723596", "2026-04-20")]))

    assert payload["bl_no"] == "HLCUSCL260148627"
    assert payload["containers"][0]["container_no"] == "HAMU2723596"
    assert payload["containers"][0]["free_time_date"] == "2026-04-20"
    assert "raw_text" not in payload


def test_persist_onestop_document_payload_calls_all_document_tables():
    class FakeEngine:
        def __init__(self):
            self.calls = []

        def _insert_do_details(self, lot_no, inventory_id, do_data):
            self.calls.append(("do_details", lot_no, inventory_id, do_data))

        def _insert_document_invoice(self, lot_no, inventory_id, invoice_data):
            self.calls.append(("invoice", lot_no, inventory_id, invoice_data))

        def _insert_document_bl(self, lot_no, inventory_id, bl_data):
            self.calls.append(("bl", lot_no, inventory_id, bl_data))

        def _insert_document_pl(self, lot_no, inventory_id, pl_data):
            self.calls.append(("pl", lot_no, inventory_id, pl_data))

        def _insert_document_do(self, lot_no, inventory_id, do_data):
            self.calls.append(("do", lot_no, inventory_id, do_data))

    engine = FakeEngine()
    row_data = {
        "lot_no": "1126021724",
        "sap_no": "2200034659",
        "bl_no": "HLCUSCL260148627",
        "product": "LITHIUM CARBONATE",
        "mxbg_pallet": 10,
        "net_weight": 5001.0,
    }
    doc_payload = {
        "packing_list": {"folio": "3812291", "lots": [{"lot_no": "1126021724"}]},
        "bl": {"bl_no": "HLCUSCL260148627"},
        "invoice": {"invoice_no": "17760"},
        "do": {
            "do_no": "26041712Z7H6",
            "containers": [{"container_no": "HAMU2723596"}],
            "free_time_info": [{"container_no": "HAMU2723596", "free_time_date": "2026-04-20"}],
        },
    }

    _persist_onestop_document_payload(engine, "1126021724", 7, row_data, doc_payload)

    assert [c[0] for c in engine.calls] == ["do_details", "invoice", "bl", "pl", "do"]
    pl_call = next(c for c in engine.calls if c[0] == "pl")
    assert pl_call[3]["folio"] == "3812291"
    assert pl_call[3]["_pl_lots_raw"] == [{"lot_no": "1126021724"}]
