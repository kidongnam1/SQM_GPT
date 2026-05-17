# -*- coding: utf-8 -*-
"""Fix 3: dashboard.py 정합성 섹션 수정
- current_stock_kg: PICKED 제외 (inventory.current_weight 공식과 통일)
- picked_kg: 별도 집계
- outbound_total_kg: SOLD 전용 (SHIPPED/CONFIRMED 제거)
- diff_kg: current + picked + outbound = total_inbound
- _sample_tb: PICKED 제외
"""
import re, sys

PATH = r"D:\program\SQM_inventory\SQM_v868_claan\backend\api\dashboard.py"

with open(PATH, encoding="utf-8") as f:
    src = f.read()

# ── Patch A: 정합성 블록 (현재재고/출고누계/diff) ───────────────────────────
OLD_A = '''        # 현재 재고 중량 (샘플 포함: AVAILABLE + RESERVED + PICKED + RETURN)
        current_stock_kg = c.execute("""
            SELECT COALESCE(SUM(weight), 0) FROM inventory_tonbag
            WHERE status IN ('AVAILABLE', 'RESERVED', 'PICKED', 'RETURN')
        """).fetchone()[0]

        # 출고 누계 중량 (샘플 포함: OUTBOUND + SOLD 상태 톤백)
        outbound_total_kg = c.execute("""
            SELECT COALESCE(SUM(weight), 0) FROM inventory_tonbag
            WHERE status IN ('SOLD', 'SHIPPED', 'CONFIRMED')
        """).fetchone()[0]

        diff_kg = round(float(total_inbound_kg) - float(current_stock_kg) - float(outbound_total_kg), 1)
        integrity = {
            "total_inbound_kg":  round(float(total_inbound_kg), 1),
            "current_stock_kg":  round(float(current_stock_kg), 1),
            "outbound_total_kg": round(float(outbound_total_kg), 1),
            "diff_kg":           diff_kg,
            "ok":                abs(diff_kg) <= 1.0,
        }'''

NEW_A = '''        # 현재 재고 중량 — inventory.current_weight(_recalc) 공식과 동일
        # AVAILABLE + RESERVED + RETURN, 샘플 포함 (is_sample 필터 없음 — dashboard는 총계)
        current_stock_kg = c.execute("""
            SELECT COALESCE(SUM(weight), 0) FROM inventory_tonbag
            WHERE status IN ('AVAILABLE', 'RESERVED', 'RETURN')
        """).fetchone()[0]

        # 출고 작업 중 (PICKED: 차량 미출발, 취소 가능) — 별도 집계
        picked_kg = c.execute("""
            SELECT COALESCE(SUM(weight), 0) FROM inventory_tonbag
            WHERE status = 'PICKED'
        """).fetchone()[0]

        # 출고 누계 (SOLD 전용 — OUTBOUND/SHIPPED/CONFIRMED는 SOLD로 통합됨, b2d136e)
        outbound_total_kg = c.execute("""
            SELECT COALESCE(SUM(weight), 0) FROM inventory_tonbag
            WHERE status = 'SOLD'
        """).fetchone()[0]

        diff_kg = round(
            float(total_inbound_kg)
            - float(current_stock_kg)
            - float(picked_kg)
            - float(outbound_total_kg),
            1,
        )
        integrity = {
            "total_inbound_kg":  round(float(total_inbound_kg), 1),
            "current_stock_kg":  round(float(current_stock_kg), 1),
            "picked_kg":         round(float(picked_kg), 1),
            "outbound_total_kg": round(float(outbound_total_kg), 1),
            "diff_kg":           diff_kg,
            "ok":                abs(diff_kg) <= 1.0,
        }'''

# ── Patch B: _sample_tb PICKED 제거 ────────────────────────────────────────
OLD_B = '''        _sample_tb = c.execute(
            """
            SELECT COALESCE(SUM(weight), 0) FROM inventory_tonbag
            WHERE COALESCE(is_sample, 0) = 1
              AND status IN ('AVAILABLE', 'RESERVED', 'PICKED', 'RETURN')
            """
        ).fetchone()[0]'''

NEW_B = '''        _sample_tb = c.execute(
            """
            SELECT COALESCE(SUM(weight), 0) FROM inventory_tonbag
            WHERE COALESCE(is_sample, 0) = 1
              AND status IN ('AVAILABLE', 'RESERVED', 'RETURN')
            """
        ).fetchone()[0]'''

if OLD_A not in src:
    sys.stdout.buffer.write(b"[WARN] Patch A: target block NOT found - already patched?\n")
else:
    src = src.replace(OLD_A, NEW_A, 1)
    sys.stdout.buffer.write(b"[OK] Patch A applied (integrity block)\n")

if OLD_B not in src:
    sys.stdout.buffer.write(b"[WARN] Patch B: target block NOT found - already patched?\n")
else:
    src = src.replace(OLD_B, NEW_B, 1)
    sys.stdout.buffer.write(b"[OK] Patch B applied (_sample_tb)\n")

with open(PATH, "w", encoding="utf-8") as f:
    f.write(src)

sys.stdout.buffer.write(b"[DONE] dashboard.py saved\n")
