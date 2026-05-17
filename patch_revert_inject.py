# -*- coding: utf-8 -*-
"""
patch_revert_inject.py
main_webview.py on_loaded() 안에 두 번째 evaluate_js() 삽입.
캐시 완전 우회 — revertToPending + showInvActionMenu 패치를 런타임 주입.
"""
from pathlib import Path

f = Path('main_webview.py')
src = f.read_text(encoding='utf-8')

if '__SQM_REVERT_PATCHED__' in src:
    print("이미 적용됨 — 스킵")
else:
    # 기존 evaluate_js 블록 끝 마커
    MARKER = "                    console.log(\"[SQM] Error bridge installed\");\n                }})();\n            ''')"

    assert MARKER in src, "마커를 찾지 못함"

    # 두 번째 evaluate_js — f-string 아님(중괄호 그대로)
    INJECT = r"""

            # ── revertToPending 런타임 패치 (캐시 우회) ──────────────────
            window.evaluate_js("""
    INJECT += "'''"
    INJECT += r"""
                (function patchRevert() {
                    if (window.__SQM_REVERT_PATCHED__) return;
                    window.__SQM_REVERT_PATCHED__ = true;

                    /* ── revertToPending 함수 ── */
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
                        desc.style.cssText = 'margin:0 0 16px;font-size:13px;color:var(--text-muted)';
                        var strong = document.createElement('strong');
                        strong.style.cssText = 'color:var(--text);font-family:monospace';
                        strong.textContent = lot;
                        desc.appendChild(document.createTextNode('\uc785\uace0 \ucde8\uc18c: '));
                        desc.appendChild(strong);
                        desc.appendChild(document.createTextNode(' \u2192 PENDING \ubcf5\uad6c (inbound_date \ucd08\uae30\ud654)'));
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
                            window.apiPost('/api/inbound/revert/' + encodeURIComponent(l), {})
                                .then(function() {
                                    window.showToast('success', '\u21a9\ufe0f ' + l + ' \u2192 PENDING \ubcf5\uad6c \uc644\ub8cc');
                                    if (window.loadAvailablePage) window.loadAvailablePage();
                                })
                                .catch(function(e) { window.showToast('error', '\uc2e4\ud328: ' + (e.message || e)); });
                        };
                        btnRow.appendChild(cancelBtn);
                        btnRow.appendChild(confirmBtn);
                        box.appendChild(h3);
                        box.appendChild(desc);
                        box.appendChild(btnRow);
                        ov.appendChild(box);
                        document.body.appendChild(ov);
                        setTimeout(function() { cancelBtn.focus(); }, 50);
                    };

                    /* ── showInvActionMenu 패치: available 라우트에서만 항목 추가 ── */
                    window.showInvActionMenu = function(btn) {
                        var lot = btn.dataset.lot || '';
                        var route = window.getCurrentRoute ? window.getCurrentRoute() : '';
                        var items = [
                            { icon:'\ud83d\udccb', label:'LOT \uc0c1\uc138 \ubcf4\uae30', kbd:'Enter', fn:function(){ window.showLotDetail(lot); } },
                            { icon:'\ud83d\udcc4', label:'LOT \ubc88\ud638 \ubcf5\uc0ac', kbd:'Ctrl+C', fn:function(){ window.invCopyLot(lot); } },
                            { icon:'\ud83d\udcd1', label:'\ud589 \uc804\uccb4 \ubcf5\uc0ac', kbd:'Ctrl+Shift+C', fn:function(){ window.invCopyLot(lot); } },
                            '-',
                            { icon:'\ud83d\ude80', label:'\uc989\uc2dc \ucd9c\uace0 \uc9c4\uc785', kbd:'O', color:'#42a5f5', fn:function(){ window.invQuickOutbound(lot); } },
                            { icon:'\ud83d\udd04', label:'\ubc18\ud488 \uc9c4\uc785', kbd:'R', color:'#ef5350', fn:function(){ window.invQuickReturn(lot); } },
                            { icon:'\ud83d\udcca', label:'LOT \uc774\ub825 \ubcf4\uae30', kbd:'H', color:'#66bb6a', fn:function(){ window.invShowLotHistory(lot); } }
                        ];
                        if (route === 'available') {
                            items.push('-');
                            items.push({ icon:'\u21a9\ufe0f', label:'PENDING\uc73c\ub85c \ub418\ub3cc\ub9ac\uae30', color:'#f59e0b', fn:function(){ window.revertToPending(lot); } });
                        }
                        window._openContextMenu(btn, items);
                    };

                    console.log('[SQM] revertToPending patch OK');
                })();
"""
    INJECT += "            ''')"

    src = src.replace(MARKER, MARKER + INJECT, 1)
    f.write_text(src, encoding='utf-8')
    print("패치 완료")
