from pathlib import Path

ROOT = Path.cwd()


def replace_once(path, old, new):
    p = ROOT / path
    text = p.read_text(encoding='utf-8')
    if old not in text:
        raise SystemExit(f'Pattern not found in {path}: {old[:80]!r}')
    text = text.replace(old, new, 1)
    p.write_text(text, encoding='utf-8', newline='')
    print(f'patched {path}')

# 1) backend KPI: add current stock MT, previous day stock MT, explicit unassigned tonbag alias.
backend = ROOT / 'backend/api/dashboard.py'
text = backend.read_text(encoding='utf-8')
old = '''        # ③ 현재 재고 LOT 수 (출고/반품/판매 완료 제외)
        cur.execute("""
            SELECT COUNT(DISTINCT lot_no)
            FROM inventory
            WHERE status NOT IN ('SOLD', 'RETURNED', 'PENDING')
        """)
        current_stock_lots = int(cur.fetchone()[0] or 0)

        # ④ 위치 미배정 톤백 수 (출고/판매 제외, location 없음)
        cur.execute("""
            SELECT COUNT(*)
            FROM inventory_tonbag
            WHERE (location IS NULL OR TRIM(location) = '')
              AND status NOT IN ('SOLD', 'RETURNED', 'PENDING')
        """)
        unassigned_locations = int(cur.fetchone()[0] or 0)

        return {
            "today_inbound_mt":     today_inbound_mt,
            "today_outbound_mt":    today_outbound_mt,
            "current_stock_lots":   current_stock_lots,
            "unassigned_locations": unassigned_locations,
        }
'''
new = '''        # ③ 현재 재고 LOT 수 (기존 호환 필드)
        cur.execute("""
            SELECT COUNT(DISTINCT lot_no)
            FROM inventory
            WHERE status NOT IN ('SOLD', 'RETURNED', 'PENDING')
        """)
        current_stock_lots = int(cur.fetchone()[0] or 0)

        # ④ 현재 재고 중량 (MT) - 창고 재고 흐름 KPI 기준
        # AVAILABLE/RESERVED/RETURN 은 현재 창고 재고로 보고, PICKED/SOLD/PENDING 은 제외한다.
        cur.execute("""
            SELECT COALESCE(SUM(weight), 0) / 1000.0
            FROM inventory_tonbag
            WHERE status IN ('AVAILABLE', 'RESERVED', 'RETURN')
        """)
        current_stock_mt = round(float(cur.fetchone()[0] or 0.0), 3)

        # ⑤ 전일 재고 (MT) = 현재 재고 - 오늘 입고 + 오늘 출고
        previous_stock_mt = round(current_stock_mt - today_inbound_mt + today_outbound_mt, 3)

        # ⑥ 위치 미배정 톤백 수 (입고되어 있으나 엑셀/창고 위치가 비어 있는 톤백)
        cur.execute("""
            SELECT COUNT(*)
            FROM inventory_tonbag
            WHERE (location IS NULL OR TRIM(location) = '')
              AND status IN ('AVAILABLE', 'RESERVED', 'RETURN')
        """)
        unassigned_tonbags = int(cur.fetchone()[0] or 0)

        return {
            "previous_stock_mt":    previous_stock_mt,
            "today_inbound_mt":     today_inbound_mt,
            "today_outbound_mt":    today_outbound_mt,
            "current_stock_mt":     current_stock_mt,
            "current_stock_lots":   current_stock_lots,
            "unassigned_tonbags":   unassigned_tonbags,
            # Backward-compatible key used by older frontend bundles.
            "unassigned_locations": unassigned_tonbags,
        }
'''
if old not in text:
    raise SystemExit('backend KPI block not found')
text = text.replace(old, new, 1)
text = text.replace('''                "today_inbound_mt":     0.0,
                "today_outbound_mt":    0.0,
                "current_stock_lots":   0,
                "unassigned_locations": 0,
                "updated_at":           now_str,
''', '''                "previous_stock_mt":    0.0,
                "today_inbound_mt":     0.0,
                "today_outbound_mt":    0.0,
                "current_stock_mt":     0.0,
                "current_stock_lots":   0,
                "unassigned_tonbags":   0,
                "unassigned_locations": 0,
                "updated_at":           now_str,
''', 1)
backend.write_text(text, encoding='utf-8', newline='')
print('patched backend/api/dashboard.py')

