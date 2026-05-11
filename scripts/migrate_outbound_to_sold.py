"""
OUTBOUND → SOLD 상태 통합 마이그레이션 스크립트
실행: python scripts/migrate_outbound_to_sold.py
"""
import re
import os

TARGET_FILES = [
    "engine_modules/inventory_modular/outbound_mixin.py",
    "engine_modules/inventory_modular/return_mixin.py",
    "engine_modules/inventory_modular/query_mixin.py",
    "engine_modules/inventory_modular/export_mixin.py",
    "engine_modules/inventory_modular/crud_mixin.py",
    "engine_modules/inventory_modular/preflight_mixin.py",
    "engine_modules/inventory_modular/tonbag_mixin.py",
    "engine_modules/inventory_modular/integrity_mixin.py",
    "engine_modules/constants.py",
    "engine_modules/preflight.py",
    "engine_modules/audit_helper.py",
    "engine_modules/return_reinbound_engine.py",
    "engine_modules/validators.py",
    "engine_modules/db_schema_mixin.py",
    "engine_modules/db_migration_mixin.py",
    "core/barcode_scan_engine.py",
    "core/constants.py",
    "core/formatters.py",
    "core/column_registry.py",
    "features/parsers/sales_order_engine.py",
    "features/parsers/picking_list_parser.py",
    "features/parsers/return_inbound_engine.py",
    "backend/api/outbound_api.py",
    "backend/api/actions2.py",
    "backend/api/allocation_api.py",
    "backend/api/dashboard.py",
    "backend/api/queries.py",
    "backend/api/queries2.py",
    "backend/api/queries3.py",
    "backend/api/scan_api.py",
    "backend/api/inventory_api.py",
    "backend/api/info.py",
    "backend/api/actions.py",
    "backend/api/actions3.py",
    "backend/api/__init__.py",
    "backend/api/refresh_excel_api.py",
    "gui_app_modular/tabs/allocation_tab.py",
    "gui_app_modular/tabs/dashboard_data_mixin.py",
    "gui_app_modular/tabs/inventory_tab.py",
    "gui_app_modular/tabs/scan_tab.py",
    "gui_app_modular/tabs/outbound_scheduled_tab.py",
    "gui_app_modular/tabs/sold_tab.py",
    "gui_app_modular/tabs/allocation_lot_overview_mixin.py",
    "gui_app_modular/handlers/outbound_handlers.py",
    "gui_app_modular/handlers/status_import_handlers.py",
    "gui_app_modular/dialogs/lot_status_dialog.py",
    "gui_app_modular/dialogs/onestop_outbound.py",
    "gui_app_modular/dialogs/lot_detail_dialog.py",
    "gui_app_modular/dialogs/allocation_dialog.py",
    "gui_app_modular/mixins/advanced_features_mixin.py",
    "gui_app_modular/mixins/custom_menubar.py",
    "gui_app_modular/mixins/menu_mixin.py",
    "gui_app_modular/mixins/toolbar_mixin.py",
    "gui_app_modular/utils/ui_constants.py",
    "parsers/allocation_parser.py",
    "parsers/document_models.py",
    "config.py",
    "version.py",
    "engine_modules/inventory_modular/adjust_executor.py",
    "engine_modules/return_reinbound_engine.py",
]

def replace_outbound_status(text: str) -> str:
    # 1. SQL SET status 직접 대입
    text = re.sub(r"(SET\s+status\s*=\s*)'OUTBOUND'", r"\1'SOLD'", text)
    text = re.sub(r'(SET\s+status\s*=\s*)"OUTBOUND"', r'\1"SOLD"', text)

    # 2. Python 변수 대입 status='OUTBOUND'
    text = re.sub(r"(\bstatus\s*=\s*)'OUTBOUND'", r"\1'SOLD'", text)
    text = re.sub(r'(\bstatus\s*=\s*)"OUTBOUND"', r'\1"SOLD"', text)

    # 3. SQL IN 절 중복 제거 ('SOLD', 'OUTBOUND') → ('SOLD')
    text = re.sub(r"'SOLD',\s*'OUTBOUND'", "'SOLD'", text)
    text = re.sub(r"'OUTBOUND',\s*'SOLD'", "'SOLD'", text)
    # IN 절 내 단독 OUTBOUND 제거
    text = re.sub(r",\s*'OUTBOUND'(\s*(?:[,\)]))", r"\1", text)
    text = re.sub(r"'OUTBOUND',\s*(?=')", "", text)

    # 4. Python set/tuple 내 중복 제거
    text = re.sub(r'"SOLD",\s*"OUTBOUND"', '"SOLD"', text)
    text = re.sub(r'"OUTBOUND",\s*"SOLD"', '"SOLD"', text)
    text = re.sub(r',\s*"OUTBOUND"(\s*[,}\]])', r'\1', text)
    text = re.sub(r'"OUTBOUND",\s*(?=")', '', text)

    # 5. 비교 연산자
    text = re.sub(r"((?:==|!=|in|not\s+in)\s*)'OUTBOUND'", r"\1'SOLD'", text)
    text = re.sub(r'((?:==|!=|in|not\s+in)\s*)"OUTBOUND"', r'\1"SOLD"', text)

    # 6. event_type OUTBOUND_SOLD → SOLD
    text = re.sub(r"'OUTBOUND_SOLD'", "'SOLD'", text)
    text = re.sub(r'"OUTBOUND_SOLD"', '"SOLD"', text)

    # 7. label/color 정의에서 'OUTBOUND' 키 → 'SOLD' (딕셔너리 키로 사용된 경우)
    text = re.sub(r"'OUTBOUND'\s*:", "'SOLD':", text)
    text = re.sub(r'"OUTBOUND"\s*:', '"SOLD":', text)

    return text

def process_file(path: str) -> bool:
    if not os.path.exists(path):
        return False
    with open(path, encoding='utf-8', errors='ignore') as f:
        original = f.read()
    updated = replace_outbound_status(original)
    if original == updated:
        return False
    with open(path, 'w', encoding='utf-8') as f:
        f.write(updated)
    changed = sum(1 for a, b in zip(original.splitlines(), updated.splitlines()) if a != b)
    print(f"  UPDATED ({changed}줄): {path}")
    return True

if __name__ == "__main__":
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(root)
    total = 0
    for p in TARGET_FILES:
        if process_file(p):
            total += 1
    print(f"\n완료: {total}개 파일 수정됨")
