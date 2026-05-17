import sqlite3
con = sqlite3.connect("data/db/sqm_inventory.db")
cur = con.cursor()

# HAPAG hints — bl_mixin.py 의 HAPAG 좌표 파싱 실패 시 AI fallback 에서 사용됨
HAPAG_PACKING = """HAPAG-LLOYD PackingList 특이사항 (SQM 고정 양식 위에서 좌표 파싱 보조):
- LOT 번호는 'NO LOTES' 열의 10자리 숫자 (1126 으로 시작, 예: 1126021720).
- mxbg(헤백 수)는 'MAXIBAGS' 또는 'BAGS' 열, 일반적으로 10/컨테이너.
- 유럽식 숫자 (5.001,500 = 5001.5 kg). 콤마=소수점.
- 200 POLYPROPYLENE MAXIBAG + 100 PALLETS, NET 100,020 / GROSS 102,625 KG 표준."""

HAPAG_INVOICE = """HAPAG-LLOYD Invoice(FA/FACTURA) 특이사항 (SQM 고정 양식):
- SAP NO = 'Ref.SQM/Our Order' 필드, 22 시작 10자리 (예: 2200034659).
- LOT 목록은 'NO LOTES:' 다음 'LOT/5,001T' 형식.
- Invoice No = 'N°' 다음 5자리 (예: 17760).
- BL-AWB-CRT Number = HLCU+SCL+9자리 (예: HLCUSCL260148627).
- Vessel: '__EXPRESS' 형식 (예: BUENAVENTURA EXPRESS 2602W)."""

HAPAG_BL = """HAPAG-LLOYD Sea Waybill 특이사항 (좌표 파싱 fallback 용):
- 내부 carrier_id = 'HAPAG' (Hapag-Lloyd 의 약칭).
- SWB-No 형식: HLCU+SCL+9자리 (예: HLCUSCL260148627). bl_mixin.py 의 HAPAG 좌표에서 추출.
- Carrier 명시: 'Hapag-Lloyd Aktiengesellschaft, Hamburg' (로고 함께).
- 컨테이너: HAMU + 공백 + 7자리 (예: HAMU 2354538). 5개/선적.
- Seal: HLK + 7자리 (예: HLK1620880).
- POD 는 환적항(BUSAN) 보다 최종 목적지(GWANGYANG) 좌표 우선."""

# HAPAG 500kg
cur.execute('''INSERT OR REPLACE INTO inbound_template
  (template_id, template_name, carrier_id, bag_weight_kg,
   gemini_hint_packing, gemini_hint_invoice, gemini_hint_bl,
   product_hint, weight_format, note, is_active,
   lot_sqm, mxbg_pallet, sap_no)
  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
  ("HAPAG_LC500", "🚢 HAPAG — 리튬카보네이트 500 kg",
   "HAPAG", 500,
   HAPAG_PACKING, HAPAG_INVOICE, HAPAG_BL,
   "LITHIUM CARBONATE", "EURO",
   "Hapag-Lloyd 500kg 헤백 (v8.6.8 신규, AI fallback 힌트)",
   1, "", 0, ""))

# HAPAG 1000kg
cur.execute('''INSERT OR REPLACE INTO inbound_template
  (template_id, template_name, carrier_id, bag_weight_kg,
   gemini_hint_packing, gemini_hint_invoice, gemini_hint_bl,
   product_hint, weight_format, note, is_active,
   lot_sqm, mxbg_pallet, sap_no)
  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
  ("HAPAG_LC1000", "🚢 HAPAG — 리튬카보네이트 1,000 kg",
   "HAPAG", 1000,
   HAPAG_PACKING, HAPAG_INVOICE, HAPAG_BL,
   "LITHIUM CARBONATE", "EURO",
   "Hapag-Lloyd 1000kg 헤백 (v8.6.8 신규)",
   1, "", 0, ""))

# MAERSK_LC1000 — 일관성 (이미 500 있고 1000 없는 상태 보완)
row = cur.execute("SELECT gemini_hint_packing, gemini_hint_invoice, gemini_hint_bl FROM inbound_template WHERE template_id='MAERSK_LC500'").fetchone()
if row:
    cur.execute('''INSERT OR REPLACE INTO inbound_template
      (template_id, template_name, carrier_id, bag_weight_kg,
       gemini_hint_packing, gemini_hint_invoice, gemini_hint_bl,
       product_hint, weight_format, note, is_active,
       lot_sqm, mxbg_pallet, sap_no)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
      ("MAERSK_LC1000", "🚢 MAERSK — 리튬카보네이트 1,000 kg",
       "MAERSK", 1000,
       row[0], row[1], row[2],
       "LITHIUM CARBONATE", "EURO",
       "MAERSK 1000kg 헤백 (v8.6.8 신규, BL은 bl_mixin.py 의 MAERSK 좌표가 9자리→MAEU 보강 처리)",
       1, "", 0, ""))

con.commit()

print("=== inbound_template 전체 (선사별 정렬) ===")
for r in cur.execute("SELECT template_id, template_name, carrier_id FROM inbound_template ORDER BY carrier_id, bag_weight_kg").fetchall():
    print(r)

print()
print("=== carrier_rules MAERSK (수정 없음 확인) ===")
for r in cur.execute("SELECT rule_name, pattern, sample_value FROM carrier_rules WHERE carrier_id='MAERSK'").fetchall():
    print(r)
