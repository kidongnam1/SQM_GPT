# -*- coding: utf-8 -*-
"""patch_revert_frontend.py — showInvActionMenu에 PENDING 되돌리기 메뉴 추가 + revertToPending 함수 삽입"""
from pathlib import Path

f = Path('frontend/js/sqm-inventory.js')
lines = f.read_text(encoding='utf-8').splitlines(keepends=True)

if any('revertToPending' in l for l in lines):
    print("이미 적용됨 — 스킵")
else:
    # ── 1. showInvActionMenu의 마지막 항목 줄 찾기 (invShowLotHistory 포함) ──
    menu_end_idx = None
    for i, line in enumerate(lines):
        if 'window.invShowLotHistory(lot)' in line and '_openContextMenu' not in line:
            menu_end_idx = i  # 이 줄 다음에 삽입
            break
    assert menu_end_idx is not None, "invShowLotHistory menu item not found"

    # 삽입할 두 줄
    SEP_LINE   = "      '-',\n"
    REVERT_LINE = "      { icon:'\u21a9\ufe0f', label:'PENDING\uc73c\ub85c \ub418\ub3cc\ub9ac\uae30', color:'#f59e0b', fn:function(){ window.revertToPending(lot); } },\n"

    lines.insert(menu_end_idx + 1, REVERT_LINE)
    lines.insert(menu_end_idx + 1, SEP_LINE)

    # ── 2. revertToPending 함수 삽입 (invCopyLot 바로 앞) ──────────
    copy_lot_idx = None
    for i, line in enumerate(lines):
        if '  window.invCopyLot = function(lot) {' in line:
            copy_lot_idx = i
            break
    assert copy_lot_idx is not None, "invCopyLot not found"

    NEW_FUNC_LINES = """\
  window.revertToPending = function(lot) {
    if (!lot) return;
    var ov = document.createElement('div');
    ov.id = 'revert-pending-overlay';
    ov.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,0.6);z-index:10000;display:flex;align-items:center;justify-content:center';
    var box = document.createElement('div');
    box.style.cssText = 'background:var(--surface,#1e293b);border:1px solid var(--border,#334155);border-radius:12px;padding:24px;min-width:320px;max-width:400px';
    var h3 = document.createElement('h3');
    h3.style.cssText = 'margin:0 0 12px;font-size:15px;color:var(--text)';
    h3.textContent = '\u21a9\ufe0f PENDING\uc73c\ub85c \ub418\ub3cc\ub9ac\uae30';
    var desc = document.createElement('p');
    desc.style.cssText = 'margin:0 0 16px;font-size:13px;color:var(--text-muted);white-space:pre-line';
    var strong = document.createElement('strong');
    strong.style.cssText = 'color:var(--text);font-family:monospace';
    strong.textContent = lot;
    desc.appendChild(document.createTextNode('\uc785\uace0 \ucde8\uc18c: '));
    desc.appendChild(strong);
    desc.appendChild(document.createTextNode('\n\ub85c PENDING\uc73c\ub85c \ub418\ub3cc\ub9bd\ub2c8\ub2e4.\ninbound_date \ucd08\uae30\ud654 / RESERVED\u00b7PICKED\u00b7SOLD \ud1a4\ubc31 \uc5c6\uc5b4\uc57c \ud569\ub2c8\ub2e4.'));
    var btnRow = document.createElement('div');
    btnRow.style.cssText = 'display:flex;gap:8px;justify-content:flex-end';
    var cancelBtn = document.createElement('button');
    cancelBtn.className = 'btn btn-ghost';
    cancelBtn.textContent = '\ucde8\uc18c';
    cancelBtn.onclick = function() { ov.remove(); };
    var confirmBtn = document.createElement('button');
    confirmBtn.className = 'btn btn-primary';
    confirmBtn.style.background = '#f59e0b';
    confirmBtn.textContent = '\ud655\uc778 \u2014 PENDING \ubcf5\uad6c';
    confirmBtn.dataset.lot = lot;
    confirmBtn.onclick = function() {
      var l = this.dataset.lot;
      ov.remove();
      apiPost('/api/inbound/revert/' + encodeURIComponent(l), {})
        .then(function() {
          showToast('success', '\u21a9\ufe0f ' + l + ' \u2192 PENDING \ubcf5\uad6c \uc644\ub8cc');
          if (window.loadAvailablePage) window.loadAvailablePage();
        })
        .catch(function(e) { showToast('error', '\uc2e4\ud328: ' + (e.message || e)); });
    };
    btnRow.appendChild(cancelBtn);
    btnRow.appendChild(confirmBtn);
    box.appendChild(h3);
    box.appendChild(desc);
    box.appendChild(btnRow);
    ov.appendChild(box);
    document.body.appendChild(ov);
  };

""".splitlines(keepends=True)

    for j, func_line in enumerate(NEW_FUNC_LINES):
        lines.insert(copy_lot_idx + j, func_line)

    f.write_text(''.join(lines), encoding='utf-8')
    print("frontend 패치 완료")