# 2) index cards: reorder and expand to 5 cards.
old_cards = '''      <div id="kpi-row" class="kpi-row">
        <div class="kpi-card" id="kpi-inbound"><div class="kpi-icon">📥</div><div class="kpi-label">오늘 입고 (MT)</div><div class="kpi-value" id="kpi-inbound-val">--</div></div>
        <div class="kpi-card" id="kpi-outbound-today"><div class="kpi-icon">📤</div><div class="kpi-label">오늘 출고 (MT)</div><div class="kpi-value" id="kpi-outbound-today-val">--</div></div>
        <div class="kpi-card" id="kpi-stock-lots"><div class="kpi-icon">📦</div><div class="kpi-label">현재 재고 LOT</div><div class="kpi-value" id="kpi-stock-lots-val">--</div></div>
        <div class="kpi-card" id="kpi-unassigned"><div class="kpi-icon">📍</div><div class="kpi-label">위치 미배정</div><div class="kpi-value" id="kpi-unassigned-val">--</div></div>
      </div>
'''
new_cards = '''      <div id="kpi-row" class="kpi-row">
        <div class="kpi-card" id="kpi-prev-stock"><div class="kpi-icon">📊</div><div class="kpi-label">전일 재고 (MT)</div><div class="kpi-value" id="kpi-prev-stock-val">--</div></div>
        <div class="kpi-card" id="kpi-inbound"><div class="kpi-icon">📥</div><div class="kpi-label">오늘 입고 (MT)</div><div class="kpi-value" id="kpi-inbound-val">--</div></div>
        <div class="kpi-card" id="kpi-outbound-today"><div class="kpi-icon">📤</div><div class="kpi-label">오늘 출고 (MT)</div><div class="kpi-value" id="kpi-outbound-today-val">--</div></div>
        <div class="kpi-card" id="kpi-current-stock"><div class="kpi-icon">📦</div><div class="kpi-label">현재 재고 (MT)</div><div class="kpi-value" id="kpi-current-stock-val">--</div></div>
        <div class="kpi-card" id="kpi-unassigned"><div class="kpi-icon">📍</div><div class="kpi-label">미배정 톤백</div><div class="kpi-value" id="kpi-unassigned-val">--</div></div>
      </div>
'''
replace_once('frontend/index.html', old_cards, new_cards)

# bump cache versions for changed JS bundles.
index = ROOT / 'frontend/index.html'
idx = index.read_text(encoding='utf-8')
idx = idx.replace('js/sqm-core.js?v=20260517p22', 'js/sqm-core.js?v=20260518kpi1')
idx = idx.replace('js/sqm-inline.js?v=20260517p29', 'js/sqm-inline.js?v=20260518kpi1')
index.write_text(idx, encoding='utf-8', newline='')
print('bumped JS cache versions')

# 3) frontend KPI binding in both JS bundles.
old_js = '''      sv('kpi-inbound-val',        d.today_inbound_mt    !== undefined ? d.today_inbound_mt    : (d.inbound_today   || d.inbound   || '-'));
      sv('kpi-outbound-today-val', d.today_outbound_mt   !== undefined ? d.today_outbound_mt   : (d.outbound_today  || d.outbound  || '-'));
      sv('kpi-stock-lots-val',     d.current_stock_lots  !== undefined ? d.current_stock_lots  : (d.stock_lots      || d.lots      || '-'));
      sv('kpi-unassigned-val',     d.unassigned_locations !== undefined ? d.unassigned_locations : (d.unassigned_bags || d.unassigned|| '-'));
'''
new_js = '''      sv('kpi-prev-stock-val',     d.previous_stock_mt   !== undefined ? d.previous_stock_mt   : '-');
      sv('kpi-inbound-val',        d.today_inbound_mt    !== undefined ? d.today_inbound_mt    : (d.inbound_today   || d.inbound   || '-'));
      sv('kpi-outbound-today-val', d.today_outbound_mt   !== undefined ? d.today_outbound_mt   : (d.outbound_today  || d.outbound  || '-'));
      sv('kpi-current-stock-val',  d.current_stock_mt    !== undefined ? d.current_stock_mt    : (d.current_stock_lots || d.stock_lots || d.lots || '-'));
      sv('kpi-unassigned-val',     d.unassigned_tonbags  !== undefined ? d.unassigned_tonbags  : (d.unassigned_locations !== undefined ? d.unassigned_locations : (d.unassigned_bags || d.unassigned || '-')));
'''
for js in ['frontend/js/sqm-core.js', 'frontend/js/sqm-inline.js']:
    replace_once(js, old_js, new_js)

print('dashboard KPI flow patch complete')
