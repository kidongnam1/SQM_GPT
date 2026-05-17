"""
patch_restore_available_20col.py
Available 페이지 헤더를 구버전 20컬럼으로 복원

변경 내용:
  현재 15컬럼 (☑ # LOT ⋯ SAP BL Product Container Vessel MXBG NET Status ↩️ Arrival WH)
  →  원본 20컬럼 (# LOT SAP BL Product Status Balance Avail/Rsv NET Container MXBG Avail Invoice Ship Arrival WH Customs Inbound Location [action])

대상 파일: frontend/js/sqm-inventory.js  (1277줄, IIFE — Edit 툴 금지, 스크립트로만)
"""
import re, shutil, sys, os
from pathlib import Path
from datetime import datetime

TARGET = Path(r"D:\program\SQM_inventory\SQM_v868_claan\frontend\js\sqm-inventory.js")

# ── 백업 ────────────────────────────────────────────────────────────────
ts = datetime.now().strftime("%Y%m%d_%H%M%S")
backup = TARGET.with_name(f"sqm-inventory.js.bak_{ts}")
shutil.copy2(TARGET, backup)
print(f"[backup] {backup.name}")

src = TARGET.read_text(encoding="utf-8")

# ── 교체 앵커 ───────────────────────────────────────────────────────────
# 함수 시작 ~ window.loadAvailablePage = loadAvailablePage; 직전까지 교체
START = "  function loadAvailablePage() {"
END   = "  window.loadAvailablePage = loadAvailablePage;"

idx_start = src.find(START)
idx_end   = src.find(END)

if idx_start == -1 or idx_end == -1:
    print("[ERROR] 앵커 문자열을 찾지 못했습니다. 파일을 확인하세요.")
    sys.exit(1)

print(f"[found] loadAvailablePage()  lines approx {src[:idx_start].count(chr(10))+1} ~ {src[:idx_end].count(chr(10))+1}")

