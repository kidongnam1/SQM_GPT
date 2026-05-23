import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.api.location_candidates import (
    expand_candidates_for_sublots,
    summarize_candidates,
)


def test_expand_candidates_assigns_each_rack_to_sub_lots_by_count():
    candidates = [
        {"location": "G6-08-13-01", "tonbag_count": 2},
        {"location": "G6-08-13-02", "tonbag_count": 2},
    ]

    expanded = expand_candidates_for_sublots(candidates, [1, 2, 3, 4])

    assert expanded == {
        1: "G6-08-13-01",
        2: "G6-08-13-01",
        3: "G6-08-13-02",
        4: "G6-08-13-02",
    }


def test_summarize_candidates_keeps_rack_counts():
    candidates = [
        {"location": "G6-08-13-01", "tonbag_count": 2},
        {"location": "G6-08-13-02", "tonbag_count": 1},
    ]

    assert summarize_candidates(candidates) == "G6-08-13-01 [2], G6-08-13-02 [1]"
