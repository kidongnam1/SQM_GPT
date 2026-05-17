# -*- coding: utf-8 -*-
"""Agent-A Patch: sqm-inventory.js — Pending 입고 확정 UI"""
from pathlib import Path

f = Path('frontend/js/sqm-inventory.js')
src = f.read_text(encoding='utf-8')
original = src

# ── Patch 1: 일괄 확정 버튼 + 헤더 컬럼 변경 ──
OLD1 = (
    "        + '<button class=\"btn btn-ghost\" style=\"font-size:12px;margin-left:auto\" onclick=\"window.loadPendingPage()\">🔄 새로고침</button>'\n"
    "        + '</div>'\n"
    "        + '<div style=\"overflow-x:auto\"><table class=\"data-table\"><thead><tr>'\n"
    "        + '<th>#</th><th>LOT</th><th>Product</th><th>Grade</th>'\n"
    "        + '<th>Qty</th><th>Unit</th><th>BL No</th><th>Vessel</th>'\n"
    "        + '<th>Arrival Date</th><th>등록일</th>'"
)
NEW1 = (
    "        + '<button class=\"btn btn-ghost\" style=\"font-size:12px;margin-left:auto\" onclick=\"window.loadPendingPage()\">🔄 새로고침</button>'\n"
    "        + '<button class=\"btn\" style=\"background:var(--accent,#3b82f6);color:#fff;font-size:12px;padding:4px 12px\" onclick=\"window.bulkConfirmPending()\">✅ 선택 일괄 확정</button>'\n"
    "        + '</div>'\n"
    "        + '<div style=\"overflow-x:auto\"><table class=\"data-table\"><thead><tr>'\n"
    "        + '<th><input type=\"checkbox\" id=\"pending-select-all\" onchange=\"window.pendingToggleAll(this)\"></th>'\n"
    "        + '<th>LOT</th><th>Product</th><th>Grade</th>'\n"
    "        + '<th>Qty</th><th>Unit</th><th>BL No</th><th>Vessel</th>'\n"
    "        + '<th>Arrival Date</th><th>등록일</th><th style=\"width:50px\">⚙️</th>'"
)
assert OLD1 in src, "Patch 1 대상을 찾지 못했습니다"
src = src.replace(OLD1, NEW1, 1)

# ── Patch 2: 각 행 첫 TD + 마지막 TD 교체 ──
OLD2 = (
    "        return '<tr>'\n"
    "          + '<td class=\"mono-cell\" style=\"color:var(--text-muted)\">' + (i+1) + '</td>'\n"
    "          + '<td class=\"mono-cell\" style=\"color:#94a3b8;font-weight:600\">' + escapeHtml(r.lot_no||'') + '</td>'\n"
    "          + '<td><span class=\"tag\">' + escapeHtml(r.product||'-') + '</span></td>'\n"
    "          + '<td class=\"mono-cell\">' + escapeHtml(r.grade||'-') + '</td>'\n"
    "          + '<td class=\"mono-cell\" style=\"text-align:right\">' + (r.quantity!=null?fmtN(r.quantity):'-') + '</td>'\n"
    "          + '<td class=\"mono-cell\">' + escapeHtml(r.unit||'-') + '</td>'\n"
    "          + '<td class=\"mono-cell\">' + escapeHtml(r.bl_no||'-') + '</td>'\n"
    "          + '<td class=\"mono-cell\">' + escapeHtml(r.vessel||'-') + '</td>'\n"
    "          + '<td class=\"mono-cell\">' + escapeHtml(r.arrival_date||'-') + '</td>'\n"
    "          + '<td class=\"mono-cell\" style=\"color:var(--text-muted)\">' + escapeHtml((r.created_at||'').slice(0,10)) + '</td>'\n"
    "          + '</tr>';"
)
NEW2 = (
    "        return '<tr>'\n"
    "          + '<td style=\"text-align:center\"><input type=\"checkbox\" class=\"pending-cb\" data-lot=\"' + escapeHtml(r.lot_no||'') + '\"></td>'\n"
    "          + '<td class=\"mono-cell\" style=\"color:#94a3b8;font-weight:600\">' + escapeHtml(r.lot_no||'') + '</td>'\n"
    "          + '<td><span class=\"tag\">' + escapeHtml(r.product||'-') + '</span></td>'\n"
    "          + '<td class=\"mono-cell\">' + escapeHtml(r.grade||'-') + '</td>'\n"
    "          + '<td class=\"mono-cell\" style=\"text-align:right\">' + (r.quantity!=null?fmtN(r.quantity):'-') + '</td>'\n"
    "          + '<td class=\"mono-cell\">' + escapeHtml(r.unit||'-') + '</td>'\n"
    "          + '<td class=\"mono-cell\">' + escapeHtml(r.bl_no||'-') + '</td>'\n"
    "          + '<td class=\"mono-cell\">' + escapeHtml(r.vessel||'-') + '</td>'\n"
    "          + '<td class=\"mono-cell\">' + escapeHtml(r.arrival_date||'-') + '</td>'\n"
    "          + '<td class=\"mono-cell\" style=\"color:var(--text-muted)\">' + escapeHtml((r.created_at||'').slice(0,10)) + '</td>'\n"
    "          + '<td style=\"text-align:center\"><button class=\"btn btn-ghost\" style=\"padding:2px 8px;font-size:13px\" '\n"
    "          + 'onclick=\"window.showPendingActionMenu(event,' + JSON.stringify(r.lot_no) + ')\">⋯</button></td>'\n"
    "          + '</tr>';"
)
assert OLD2 in src, "Patch 2 대상을 찾지 못했습니다"
src = src.replace(OLD2, NEW2, 1)

