# -*- coding: utf-8 -*-
"""
scripts/cleanup_inbound_templates.py
=====================================
seed_templates_api.py 재시딩 전, inbound_template 의 기존 5개 행을 정리.

대상 행 (2026-05-14 시점 DB 상태):
  - MAERSK_LC500     (이모지 포함 이름 — seed 와 충돌)
  - MSC_LC500        (이모지 포함 이름 — seed 와 충돌)
  - MSC_LC1000       (이모지 포함 이름 — seed 와 충돌)
  - UNKNOWN_500      (UI 필터에서 제외되는 dead row)
  - UNKNOWN_1000     (UI 필터에서 제외되는 dead row)

실행:
    python scripts/cleanup_inbound_templates.py            # dry-run (조회만)
    python scripts/cleanup_inbound_templates.py --apply    # 실제 DELETE
"""
import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "db" / "sqm_inventory.db"

TARGET_IDS = [
    "MAERSK_LC500",
    "MSC_LC500",
    "MSC_LC1000",
    "UNKNOWN_500",
    "UNKNOWN_1000",
]


def main() -> int:
    apply = "--apply" in sys.argv
    if not DB_PATH.exists():
        print(f"[ERROR] DB not found: {DB_PATH}")
        return 1

    con = sqlite3.connect(str(DB_PATH))
    cur = con.cursor()

    placeholders = ",".join("?" * len(TARGET_IDS))
    rows = cur.execute(
        f"SELECT template_id, template_name, carrier_id, bag_weight_kg "
        f"FROM inbound_template WHERE template_id IN ({placeholders})",
        TARGET_IDS,
    ).fetchall()

    print("=" * 60)
    print(f"DB: {DB_PATH}")
    print(f"Mode: {'APPLY (DELETE 실행)' if apply else 'DRY-RUN (조회만)'}")
    print("=" * 60)
    print(f"삭제 대상 (실제 존재 {len(rows)}/{len(TARGET_IDS)}):")
    for r in rows:
        print(f"  - {r[0]:15s} | {r[2]:8s} | {r[3]}kg | {r[1]}")

    if not rows:
        print("[INFO] 대상 행 없음 — 이미 정리됨.")
        con.close()
        return 0

    if not apply:
        print()
        print("[DRY-RUN] 실제 삭제하려면 --apply 플래그를 붙여 재실행하세요:")
        print("    python scripts/cleanup_inbound_templates.py --apply")
        con.close()
        return 0

    cur.execute(
        f"DELETE FROM inbound_template WHERE template_id IN ({placeholders})",
        TARGET_IDS,
    )
    con.commit()
    print(f"\n[DONE] {cur.rowcount}개 행 삭제 완료.")

    remaining = cur.execute(
        "SELECT carrier_id, COUNT(*) FROM inbound_template GROUP BY carrier_id"
    ).fetchall()
    print("\n잔여 carrier_id 분포:")
    for c, n in remaining:
        print(f"  {c}: {n}개")

    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
