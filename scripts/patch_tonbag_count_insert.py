# -*- coding: utf-8 -*-
"""
patch_tonbag_count_insert.py
============================
Purpose: crud_mixin.py add_inventory() INSERT에 tonbag_count 컬럼 추가
Why    : 정합성 검사가 inventory.tonbag_count vs COUNT(inventory_tonbag) 비교하는데
         INSERT 쿼리가 tonbag_count를 누락 → 항상 0 → mismatch FAIL 발생
Bug    : db_schema_mixin.py:110에 tonbag_count INTEGER DEFAULT 0 컬럼 존재
         하지만 crud_mixin.py:216-228 INSERT는 mxbg_pallet만 채움
Fix    : INSERT에 tonbag_count 컬럼 추가 (mxbg_pallet과 동일 값 + 샘플 1개 포함 = mxbg_pallet + 1)
         이유: 정합성 SQL은 i.tonbag_count = COUNT(t.id) 비교 → 샘플 포함된 실제 수와 일치해야
Rule   : CLAUDE.md Rule 5 — Python 스크립트로만 (안전성)
Author : Ruby (Senior Software Architect) — 2026-05-15
"""
import sys
import shutil
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
CRUD = ROOT / "engine_modules" / "inventory_modular" / "crud_mixin.py"

# 현재 (Option A 패치 적용 상태) INSERT 부분
ANCHOR = """                # v868 PENDING 워크플로우: status 파라미터로 받음 (PDF 입고=PENDING, Excel/기타=AVAILABLE 기본)
                _safe_status = status if status in ('AVAILABLE', 'PENDING') else 'AVAILABLE'
                self.db.execute(\"\"\"
                    INSERT INTO inventory (
                        lot_no, sap_no, bl_no, container_no, product, product_code,
                        lot_sqm, folio, vessel, mxbg_pallet, net_weight, gross_weight,
                        current_weight, initial_weight, picked_weight,
                        salar_invoice_no, ship_date, arrival_date, con_return, free_time,
                        warehouse, stock_date, packing_type, status, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                \"\"\", (lot_no, sap_no, bl_no, container_no, product, product_code,
                      lot_sqm, folio, vessel, mxbg_pallet, net_weight, gross_weight,
                      _current_weight_init, net_weight,  # v8.7.1: current_weight = net - sample
                      salar_invoice_no, ship_date, arrival_date, con_return, free_time,
                      warehouse, stock_date, packing_type, _safe_status, now))"""

# 패치: tonbag_count 컬럼 추가 (mxbg_pallet + 1 샘플 톤백 = 실제 INSERT 톤백 수)
PATCH = """                # v868 PENDING 워크플로우: status 파라미터로 받음 (PDF 입고=PENDING, Excel/기타=AVAILABLE 기본)
                _safe_status = status if status in ('AVAILABLE', 'PENDING') else 'AVAILABLE'
                # v868 fix (2026-05-15): tonbag_count 컬럼 INSERT 누락 버그 수정
                # 정합성 검사가 i.tonbag_count vs COUNT(inventory_tonbag) 비교하는데
                # tonbag_count를 채우지 않아 항상 0 → 모든 LOT에서 mismatch FAIL 발생
                # mxbg_pallet개 일반 톤백 + 1개 샘플 톤백 = mxbg_pallet + 1
                _tonbag_count_total = mxbg_pallet + 1
                self.db.execute(\"\"\"
                    INSERT INTO inventory (
                        lot_no, sap_no, bl_no, container_no, product, product_code,
                        lot_sqm, folio, vessel, mxbg_pallet, tonbag_count, net_weight, gross_weight,
                        current_weight, initial_weight, picked_weight,
                        salar_invoice_no, ship_date, arrival_date, con_return, free_time,
                        warehouse, stock_date, packing_type, status, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                \"\"\", (lot_no, sap_no, bl_no, container_no, product, product_code,
                      lot_sqm, folio, vessel, mxbg_pallet, _tonbag_count_total, net_weight, gross_weight,
                      _current_weight_init, net_weight,  # v8.7.1: current_weight = net - sample
                      salar_invoice_no, ship_date, arrival_date, con_return, free_time,
                      warehouse, stock_date, packing_type, _safe_status, now))"""


def main() -> int:
    if not CRUD.exists():
        print(f"[ERROR] target not found: {CRUD}", file=sys.stderr)
        return 1

    text = CRUD.read_text(encoding="utf-8")

    if "_tonbag_count_total" in text:
        print("[SKIP] already patched.")
        return 0

    count = text.count(ANCHOR)
    if count == 0:
        print("[ERROR] anchor not found. Option A 패치가 먼저 적용되어야 함.", file=sys.stderr)
        return 2
    if count > 1:
        print(f"[ERROR] anchor matched {count} times.", file=sys.stderr)
        return 3

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = CRUD.with_suffix(f".py.bak_tonbag_count_{ts}")
    shutil.copy2(CRUD, backup)
    print(f"[INFO] backup: {backup.name}")

    new_text = text.replace(ANCHOR, PATCH, 1)
    CRUD.write_text(new_text, encoding="utf-8")

    # py_compile 검증
    import py_compile
    try:
        py_compile.compile(str(CRUD), doraise=True)
        print("[OK] py_compile passed.")
    except py_compile.PyCompileError as e:
        print(f"[FAIL] syntax error: {e}", file=sys.stderr)
        return 4

    print("[OK] patch applied — tonbag_count 컬럼 INSERT 추가됨.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
