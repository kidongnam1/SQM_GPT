# -*- coding: utf-8 -*-
"""
patch_add_inventory_status.py
==============================
Purpose: add_inventory() 에 status 파라미터 추가 (기본값 'AVAILABLE') + INSERT 3곳의 하드코딩 제거
Why    : v868 PENDING 워크플로우 반쪽 구현 수정 — PDF 스캔 입고 시 PENDING으로 들어가도록
         (053fa7a 커밋이 API/UI만 추가하고 실제 INSERT 코드 변경은 누락한 버그 수정)
Rule   : CLAUDE.md Rule 5 — 안전 위해 Python 스크립트 사용 (멱등성 + 백업 + 라인 검증)
Author : Ruby (Senior Software Architect) — 2026-05-15
"""
import sys
import shutil
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent

# ────────────────────────────────────────────────────────────
# 패치 1: crud_mixin.py
# ────────────────────────────────────────────────────────────
CRUD = ROOT / "engine_modules" / "inventory_modular" / "crud_mixin.py"

# (1-A) add_inventory 시그니처에 status 파라미터 추가
ANCHOR_A = """    def add_inventory(self, lot_no: str, sap_no: str = None, bl_no: str = None,
                      container_no: str = None, product: str = None,
                      product_code: str = None, mxbg_pallet: int = 20,
                      net_weight: float = 10000, warehouse: str = 'GY',
                      arrival_date=None, stock_date=None, **kwargs) -> Dict:"""

PATCH_A = """    def add_inventory(self, lot_no: str, sap_no: str = None, bl_no: str = None,
                      container_no: str = None, product: str = None,
                      product_code: str = None, mxbg_pallet: int = 20,
                      net_weight: float = 10000, warehouse: str = 'GY',
                      arrival_date=None, stock_date=None,
                      status: str = 'AVAILABLE', **kwargs) -> Dict:"""

# (1-B) inventory INSERT의 'AVAILABLE' 하드코딩 → ? 바인딩
ANCHOR_B = """                self.db.execute(\"\"\"
                    INSERT INTO inventory (
                        lot_no, sap_no, bl_no, container_no, product, product_code,
                        lot_sqm, folio, vessel, mxbg_pallet, net_weight, gross_weight,
                        current_weight, initial_weight, picked_weight,
                        salar_invoice_no, ship_date, arrival_date, con_return, free_time,
                        warehouse, stock_date, packing_type, status, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?, ?, ?, ?, ?, 'AVAILABLE', ?)
                \"\"\", (lot_no, sap_no, bl_no, container_no, product, product_code,
                      lot_sqm, folio, vessel, mxbg_pallet, net_weight, gross_weight,
                      _current_weight_init, net_weight,  # v8.7.1: current_weight = net - sample
                      salar_invoice_no, ship_date, arrival_date, con_return, free_time,
                      warehouse, stock_date, packing_type, now))"""

