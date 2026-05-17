"""
상태 전이 단일 기준
===================

PENDING   -> AVAILABLE
AVAILABLE -> PENDING / RESERVED
RESERVED  -> AVAILABLE / PICKED
PICKED    -> RESERVED / SOLD
SOLD      -> PICKED / RETURN
RETURN    -> AVAILABLE

이 파일은 문서와 테스트를 한 곳에 둔다.
상태 규칙을 바꿀 때는 이 표와 검증을 함께 고쳐야 한다.
"""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from backend.api import allocation_api


STATE_TRANSITIONS = {
    "PENDING": {"AVAILABLE"},
    "AVAILABLE": {"PENDING", "RESERVED"},
    "RESERVED": {"AVAILABLE", "PICKED"},
    "PICKED": {"RESERVED", "SOLD"},
    "SOLD": {"PICKED", "RETURN"},
    "RETURN": {"AVAILABLE"},
}


def test_revert_map_matches_contract():
    assert allocation_api._REVERT_MAP == {
        "RESERVED": ("RESERVED", "AVAILABLE"),
        "PICKED": ("PICKED", "RESERVED"),
        "SOLD": ("SOLD", "PICKED"),
    }


def test_core_reverse_transitions_are_allowed():
    for src, dst in allocation_api._REVERT_MAP.values():
        assert dst in STATE_TRANSITIONS[src]