# ── Patch 3: 새 함수들 삽입 (})(); 바로 직전) ──
NEW_FUNCS = '''
  window.pendingToggleAll = function(cb) {
    document.querySelectorAll('.pending-cb').forEach(function(c){ c.checked = cb.checked; });
  };

  window.showPendingActionMenu = function(event, lotNo) {
    event.stopPropagation();
    var old = document.getElementById('pending-ctx-menu');
    if (old) old.remove();
    var menu = document.createElement('div');
    menu.id = 'pending-ctx-menu';
    menu.style.cssText = 'position:fixed;z-index:9999;background:var(--surface,#1e293b);'
      + 'border:1px solid var(--border,#334155);border-radius:8px;padding:4px 0;min-width:180px;'
      + 'box-shadow:0 4px 20px rgba(0,0,0,0.4);';
    menu.style.top = event.clientY + 'px';
    menu.style.left = (event.clientX - 180) + 'px';
    menu.innerHTML = '<div style="padding:8px 16px;cursor:pointer;font-size:13px;color:var(--text)"'
      + ' onmouseenter="this.style.background=\'var(--border,#334155)\'" onmouseleave="this.style.background=\'\'"'
      + ' onclick="window.showPendingConfirmModal(\'' + escapeHtml(lotNo) + '\');document.getElementById(\'pending-ctx-menu\').remove()">\\u2705 AVAILABLE \\uc785\\uace0 \\ud655\\uc815</div>'
      + '<div style="padding:8px 16px;cursor:pointer;font-size:13px;color:var(--text-muted)"'
      + ' onmouseenter="this.style.background=\'var(--border,#334155)\'" onmouseleave="this.style.background=\'\'"'
      + ' onclick="window.invShowLotHistory(\'' + escapeHtml(lotNo) + '\');document.getElementById(\'pending-ctx-menu\').remove()">\\ud83d\\udcca LOT \\uc774\\ub825 \\ubcf4\\uae30</div>';
    document.body.appendChild(menu);
    setTimeout(function(){
      document.addEventListener('click', function rm(){ menu.remove(); document.removeEventListener('click', rm); });
    }, 0);
  };

  window.showPendingConfirmModal = function(lotNo) {
    var today = new Date().toISOString().slice(0, 10);
    var ov = document.createElement('div');
    ov.id = 'pending-confirm-overlay';
    ov.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,0.6);z-index:10000;display:flex;align-items:center;justify-content:center';
    ov.innerHTML = '<div style="background:var(--surface,#1e293b);border:1px solid var(--border,#334155);'
      + 'border-radius:12px;padding:24px;min-width:320px;max-width:400px">'
      + '<h3 style="margin:0 0 16px;font-size:15px;color:var(--text)">\u2705 \uc785\uace0 \ud655\uc815</h3>'
      + '<div style="margin-bottom:8px;font-size:13px;color:var(--text-muted)">LOT: <span style="color:var(--text);font-family:monospace">' + escapeHtml(lotNo) + '</span></div>'
      + '<label style="font-size:13px;color:var(--text-muted);display:block;margin-bottom:6px">\uc785\uace0 \ud655\uc815\uc77c (YYYY-MM-DD)</label>'
      + '<input id="pending-confirm-date" type="date" value="' + today + '" max="' + today + '"'
      + ' style="width:100%;box-sizing:border-box;padding:8px;background:var(--bg,#0f172a);border:1px solid var(--border,#334155);'
      + 'border-radius:6px;color:var(--text);font-size:14px;margin-bottom:16px">'
      + '<div style="display:flex;gap:8px;justify-content:flex-end">'
      + '<button class="btn btn-ghost" onclick="document.getElementById(\'pending-confirm-overlay\').remove()">\ucde8\uc18c</button>'
      + '<button class="btn btn-primary" onclick="window.executePendingConfirm(\'' + escapeHtml(lotNo) + '\')">\ud655\uc815</button>'
      + '</div></div>';
    document.body.appendChild(ov);
    setTimeout(function(){ var d = document.getElementById('pending-confirm-date'); if (d) d.focus(); }, 50);
  };

  window.executePendingConfirm = function(lotNo) {
    var dateEl = document.getElementById('pending-confirm-date');
    var inboundDate = dateEl ? dateEl.value : '';
    if (!inboundDate || !/^\\d{4}-\\d{2}-\\d{2}$/.test(inboundDate)) {
      showToast('error', '\ub0a0\uc9dc\ub97c \uc62c\ubc14\ub974\uac8c \uc785\ub825\ud574 \uc8fc\uc138\uc694 (YYYY-MM-DD)'); return;
    }
    if (inboundDate > new Date().toISOString().slice(0, 10)) {
      showToast('error', '\ubbf8\ub798 \ub0a0\uc9dc\ub294 \uc785\ub825\ud560 \uc218 \uc5c6\uc2b5\ub2c8\ub2e4'); return;
    }
    var ov = document.getElementById('pending-confirm-overlay');
    if (ov) ov.remove();
    apiPost('/api/inbound/confirm/' + encodeURIComponent(lotNo), { inbound_date: inboundDate })
      .then(function() {
        showToast('success', '\u2705 ' + lotNo + ' \uc785\uace0 \ud655\uc815 \uc644\ub8cc');
        window.loadPendingPage();
        setTimeout(function() { if (window.navigate) window.navigate('available'); }, 3000);
      })
      .catch(function(e) { showToast('error', '\uc785\uace0 \ud655\uc815 \uc2e4\ud328: ' + (e.message || e)); });
  };

  window.bulkConfirmPending = function() {
    var checked = Array.from(document.querySelectorAll('.pending-cb:checked')).map(function(c) { return c.dataset.lot; });
    if (!checked.length) { showToast('warning', '\ud655\uc815\ud560 LOT\uc744 \uc120\ud0dd\ud558\uc138\uc694'); return; }
    var today = new Date().toISOString().slice(0, 10);
    var ov = document.createElement('div');
    ov.id = 'bulk-confirm-overlay';
    ov.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,0.6);z-index:10000;display:flex;align-items:center;justify-content:center';
    ov.innerHTML = '<div style="background:var(--surface,#1e293b);border:1px solid var(--border,#334155);'
      + 'border-radius:12px;padding:24px;min-width:360px">'
      + '<h3 style="margin:0 0 12px;font-size:15px;color:var(--text)">\u2705 \uc77c\uad04 \uc785\uace0 \ud655\uc815 (' + checked.length + '\uac74)</h3>'
      + '<div style="max-height:120px;overflow-y:auto;margin-bottom:12px;font-size:12px;color:var(--text-muted);font-family:monospace">'
      + checked.map(function(l) { return escapeHtml(l); }).join('<br>') + '</div>'
      + '<label style="font-size:13px;color:var(--text-muted);display:block;margin-bottom:6px">\uc77c\uad04 \ud655\uc815\uc77c</label>'
      + '<input id="bulk-confirm-date" type="date" value="' + today + '" max="' + today + '"'
      + ' style="width:100%;box-sizing:border-box;padding:8px;background:var(--bg,#0f172a);border:1px solid var(--border,#334155);'
      + 'border-radius:6px;color:var(--text);font-size:14px;margin-bottom:16px">'
      + '<div id="bulk-progress" style="display:none;margin-bottom:12px;font-size:13px;color:var(--accent,#3b82f6)"></div>'
      + '<div style="display:flex;gap:8px;justify-content:flex-end">'
      + '<button class="btn btn-ghost" onclick="document.getElementById(\'bulk-confirm-overlay\').remove()">\ucde8\uc18c</button>'
      + '<button id="bulk-confirm-btn" class="btn btn-primary" onclick="window._execBulkConfirm(' + JSON.stringify(checked) + ')">\uc77c\uad04 \ud655\uc815</button>'
      + '</div></div>';
    document.body.appendChild(ov);
  };

  window._execBulkConfirm = function(lots) {
    var dateEl = document.getElementById('bulk-confirm-date');
    var inboundDate = dateEl ? dateEl.value : '';
    if (!inboundDate || !/^\\d{4}-\\d{2}-\\d{2}$/.test(inboundDate)) {
      showToast('error', '\ub0a0\uc9dc\ub97c \uc62c\ubc14\ub974\uac8c \uc785\ub825\ud574 \uc8fc\uc138\uc694'); return;
    }
    var btn = document.getElementById('bulk-confirm-btn');
    if (btn) btn.disabled = true;
    var prog = document.getElementById('bulk-progress');
    if (prog) prog.style.display = 'block';
    var done = 0, errs = [];
    function next(i) {
      if (i >= lots.length) {
        var ov = document.getElementById('bulk-confirm-overlay');
        if (ov) ov.remove();
        if (errs.length) {
          showToast('warning', '\uc644\ub8cc ' + done + '\uac74 / \uc2e4\ud328 ' + errs.length + '\uac74: ' + errs.join(', '));
        } else {
          showToast('success', '\u2705 ' + done + '\uac74 \uc77c\uad04 \ud655\uc815 \uc644\ub8cc');
          setTimeout(function() { if (window.navigate) window.navigate('available'); }, 2000);
        }
        window.loadPendingPage(); return;
      }
      if (prog) prog.textContent = '\uc9c4\ud589 \uc911... ' + (i + 1) + '/' + lots.length + ' \u2014 ' + lots[i];
      apiPost('/api/inbound/confirm/' + encodeURIComponent(lots[i]), { inbound_date: inboundDate })
        .then(function() { done++; next(i + 1); })
        .catch(function() { errs.push(lots[i]); next(i + 1); });
    }
    next(0);
  };

'''

OLD3 = '  window.loadInventoryPage  = loadInventoryPage;\n})();'
NEW3 = NEW_FUNCS + '  window.loadInventoryPage  = loadInventoryPage;\n})();'
assert OLD3 in src, "Patch 3 대상을 찾지 못했습니다"
src = src.replace(OLD3, NEW3, 1)

f.write_text(src, encoding='utf-8')
print(f"패치 완료. 원본 {len(original)}자 → 수정 {len(src)}자")
print(f"추가 함수: pendingToggleAll, showPendingActionMenu, showPendingConfirmModal, executePendingConfirm, bulkConfirmPending, _execBulkConfirm")