PATCH_B = """                # v868 PENDING 워크플로우: status 파라미터로 받음 (PDF 입고=PENDING, Excel/기타=AVAILABLE 기본)
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

# (1-C) inventory_tonbag INSERT의 'AVAILABLE' 하드코딩 → _safe_status 바인딩 (일반 톤백)
ANCHOR_C = """                self.db.executemany(\"\"\"
                    INSERT INTO inventory_tonbag (
                        inventory_id, lot_no, sub_lt, weight, status,
                        is_sample, created_at
                    ) VALUES (?, ?, ?, ?, 'AVAILABLE', 0, ?)
                \"\"\", _tonbag_rows)"""

PATCH_C = """                # v868: 톤백도 inventory와 동일 status (PENDING/AVAILABLE)
                _tonbag_rows_with_status = [
                    (inv_id, lot_no, sub, weight_per_bag, _safe_status, now)
                    for sub in range(1, mxbg_pallet + 1)
                ]
                self.db.executemany(\"\"\"
                    INSERT INTO inventory_tonbag (
                        inventory_id, lot_no, sub_lt, weight, status,
                        is_sample, created_at
                    ) VALUES (?, ?, ?, ?, ?, 0, ?)
                \"\"\", _tonbag_rows_with_status)"""

# (1-D) inventory_tonbag INSERT 샘플 톤백 'AVAILABLE' 하드코딩 → _safe_status 바인딩
ANCHOR_D = """                self.db.execute(\"\"\"
                    INSERT INTO inventory_tonbag (
                        inventory_id, lot_no, sub_lt, weight, status,
                        is_sample, created_at
                    ) VALUES (?, ?, 0, ?, 'AVAILABLE', 1, ?)
                \"\"\", (inv_id, lot_no, SAMPLE_WEIGHT_KG, now))"""

PATCH_D = """                self.db.execute(\"\"\"
                    INSERT INTO inventory_tonbag (
                        inventory_id, lot_no, sub_lt, weight, status,
                        is_sample, created_at
                    ) VALUES (?, ?, 0, ?, ?, 1, ?)
                \"\"\", (inv_id, lot_no, SAMPLE_WEIGHT_KG, _safe_status, now))"""

# (1-E) add_inventory_from_dict의 allowed set에 status 추가 + 주석 수정
ANCHOR_E = """        # add_inventory가 받지 않는 키 제거 (location, remark, status는 INSERT에 없음)
        allowed = {
            'lot_no', 'sap_no', 'bl_no', 'container_no', 'product', 'product_code',
            'mxbg_pallet', 'net_weight', 'gross_weight', 'warehouse', 'arrival_date', 'stock_date',
            'lot_sqm', 'folio', 'vessel', 'salar_invoice_no', 'ship_date', 'con_return', 'free_time', 'initial_weight', 'current_weight',
            'packing_type',
        }"""

PATCH_E = """        # v868 PENDING 워크플로우: status 화이트리스트에 추가 (PDF 입고는 PENDING 전달 필요)
        # add_inventory가 받지 않는 키 제거 (location, remark는 INSERT에 없음)
        allowed = {
            'lot_no', 'sap_no', 'bl_no', 'container_no', 'product', 'product_code',
            'mxbg_pallet', 'net_weight', 'gross_weight', 'warehouse', 'arrival_date', 'stock_date',
            'lot_sqm', 'folio', 'vessel', 'salar_invoice_no', 'ship_date', 'con_return', 'free_time', 'initial_weight', 'current_weight',
            'packing_type', 'status',
        }"""


# ────────────────────────────────────────────────────────────
# 패치 2: backend/api/inbound.py — PDF 입고 시 status='PENDING' 전달
# ────────────────────────────────────────────────────────────
INBOUND = ROOT / "backend" / "api" / "inbound.py"

ANCHOR_F = """                    for idx, lot in enumerate(getattr(parsed, "lots", []) or []):
                        lot_data = dict(common)
                        lot_data.update(lot or {})
                        if not lot_data.get("lot_no"):
                            save_errors.append({"index": idx, "reason": "lot_no 없음"})
                            continue
                        try:
                            result = engine.add_inventory_from_dict(lot_data)"""

PATCH_F = """                    for idx, lot in enumerate(getattr(parsed, "lots", []) or []):
                        lot_data = dict(common)
                        lot_data.update(lot or {})
                        if not lot_data.get("lot_no"):
                            save_errors.append({"index": idx, "reason": "lot_no 없음"})
                            continue
                        # v868 PENDING 워크플로우 (053fa7a): PDF 스캔 입고는 포트 입항 단계 → PENDING
                        # 사용자가 Pending 탭에서 입고 확정해야 AVAILABLE로 전환 (POST /api/inbound/confirm/{lot})
                        lot_data["status"] = "PENDING"
                        try:
                            result = engine.add_inventory_from_dict(lot_data)"""


def apply_patch(file_path: Path, anchor: str, patch: str, label: str) -> bool:
    """단일 패치 적용 — 멱등성 + 검증"""
    text = file_path.read_text(encoding="utf-8")
    # 멱등성 체크
    if patch in text:
        print(f"  [SKIP] {label} — already patched.")
        return True
    if anchor not in text:
        print(f"  [ERROR] {label} — anchor not found.")
        return False
    if text.count(anchor) > 1:
        print(f"  [ERROR] {label} — anchor matched {text.count(anchor)} times (ambiguous).")
        return False
    new_text = text.replace(anchor, patch, 1)
    file_path.write_text(new_text, encoding="utf-8")
    print(f"  [OK] {label} applied.")
    return True


def main() -> int:
    if not CRUD.exists() or not INBOUND.exists():
        print(f"[ERROR] target file missing", file=sys.stderr)
        return 1

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 백업
    bk_crud = CRUD.with_suffix(f".py.bak_status_{ts}")
    bk_inb = INBOUND.with_suffix(f".py.bak_status_{ts}")
    shutil.copy2(CRUD, bk_crud)
    shutil.copy2(INBOUND, bk_inb)
    print(f"[INFO] backup: {bk_crud.name}, {bk_inb.name}")

    print("\n=== Patch 1: crud_mixin.py ===")
    ok = True
    ok &= apply_patch(CRUD, ANCHOR_A, PATCH_A, "(A) signature +status")
    ok &= apply_patch(CRUD, ANCHOR_B, PATCH_B, "(B) inventory INSERT")
    ok &= apply_patch(CRUD, ANCHOR_C, PATCH_C, "(C) inventory_tonbag bulk INSERT")
    ok &= apply_patch(CRUD, ANCHOR_D, PATCH_D, "(D) inventory_tonbag sample INSERT")
    ok &= apply_patch(CRUD, ANCHOR_E, PATCH_E, "(E) add_inventory_from_dict allowed +status")

    print("\n=== Patch 2: backend/api/inbound.py ===")
    ok &= apply_patch(INBOUND, ANCHOR_F, PATCH_F, "(F) PDF 입고 status='PENDING' 전달")

    if not ok:
        print("\n[FAIL] one or more patches failed. restore from backup if needed.", file=sys.stderr)
        return 2

    # syntax 검증
    import py_compile
    try:
        py_compile.compile(str(CRUD), doraise=True)
        py_compile.compile(str(INBOUND), doraise=True)
        print("\n[OK] py_compile passed for both files.")
    except py_compile.PyCompileError as e:
        print(f"\n[FAIL] syntax error after patch: {e}", file=sys.stderr)
        return 3

    print("\n🎉 ALL PATCHES APPLIED SUCCESSFULLY")
    return 0


if __name__ == "__main__":
    sys.exit(main())
