# -*- coding: utf-8 -*-
"""Fix 2: inventory_lot_summary VIEW 정정 + v_lot_weight VIEW 신규 생성"""
import sqlite3, sys

DB = r"D:\program\SQM_inventory\SQM_v868_claan\data\db\sqm_inventory.db"

NEW_LOT_SUMMARY = """
CREATE VIEW inventory_lot_summary AS
SELECT
    lot_no,
    COUNT(*)
        FILTER(WHERE status='AVAILABLE' AND COALESCE(is_sample,0)=0)
        AS available_count,
    COALESCE(SUM(weight)
        FILTER(WHERE status='AVAILABLE' AND COALESCE(is_sample,0)=0), 0)
        AS available_weight_kg,
    -- current_weight_kg = _recalc_current_weight() 공식과 동일
    --   (AVAILABLE + RESERVED + RETURN, is_sample=0)
    COALESCE(SUM(weight)
        FILTER(WHERE status IN ('AVAILABLE','RESERVED','RETURN')
               AND COALESCE(is_sample,0)=0), 0)
        AS current_weight_kg,
    COUNT(*)
        FILTER(WHERE status='RESERVED')
        AS reserved_count,
    COALESCE(SUM(weight)
        FILTER(WHERE status='RESERVED'), 0)
        AS reserved_weight_kg,
    COUNT(*)
        FILTER(WHERE status='PICKED')
        AS picked_count,
    COALESCE(SUM(weight)
        FILTER(WHERE status='PICKED'), 0)
        AS picked_weight_kg,
    -- outbound = SOLD 전용 (OUTBOUND/SHIPPED/CONFIRMED → SOLD 통합, b2d136e)
    COUNT(*)
        FILTER(WHERE status='SOLD')
        AS outbound_count,
    COALESCE(SUM(weight)
        FILTER(WHERE status='SOLD'), 0)
        AS outbound_weight_kg,
    COUNT(*)
        FILTER(WHERE status='RETURN')
        AS return_count,
    COALESCE(SUM(weight)
        FILTER(WHERE status='RETURN'), 0)
        AS return_weight_kg,
    COUNT(*)
        FILTER(WHERE COALESCE(is_sample,0)=1)
        AS sample_count,
    COALESCE(SUM(weight)
        FILTER(WHERE COALESCE(is_sample,0)=1), 0)
        AS sample_weight_kg,
    COUNT(*)  AS total_count,
    COALESCE(SUM(weight), 0) AS total_weight_kg
FROM inventory_tonbag
GROUP BY lot_no
"""

NEW_V_LOT_WEIGHT = """
CREATE VIEW v_lot_weight AS
SELECT
    lot_no,
    COALESCE(SUM(CASE
        WHEN status IN ('AVAILABLE','RESERVED','RETURN') AND COALESCE(is_sample,0)=0
        THEN weight ELSE 0 END), 0) AS current_weight,
    COALESCE(SUM(CASE
        WHEN status='PICKED' AND COALESCE(is_sample,0)=0
        THEN weight ELSE 0 END), 0) AS picked_weight
FROM inventory_tonbag
GROUP BY lot_no
"""

con = sqlite3.connect(DB, timeout=10)
try:
    con.execute("DROP VIEW IF EXISTS inventory_lot_summary")
    con.execute(NEW_LOT_SUMMARY)
    con.execute("DROP VIEW IF EXISTS v_lot_weight")
    con.execute(NEW_V_LOT_WEIGHT)
    con.commit()

    # 검증
    cols = [r[1] for r in con.execute("PRAGMA table_info(inventory_lot_summary)").fetchall()]
    sys.stdout.buffer.write(b"[OK] inventory_lot_summary columns: " + ", ".join(cols).encode("utf-8") + b"\n")

    vcols = [r[1] for r in con.execute("PRAGMA table_info(v_lot_weight)").fetchall()]
    sys.stdout.buffer.write(b"[OK] v_lot_weight columns: " + ", ".join(vcols).encode("utf-8") + b"\n")

    # 샘플 조회
    row = con.execute("""
        SELECT lot_no, available_count, current_weight_kg, outbound_count, return_count
        FROM inventory_lot_summary LIMIT 3
    """).fetchall()
    for r in row:
        line = f"  lot={r[0]} avail={r[1]} cur_w={r[2]} out={r[3]} ret={r[4]}"
        sys.stdout.buffer.write(line.encode("utf-8") + b"\n")

finally:
    con.close()
