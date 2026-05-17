# -*- coding: utf-8 -*-
"""patch_A_rewrite: line 678 이후 삽입 블록을 올바른 버전으로 교체"""
from pathlib import Path

f = Path('frontend/js/sqm-inventory.js')
lines = f.read_text(encoding='utf-8').splitlines()

# line 678(0-indexed: 677)부터 "window.loadInventoryPage  = loadInventoryPage;" 직전까지 교체
start_idx = None
end_idx = None
for i, line in enumerate(lines):
    if line.strip() == 'window.pendingToggleAll = function(cb) {' and start_idx is None:
        start_idx = i
    if '  window.loadInventoryPage  = loadInventoryPage;' in line:
        end_idx = i

assert start_idx is not None, "start not found"
assert end_idx is not None, "end not found"

# 새 함수 블록 — 따옴표 문제 없이 DOM 방식 + 올바른 이스케이프
NEW_FUNCS = r"""  window.pendingToggleAll = function(cb) {
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
    var item1 = document.createElement('div');
    item1.style.cssText = 'padding:8px 16px;cursor:pointer;font-size:13px;color:var(--text)';
    item1.dataset.lot = lotNo;
    item1.onmouseenter = function() { this.style.background = '#334155'; };
    item1.onmouseleave = function() { this.style.background = ''; };
    item1.onclick = function() {
      window.showPendingConfirmModal(this.dataset.lot);
      var m = document.getElementById('pending-ctx-menu'); if (m) m.remove();
    };
    item1.textContent = '\u2705 AVAILABLE \uc785\uace0 \ud655\uc815';
    var item2 = document.createElement('div');
    item2.style.cssText = 'padding:8px 16px;cursor:pointer;font-size:13px;color:var(--text-muted)';
    item2.dataset.lot = lotNo;
    item2.onmouseenter = function() { this.style.background = '#334155'; };
    item2.onmouseleave = function() { this.style.background = ''; };
    item2.onclick = function() {
      window.invShowLotHistory(this.dataset.lot);
      var m = document.getElementById('pending-ctx-menu'); if (m) m.remove();
    };
    item2.textContent = '\ud83d\udcca LOT \uc774\ub825 \ubcf4\uae30';
    menu.appendChild(item1);
    menu.appendChild(item2);
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
    var inner = document.createElement('div');
    inner.style.cssText = 'background:var(--surface,#1e293b);border:1px solid var(--border,#334155);border-radius:12px;padding:24px;min-width:320px;max-width:400px';
    var h3 = document.createElement('h3');
    h3.style.cssText = 'margin:0 0 16px;font-size:15px;color:var(--text)';
    h3.textContent = '\u2705 \uc785\uace0 \ud655\uc815';
    var lotInfo = document.createElement('div');
    lotInfo.style.cssText = 'margin-bottom:8px;font-size:13px;color:var(--text-muted)';
    var lotSpan = document.createElement('span');
    lotSpan.style.cssText = 'color:var(--text);font-family:monospace';
    lotSpan.textContent = lotNo;
    lotInfo.appendChild(document.createTextNode('LOT: '));
    lotInfo.appendChild(lotSpan);
    var label = document.createElement('label');
    label.style.cssText = 'font-size:13px;color:var(--text-muted);display:block;margin-bottom:6px';
    label.textContent = '\uc785\uace0 \ud655\uc815\uc77c (YYYY-MM-DD)';
    var input = document.createElement('input');
    input.id = 'pending-confirm-date';
    input.type = 'date';
    input.value = today;
    input.max = today;
    input.style.cssText = 'width:100%;box-sizing:border-box;padding:8px;background:var(--bg,#0f172a);border:1px solid var(--border,#334155);border-radius:6px;color:var(--text);font-size:14px;margin-bottom:16px';
    var btnRow = document.createElement('div');
    btnRow.style.cssText = 'display:flex;gap:8px;justify-content:flex-end';
    var cancelBtn = document.createElement('button');
    cancelBtn.className = 'btn btn-ghost';
    cancelBtn.textContent = '\ucde8\uc18c';
    cancelBtn.onclick = function() { ov.remove(); };
    var confirmBtn = document.createElement('button');
    confirmBtn.className = 'btn btn-primary';
    confirmBtn.textContent = '\ud655\uc815';
    confirmBtn.dataset.lot = lotNo;
    confirmBtn.onclick = function() { window.executePendingConfirm(this.dataset.lot); };
    btnRow.appendChild(cancelBtn);
    btnRow.appendChild(confirmBtn);
    inner.appendChild(h3);
    inner.appendChild(lotInfo);
    inner.appendChild(label);
    inner.appendChild(input);
    inner.appendChild(btnRow);
    ov.appendChild(inner);
    document.body.appendChild(ov);
    setTimeout(function() { input.focus(); }, 50);
  };

  window.executePendingConfirm = function(lotNo) {
    var dateEl = document.getElementById('pending-confirm-date');
    var inboundDate = dateEl ? dateEl.value : '';
    if (!inboundDate || !/^\d{4}-\d{2}-\d{2}$/.test(inboundDate)) {
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
    var inner = document.createElement('div');
    inner.style.cssText = 'background:var(--surface,#1e293b);border:1px solid var(--border,#334155);border-radius:12px;padding:24px;min-width:360px';
    var h3 = document.createElement('h3');
    h3.style.cssText = 'margin:0 0 12px;font-size:15px;color:var(--text)';
    h3.textContent = '\u2705 \uc77c\uad04 \uc785\uace0 \ud655\uc815 (' + checked.length + '\uac74)';
    var lotList = document.createElement('div');
    lotList.style.cssText = 'max-height:120px;overflow-y:auto;margin-bottom:12px;font-size:12px;color:var(--text-muted);font-family:monospace';
    lotList.textContent = checked.join(', ');
    var label = document.createElement('label');
    label.style.cssText = 'font-size:13px;color:var(--text-muted);display:block;margin-bottom:6px';
    label.textContent = '\uc77c\uad04 \ud655\uc815\uc77c';
    var input = document.createElement('input');
    input.id = 'bulk-confirm-date';
    input.type = 'date';
    input.value = today;
    input.max = today;
    input.style.cssText = 'width:100%;box-sizing:border-box;padding:8px;background:var(--bg,#0f172a);border:1px solid var(--border,#334155);border-radius:6px;color:var(--text);font-size:14px;margin-bottom:16px';
    var prog = document.createElement('div');
    prog.id = 'bulk-progress';
    prog.style.cssText = 'display:none;margin-bottom:12px;font-size:13px;color:var(--accent,#3b82f6)';
    var btnRow = document.createElement('div');
    btnRow.style.cssText = 'display:flex;gap:8px;justify-content:flex-end';
    var cancelBtn = document.createElement('button');
    cancelBtn.className = 'btn btn-ghost';
    cancelBtn.textContent = '\ucde8\uc18c';
    cancelBtn.onclick = function() { ov.remove(); };
    var execBtn = document.createElement('button');
    execBtn.id = 'bulk-confirm-btn';
    execBtn.className = 'btn btn-primary';
    execBtn.textContent = '\uc77c\uad04 \ud655\uc815';
    execBtn.dataset.lots = JSON.stringify(checked);
    execBtn.onclick = function() { window._execBulkConfirm(JSON.parse(this.dataset.lots)); };
    btnRow.appendChild(cancelBtn);
    btnRow.appendChild(execBtn);
    inner.appendChild(h3);
    inner.appendChild(lotList);
    inner.appendChild(label);
    inner.appendChild(input);
    inner.appendChild(prog);
    inner.appendChild(btnRow);
    ov.appendChild(inner);
    document.body.appendChild(ov);
  };

  window._execBulkConfirm = function(lots) {
    var dateEl = document.getElementById('bulk-confirm-date');
    var inboundDate = dateEl ? dateEl.value : '';
    if (!inboundDate || !/^\d{4}-\d{2}-\d{2}$/.test(inboundDate)) {
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

"""

# 기존 블록(start_idx ~ end_idx-1)을 새 블록으로 교체
new_lines = lines[:start_idx] + NEW_FUNCS.splitlines() + [''] + lines[end_idx:]
f.write_text('\n'.join(new_lines) + '\n', encoding='utf-8')
print(f"교체 완료: line {start_idx+1}~{end_idx} → 새 블록 {len(NEW_FUNCS.splitlines())}줄")