# ── 새 함수 본문 ────────────────────────────────────────────────────────
NEW_FUNC = r"""  function loadAvailablePage() {
    var route = 'available';
    if (window.getCurrentRoute() !== route) return;
    var c = document.getElementById('page-container');
    if (!c) return;
    c.innerHTML = '<div class="loading-spinner" style="padding:40px;text-align:center;color:var(--text-muted)">⏳ Available 재고 로딩 중...</div>';

    apiGet('/api/inventory?status=AVAILABLE&limit=5000').then(function(res) {
      if (window.getCurrentRoute() !== route) return;
      var rows = Array.isArray(res) ? res : (res.data || res.rows || res.items || []);
      if (!rows.length) {
        c.innerHTML = '<div class="empty" style="padding:60px;text-align:center;color:var(--text-muted,#888)">✅ Available 재고 없음 (전량 배분 또는 피킹 완료)</div>';
        return;
      }
      var sumBal = 0, sumNet = 0, sumIni = 0, sumOb = 0;
      rows.forEach(function(r) {
        if (r.balance      != null && !isNaN(Number(r.balance)))      sumBal += Number(r.balance);
        if (r.net          != null && !isNaN(Number(r.net)))          sumNet += Number(r.net);
        if (r.initial_weight  != null) sumIni += Number(r.initial_weight);
        if (r.outbound_weight != null) sumOb  += Number(r.outbound_weight);
      });
      var html = '<section style="padding:12px 16px">'
        + '<div style="display:flex;align-items:center;gap:12px;margin-bottom:8px;flex-wrap:wrap">'
        + '<h2 style="margin:0;font-size:16px;color:#22c55e">✅ Available 재고 — 판매 가능 물량</h2>'
        + '<span style="font-size:12px;color:var(--text-muted)">' + rows.length + ' LOT · Balance ' + fmtN(sumBal) + ' MT</span>'
        + '<button class="btn btn-ghost" style="font-size:12px;margin-left:auto" onclick="window.loadAvailablePage()">🔄 새로고침</button>'
        + '</div>'
        + '<div style="overflow-x:auto"><table class="data-table"><thead><tr>'
        + '<th>#</th><th style="text-align:left !important">LOT</th><th>SAP</th><th>BL</th><th>Product</th>'
        + '<th>Status</th><th>Balance(MT)</th><th>Avail/Rsv(MT)</th><th>NET(MT)</th><th>Container</th>'
        + '<th>MXBG</th><th>Avail</th><th>Invoice</th>'
        + '<th>Ship</th><th>Arrival</th><th>WH</th><th>Customs</th>'
        + '<th>Inbound(MT)</th><th>Location</th><th></th>'
        + '</tr></thead><tbody>';
      html += rows.map(function(r, i) {
        var lotKey = escapeHtml(r.lot||'');
        var hasSample = (r.sample_bags > 0);
        var parentContainer = escapeHtml(r.container || '-');
        var sampleRow = '';
        if (hasSample) {
          sampleRow =
            '<tr style="background:rgba(234,179,8,0.08);border-left:3px solid #eab308">' +
            '<td class="mono-cell" style="color:#eab308;text-align:center;padding:6px 10px">🔬</td>' +
            '<td class="mono-cell cell-left" style="color:#eab308;font-weight:700;padding:6px 10px">' + lotKey + '(SP)</td>' +
            '<td class="mono-cell" style="color:#94a3b8">' + escapeHtml(r.sap||'') + '</td>' +
            '<td class="mono-cell" style="color:#94a3b8">' + escapeHtml(r.bl||'') + '</td>' +
            '<td><span class="tag" style="background:rgba(234,179,8,0.2);color:#eab308">' + escapeHtml(r.product||'') + '</span></td>' +
            '<td style="color:#eab308;font-weight:600">SAMPLE</td>' +
            '<td class="mono-cell" style="text-align:right;color:#eab308;font-weight:600">' + fmtN(r.sample_weight_mt||0) + '</td>' +
            '<td class="mono-cell" style="text-align:right;color:#eab308">' + fmtN(r.sample_weight_mt||0) + '</td>' +
            '<td class="mono-cell" style="text-align:right;color:#eab308">' + fmtN(r.sample_weight_mt||0) + '</td>' +
            '<td class="mono-cell" style="color:#94a3b8">' + parentContainer + '</td>' +
            '<td class="mono-cell" style="text-align:center;color:#eab308;font-weight:700">' + r.sample_bags + '</td>' +
            '<td class="mono-cell" style="text-align:center;color:#eab308;font-weight:700">' + r.sample_bags + '</td>' +
            '<td colspan="7" style="color:#555">—</td>' +
            '<td></td>' +
            '</tr>';
        }
        var lotSafe = (r.lot||'').replace(/\\/g,'\\\\').replace(/'/g,"\\'");
        var mainRow =
          '<tr style="' + (hasSample ? 'border-left:3px solid #22c55e' : '') + '">'
          + '<td class="mono-cell" style="color:var(--text-muted)">' + (i+1) + '</td>'
          + '<td class="mono-cell cell-left" style="color:var(--accent);font-weight:600;padding:6px 10px">' + lotKey + '</td>'
          + '<td class="mono-cell">' + escapeHtml(r.sap||'') + '</td>'
          + '<td class="mono-cell">' + escapeHtml(r.bl||'') + '</td>'
          + '<td><span class="tag">' + escapeHtml(r.product||'') + '</span></td>'
          + '<td><span class="tag" style="background:rgba(34,197,94,0.15);color:#22c55e">✅ AVAILABLE</span></td>'
          + '<td class="mono-cell" style="text-align:right">' + (r.balance!=null?fmtN(r.balance):'-') + '</td>'
          + '<td class="mono-cell" style="text-align:right">'
            + '<span style="color:#22c55e;font-weight:700">' + (r.avail_mt!=null?fmtN(r.avail_mt):'-') + '</span>'
            + '<span style="color:#94a3b8;font-size:11px"> / </span>'
            + '<span style="color:#3b82f6">' + (r.reserved_mt!=null&&r.reserved_mt>0?'▲'+fmtN(r.reserved_mt):'0') + '</span>'
          + '</td>'
          + '<td class="mono-cell" style="text-align:right">' + (r.net!=null?fmtN(r.net):'-') + '</td>'
          + '<td class="mono-cell">' + escapeHtml(r.container||'') + '</td>'
          + '<td class="mono-cell" style="text-align:center">'
            + (r.mxbg_pallet > 0
              ? '<button class="btn btn-ghost btn-xs" style="font-weight:700;color:var(--accent)" '
                + 'data-lot="' + lotKey + '" onclick="window.showTonbagModal(this.dataset.lot)" title="톤백 상세 보기">' + r.mxbg_pallet + '</button>'
              : '-')
          + '</td>'
          + '<td class="mono-cell" style="text-align:center">' + (r.avail_bags!=null?r.avail_bags:'-') + '</td>'
          + '<td class="mono-cell">' + escapeHtml(r.invoice_no||'') + '</td>'
          + '<td class="mono-cell">' + escapeHtml((r.ship_date||'').slice(0,10)) + '</td>'
          + '<td class="mono-cell">' + escapeHtml((r.arrival_date||'').slice(0,10)) + '</td>'
          + '<td class="mono-cell">' + escapeHtml(r.wh||'') + '</td>'
          + '<td class="mono-cell">' + escapeHtml(r.customs||'') + '</td>'
          + '<td class="mono-cell" style="text-align:right">' + (r.initial_weight!=null?fmtN(r.initial_weight):'-') + '</td>'
          + '<td><span class="tag">' + escapeHtml(r.location||'-') + '</span></td>'
          + '<td style="white-space:nowrap;padding:6px 10px">'
            + '<button class="btn btn-ghost btn-xs" data-lot="' + lotKey + '" onclick="window.showInvActionMenu(this)" style="font-size:15px;padding:0 4px" title="추가기능">⋯</button> '
            + '<button class="btn btn-ghost btn-xs" onclick="window.revertToPending(\'' + lotSafe + '\')" title="입고 취소 → PENDING" style="color:#f59e0b;font-size:13px;padding:1px 5px;border:1px solid #f59e0b55">↩️</button>'
          + '</td>'
          + '</tr>';
        return mainRow + sampleRow;
      }).join('');
      html += '</tbody><tfoot><tr style="background:var(--panel);font-weight:700">';
      html += '<td colspan="6" style="text-align:right;padding:8px 10px">합계 (' + rows.length + ' LOT)</td>';
      html += '<td class="mono-cell" style="text-align:right">' + fmtN(sumBal) + '</td>';
      html += '<td></td>';
      html += '<td class="mono-cell" style="text-align:right">' + fmtN(sumNet) + '</td>';
      html += '<td colspan="8"></td>';
      html += '<td class="mono-cell" style="text-align:right">' + fmtN(sumIni) + '</td>';
      html += '<td colspan="2"></td>';
      html += '</tr></tfoot></table></div></section>';
      c.innerHTML = html;
    }).catch(function(e) {
      if (window.getCurrentRoute() !== route) return;
      c.innerHTML = '<div class="empty" style="padding:40px;text-align:center">Load failed: ' + escapeHtml(e.message||String(e)) + '</div>';
      showToast('error', 'Available 로드 실패');
    });
  }
"""

# ── 문자열 치환 ─────────────────────────────────────────────────────────
new_src = src[:idx_start] + NEW_FUNC + "\n  " + src[idx_end:]

TARGET.write_text(new_src, encoding="utf-8")
print(f"[done] {TARGET.name} 저장 완료")

# ── 라인 수 검증 ────────────────────────────────────────────────────────
old_lines = src.count("\n")
new_lines = new_src.count("\n")
print(f"[lines] {old_lines} → {new_lines}  (diff {new_lines - old_lines:+d})")

# ── IIFE 닫힘 확인 ──────────────────────────────────────────────────────
tail = new_src[-200:]
if "})();" in tail or "} )();" in tail or "}());" in tail:
    print("[ok] IIFE 닫힘 확인 ✅")
else:
    print("[WARN] IIFE 닫힘 문자열 미확인 — 마지막 200자 수동 확인 필요")
    print(repr(tail[-100:]))
