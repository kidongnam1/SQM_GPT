# -*- coding: utf-8 -*-
"""
patch_all_footers.py
====================
Add sticky footer totals bar to all 9 remaining tables.

Files patched:
  pages/outbound.js    - scheduled/history table  (IIFE -> patch)
  pages/picked.js      - picked table             (ES module -> patch)
  pages/return.js      - return table             (ES module -> patch)
  pages/allocation.js  - allocation table         (IIFE -> patch)
  pages/dashboard.js   - products + lots tables   (ES module -> patch)
  pages/tonbag.js      - tonbag + move-history    (IIFE -> patch)
  pages/log.js         - log table                (ES module -> patch)
  pages/scan.js        - scan-history table       (IIFE -> patch)
"""

import shutil, pathlib, datetime, sys, re

JS_DIR = pathlib.Path(__file__).parent.parent / 'frontend' / 'js' / 'pages'
STAMP  = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
ERRORS = []

# ── common footer style strings (injected as JS literals) ─────────────────
# Badge span style
FS = (
    'display:inline-block;padding:2px 14px;margin-right:8px;'
    'background:rgba(79,195,247,0.13);border-radius:6px;'
    'font-size:12px;color:var(--accent,#4fc3f7);font-weight:700;'
)
# Footer wrapper style
FW = (
    'padding:5px 12px;background:var(--bg-hover);'
    'border-top:1px solid var(--panel-border);font-size:12px;flex-shrink:0;'
)
# Hint text style
FH = 'font-size:11px;color:var(--text-muted);margin-left:4px;'

def backup(path):
    bak = path.with_suffix('.js.bak_allfoot_' + STAMP)
    shutil.copy2(path, bak)
    print('[bak] ' + bak.name)

def save(path, txt, orig):
    if txt == orig:
        print('[WARN] no change: ' + path.name)
        return
    path.write_text(txt, encoding='utf-8')
    print('[saved] ' + path.name + ' (' + str(len(txt.splitlines())) + ' lines)')

def check(txt, must_have, label):
    for s in must_have:
        if s not in txt:
            ERRORS.append(label + ': missing [' + s + ']')

# ══════════════════════════════════════════════════════════════════════════════
# 1. pages/outbound.js  (IIFE, renderTable generic)
#    - Add _renderOutboundFooter helper
#    - Call it at end of renderTable
# ══════════════════════════════════════════════════════════════════════════════
def patch_outbound():
    p = JS_DIR / 'outbound.js'
    backup(p)
    txt = orig = p.read_text(encoding='utf-8')

    # Helper function to insert before the final return statement
    HELPER = (
        "\n"
        "  function _renderOutboundFooter(tbodyId, rows) {\n"
        "    var footId = tbodyId.replace(/-tbody$/, '-footer');\n"
        "    var foot = document.getElementById(footId);\n"
        "    if (!foot) {\n"
        "      var tb = document.getElementById(tbodyId);\n"
        "      if (!tb) return;\n"
        "      var tbl = tb.closest ? tb.closest('table') : tb.parentElement;\n"
        "      if (!tbl || !tbl.parentNode) return;\n"
        "      foot = document.createElement('div');\n"
        "      foot.id = footId;\n"
        "      foot.style.cssText = '" + FW + "';\n"
        "      tbl.parentNode.insertBefore(foot, tbl.nextSibling);\n"
        "    }\n"
        "    var s = '" + FS + "';\n"
        "    var total = 0;\n"
        "    rows.forEach(function(r) { total += Number(r.balance || r.net || r.balance_kg || 0); });\n"
        "    foot.innerHTML =\n"
        "        '<span style=\"' + s + '\">📋 ' + rows.length.toLocaleString('ko-KR') + ' 건</span>'\n"
        "      + (total > 0 ? '<span style=\"' + s + '\">⚖ ' + total.toLocaleString('ko-KR', {maximumFractionDigits:3}) + ' MT</span>' : '');\n"
        "  }\n"
        "\n"
    )
    ANCHOR_BEFORE = "  return { loadScheduled, loadHistory, renderTable, confirmOutbound, cancelOutbound };"
    if ANCHOR_BEFORE not in txt:
        ERRORS.append('outbound.js: return anchor not found'); return
    txt = txt.replace(ANCHOR_BEFORE, HELPER + ANCHOR_BEFORE, 1)

    # Call _renderOutboundFooter at end of renderTable (after tbody.innerHTML = ...)
    OLD_RT_END = (
        "    ).join('') : `<tr><td colspan=\"${columns.length}\" "
        "style=\"text-align:center;padding:40px;color:var(--text-muted)\">데이터 없음</td></tr>`;\n"
        "  }"
    )
    NEW_RT_END = (
        "    ).join('') : `<tr><td colspan=\"${columns.length}\" "
        "style=\"text-align:center;padding:40px;color:var(--text-muted)\">데이터 없음</td></tr>`;\n"
        "    _renderOutboundFooter(tbodyId, rows);\n"
        "  }"
    )
    if OLD_RT_END not in txt:
        # fallback: find closing brace of renderTable
        m = re.search(r"(    \.join\(''\) : `<tr><td colspan.*?없음</td></tr>`;\n  })", txt, re.DOTALL)
        if m:
            old = m.group(0)
            new = old.rstrip('}').rstrip() + '\n    _renderOutboundFooter(tbodyId, rows);\n  }'
            txt = txt.replace(old, new, 1)
            print('[outbound] renderTable footer call added (regex fallback)')
        else:
            ERRORS.append('outbound.js: renderTable end anchor not found'); return
    else:
        txt = txt.replace(OLD_RT_END, NEW_RT_END, 1)

    check(txt, ['_renderOutboundFooter'], 'outbound.js')
    save(p, txt, orig)

# ══════════════════════════════════════════════════════════════════════════════
# 2. pages/picked.js  (ES module)
#    - Add <div id="picked-footer"> after </table> in HTML template
#    - Update footer after tbody.innerHTML = ...
# ══════════════════════════════════════════════════════════════════════════════
def patch_picked():
    p = JS_DIR / 'picked.js'
    backup(p)
    txt = orig = p.read_text(encoding='utf-8')

    # Add footer div to HTML template
    OLD_TMPL = '      <div class="empty" id="picked-empty" style="display:none">표시할 데이터가 없습니다</div>'
    NEW_TMPL = (
        '      <div id="picked-footer" style="' + FW + '"></div>\n'
        + OLD_TMPL
    )
    if OLD_TMPL not in txt:
        ERRORS.append('picked.js: HTML template anchor not found'); return
    txt = txt.replace(OLD_TMPL, NEW_TMPL, 1)

    # Update footer after tbody.innerHTML assignment
    OLD_SHOW = "    table.style.display = '';\n  } catch"
    NEW_SHOW = (
        "    table.style.display = '';\n"
        "    var _pfoot = document.getElementById('picked-footer');\n"
        "    if (_pfoot) {\n"
        "      var _pqty = rows.reduce(function(s,r){return s+Number(r.qty||r.bags||0);},0);\n"
        "      var _ps = '" + FS + "';\n"
        "      _pfoot.innerHTML = '<span style=\"'+_ps+'\">🚛 PICKED '+rows.length.toLocaleString('ko-KR')+' 건</span>'\n"
        "        + (_pqty > 0 ? '<span style=\"'+_ps+'\">📦 수량 '+_pqty.toLocaleString('ko-KR')+'</span>' : '');\n"
        "    }\n"
        "  } catch"
    )
    if OLD_SHOW not in txt:
        ERRORS.append('picked.js: table.style.display anchor not found'); return
    txt = txt.replace(OLD_SHOW, NEW_SHOW, 1)

    check(txt, ['picked-footer'], 'picked.js')
    save(p, txt, orig)

# ══════════════════════════════════════════════════════════════════════════════
# 3. pages/return.js  (ES module)
# ══════════════════════════════════════════════════════════════════════════════
def patch_return():
    p = JS_DIR / 'return.js'
    backup(p)
    txt = orig = p.read_text(encoding='utf-8')

    # Add footer div to HTML template
    OLD_TMPL = '      <div class="empty" id="return-empty" style="display:none">표시할 데이터가 없습니다</div>'
    NEW_TMPL = (
        '      <div id="return-footer" style="' + FW + '"></div>\n'
        + OLD_TMPL
    )
    if OLD_TMPL not in txt:
        ERRORS.append('return.js: HTML template anchor not found'); return
    txt = txt.replace(OLD_TMPL, NEW_TMPL, 1)

    # Update footer after table shown
    OLD_SHOW = "    table.style.display = '';\n    empty.style.display = 'none';\n  } catch"
    NEW_SHOW = (
        "    table.style.display = '';\n"
        "    empty.style.display = 'none';\n"
        "    var _rfoot = document.getElementById('return-footer');\n"
        "    if (_rfoot) {\n"
        "      var _rbags = rows.reduce(function(s,r){return s+Number(r.bags||0);},0);\n"
        "      var _rs = '" + FS + "';\n"
        "      _rfoot.innerHTML = '<span style=\"'+_rs+'\">🔄 반품 '+rows.length.toLocaleString('ko-KR')+' 건</span>'\n"
        "        + (_rbags > 0 ? '<span style=\"'+_rs+'\">🎒 톤백 '+_rbags.toLocaleString('ko-KR')+'</span>' : '');\n"
        "    }\n"
        "  } catch"
    )
    if OLD_SHOW not in txt:
        ERRORS.append('return.js: table show anchor not found'); return
    txt = txt.replace(OLD_SHOW, NEW_SHOW, 1)

    check(txt, ['return-footer'], 'return.js')
    save(p, txt, orig)

# ══════════════════════════════════════════════════════════════════════════════
# 4. pages/allocation.js  (IIFE)
#    - Add _renderAllocFooter() inside IIFE
#    - Call at end of render()
# ══════════════════════════════════════════════════════════════════════════════
def patch_allocation():
    p = JS_DIR / 'allocation.js'
    backup(p)
    txt = orig = p.read_text(encoding='utf-8')

    HELPER = (
        "\n"
        "  function _renderAllocFooter() {\n"
        "    var foot = document.getElementById('allocation-footer');\n"
        "    if (!foot) {\n"
        "      var tb = document.getElementById('allocation-tbody');\n"
        "      if (!tb) return;\n"
        "      var tbl = tb.closest ? tb.closest('table') : tb.parentElement;\n"
        "      if (!tbl || !tbl.parentNode) return;\n"
        "      foot = document.createElement('div');\n"
        "      foot.id = 'allocation-footer';\n"
        "      foot.style.cssText = '" + FW + "';\n"
        "      tbl.parentNode.insertBefore(foot, tbl.nextSibling);\n"
        "    }\n"
        "    var s = '" + FS + "';\n"
        "    var totBal  = data.reduce(function(a,r){return a+Number(r.balance||0);}, 0);\n"
        "    var totBags = data.reduce(function(a,r){return a+Number(r.bags||0);}, 0);\n"
        "    foot.innerHTML =\n"
        "        '<span style=\"' + s + '\">📋 배정 ' + data.length.toLocaleString('ko-KR') + ' LOT</span>'\n"
        "      + '<span style=\"' + s + '\">⚖ ' + totBal.toLocaleString('ko-KR', {maximumFractionDigits:3}) + ' MT</span>'\n"
        "      + (totBags > 0 ? '<span style=\"' + s + '\">톤백 ' + totBags.toLocaleString('ko-KR') + ' 개</span>' : '');\n"
        "  }\n"
        "\n"
    )
    ANCHOR = "  return { load, render, toggle, cancel, cancelBulk };"
    if ANCHOR not in txt:
        ERRORS.append('allocation.js: return anchor not found'); return
    txt = txt.replace(ANCHOR, HELPER + ANCHOR, 1)

    # Call at end of render()
    OLD_RENDER_END = "  }\n\n  function toggle"
    NEW_RENDER_END = "    _renderAllocFooter();\n  }\n\n  function toggle"
    if OLD_RENDER_END not in txt:
        ERRORS.append('allocation.js: render end anchor not found'); return
    txt = txt.replace(OLD_RENDER_END, NEW_RENDER_END, 1)

    check(txt, ['_renderAllocFooter', 'allocation-footer'], 'allocation.js')
    save(p, txt, orig)

# ══════════════════════════════════════════════════════════════════════════════
# 5. pages/dashboard.js  (ES module)
#    - dash-products already has total-row inside tbody → add sticky footer div
#    - dash-lots: add count footer
# ══════════════════════════════════════════════════════════════════════════════
def patch_dashboard():
    p = JS_DIR / 'dashboard.js'
    backup(p)
    txt = orig = p.read_text(encoding='utf-8')

    # Add footer divs after each table in HTML template
    OLD_PROD = (
        "          <tbody id=\"dash-products\"></tbody>\n"
        "        </table>\n"
        "      </div>"
    )
    NEW_PROD = (
        "          <tbody id=\"dash-products\"></tbody>\n"
        "        </table>\n"
        "        <div id=\"dash-products-footer\" style=\"" + FW + "\"></div>\n"
        "      </div>"
    )
    if OLD_PROD not in txt:
        ERRORS.append('dashboard.js: dash-products table anchor not found'); return
    txt = txt.replace(OLD_PROD, NEW_PROD, 1)

    OLD_LOTS = (
        "          <tbody id=\"dash-lots\"></tbody>\n"
        "        </table>\n"
        "      </div>"
    )
    NEW_LOTS = (
        "          <tbody id=\"dash-lots\"></tbody>\n"
        "        </table>\n"
        "        <div id=\"dash-lots-footer\" style=\"" + FW + "\"></div>\n"
        "      </div>"
    )
    if OLD_LOTS not in txt:
        ERRORS.append('dashboard.js: dash-lots table anchor not found'); return
    txt = txt.replace(OLD_LOTS, NEW_LOTS, 1)

    # Update products footer at end of renderProducts
    OLD_REND_P_END = "}\n\nfunction renderLots"
    NEW_REND_P_END = (
        "  var _dpfoot = document.getElementById('dash-products-footer');\n"
        "  if (_dpfoot) {\n"
        "    var _dps = '" + FS + "';\n"
        "    var _totSell = rows.reduce(function(a,r){return a+(r.sellable||0);},0);\n"
        "    var _totAll  = rows.reduce(function(a,r){return a+(r.total||0);},0);\n"
        "    _dpfoot.innerHTML = '<span style=\"'+_dps+'\">타입 '+rows.length+'조</span>'\n"
        "      + '<span style=\"'+_dps+'\">판매가능 '+num(_totSell)+' MT</span>'\n"
        "      + '<span style=\"'+_dps+'\">합계 '+num(_totAll)+' MT</span>';\n"
        "  }\n"
        "}\n\nfunction renderLots"
    )
    if OLD_REND_P_END not in txt:
        ERRORS.append('dashboard.js: renderProducts end anchor not found'); return
    txt = txt.replace(OLD_REND_P_END, NEW_REND_P_END, 1)

    # Update lots footer at end of renderLots
    OLD_REND_L_END = "  ).join('');\n}\n\nexport function unmount"
    NEW_REND_L_END = (
        "  ).join('');\n"
        "  var _dlfoot = document.getElementById('dash-lots-footer');\n"
        "  if (_dlfoot) {\n"
        "    var _dls = '" + FS + "';\n"
        "    _dlfoot.innerHTML = '<span style=\"'+_dls+'\">LOT '+rows.length+'건</span>';\n"
        "  }\n"
        "}\n\nexport function unmount"
    )
    if OLD_REND_L_END not in txt:
        ERRORS.append('dashboard.js: renderLots end anchor not found'); return
    txt = txt.replace(OLD_REND_L_END, NEW_REND_L_END, 1)

    check(txt, ['dash-products-footer', 'dash-lots-footer'], 'dashboard.js')
    save(p, txt, orig)

# ══════════════════════════════════════════════════════════════════════════════
# 6. pages/tonbag.js  (IIFE: TonbagPage + MovePage)
#    - TonbagPage.render(): count + weight sum
#    - MovePage.renderHistory(): count only
# ══════════════════════════════════════════════════════════════════════════════
def patch_tonbag():
    p = JS_DIR / 'tonbag.js'
    backup(p)
    txt = orig = p.read_text(encoding='utf-8')

    # --- TonbagPage footer helper (before TonbagPage return) ---
    TB_HELPER = (
        "\n"
        "  function _renderTonbagPageFooter(rows) {\n"
        "    var foot = document.getElementById('tonbag-page-footer');\n"
        "    if (!foot) {\n"
        "      var tb = document.getElementById('tonbag-tbody');\n"
        "      if (!tb) return;\n"
        "      var tbl = tb.closest ? tb.closest('table') : tb.parentElement;\n"
        "      if (!tbl || !tbl.parentNode) return;\n"
        "      foot = document.createElement('div');\n"
        "      foot.id = 'tonbag-page-footer';\n"
        "      foot.style.cssText = '" + FW + "';\n"
        "      tbl.parentNode.insertBefore(foot, tbl.nextSibling);\n"
        "    }\n"
        "    var s = '" + FS + "';\n"
        "    var totW = rows.reduce(function(a,r){return a+Number(r.weight||0);},0);\n"
        "    foot.innerHTML =\n"
        "        '<span style=\"' + s + '\">톤백 ' + rows.length.toLocaleString('ko-KR') + ' 건</span>'\n"
        "      + '<span style=\"' + s + '\">⚖ 수량 ' + totW.toLocaleString('ko-KR', {maximumFractionDigits:2}) + ' kg</span>';\n"
        "  }\n"
        "\n"
    )
    TB_ANCHOR = "  return { load, render, setFilter };"
    if TB_ANCHOR not in txt:
        ERRORS.append('tonbag.js: TonbagPage return anchor not found'); return
    txt = txt.replace(TB_ANCHOR, TB_HELPER + TB_ANCHOR, 1)

    # Call after filtered.length (render() body) - find the closing of render function
    OLD_TB_RENDER = "  function setFilter(key, value) { filters[key] = value; render(); }"
    NEW_TB_RENDER = (
        "  function _doRenderFooter() {\n"
        "    var filtered = data.filter(function(r) {\n"
        "      return (!filters.product || r.product === filters.product) &&\n"
        "             (!filters.container || (r.container && r.container.indexOf(filters.container) >= 0));\n"
        "    });\n"
        "    _renderTonbagPageFooter(filtered);\n"
        "  }\n"
        "  function setFilter(key, value) { filters[key] = value; render(); _doRenderFooter(); }"
    )
    if OLD_TB_RENDER not in txt:
        ERRORS.append('tonbag.js: setFilter anchor not found'); return
    txt = txt.replace(OLD_TB_RENDER, NEW_TB_RENDER, 1)

    # Also call after tbody.innerHTML in render()
    OLD_TB_BODY = (
        "    tbody.innerHTML = filtered.length ? filtered.map(r => `\n"
        "      <tr>\n"
        "        <td class=\"mono-cell\">${r.sub_lt || r.tonbag_id || '-'}</td>\n"
        "        <td class=\"mono-cell\" style=\"color:var(--accent)\">${r.lot_no || '-'}</td>\n"
        "        <td><span class=\"tag\">${r.product || '-'}</span></td>\n"
        "        <td>${window.STATUS_BADGE?.[r.status] || r.status || '-'}</td>\n"
        "        <td class=\"mono-cell\">${(r.weight || 0).toLocaleString()}</td>\n"
        "        <td class=\"mono-cell\">${r.location || '-'}</td>\n"
        "        <td class=\"mono-cell\">${r.container || '-'}</td>\n"
        "        <td><button class=\"btn btn-ghost btn-xs\">상세</button></td>\n"
        "      </tr>\n"
        "    `).join('') : `<tr><td colspan=\"8\" style=\"text-align:center;padding:40px;color:var(--text-muted)\">데이터 없음</td></tr>`;\n"
        "  }"
    )
    NEW_TB_BODY = (
        "    tbody.innerHTML = filtered.length ? filtered.map(r => `\n"
        "      <tr>\n"
        "        <td class=\"mono-cell\">${r.sub_lt || r.tonbag_id || '-'}</td>\n"
        "        <td class=\"mono-cell\" style=\"color:var(--accent)\">${r.lot_no || '-'}</td>\n"
        "        <td><span class=\"tag\">${r.product || '-'}</span></td>\n"
        "        <td>${window.STATUS_BADGE?.[r.status] || r.status || '-'}</td>\n"
        "        <td class=\"mono-cell\">${(r.weight || 0).toLocaleString()}</td>\n"
        "        <td class=\"mono-cell\">${r.location || '-'}</td>\n"
        "        <td class=\"mono-cell\">${r.container || '-'}</td>\n"
        "        <td><button class=\"btn btn-ghost btn-xs\">상세</button></td>\n"
        "      </tr>\n"
        "    `).join('') : `<tr><td colspan=\"8\" style=\"text-align:center;padding:40px;color:var(--text-muted)\">데이터 없음</td></tr>`;\n"
        "    _renderTonbagPageFooter(filtered);\n"
        "  }"
    )
    if OLD_TB_BODY not in txt:
        ERRORS.append('tonbag.js: render tbody anchor not found'); return
    txt = txt.replace(OLD_TB_BODY, NEW_TB_BODY, 1)

    # --- MovePage footer helper (before MovePage return) ---
    MV_HELPER = (
        "\n"
        "  function _renderMoveFooter(rows) {\n"
        "    var foot = document.getElementById('move-history-footer');\n"
        "    if (!foot) {\n"
        "      var tb = document.getElementById('move-history-tbody');\n"
        "      if (!tb) return;\n"
        "      var tbl = tb.closest ? tb.closest('table') : tb.parentElement;\n"
        "      if (!tbl || !tbl.parentNode) return;\n"
        "      foot = document.createElement('div');\n"
        "      foot.id = 'move-history-footer';\n"
        "      foot.style.cssText = '" + FW + "';\n"
        "      tbl.parentNode.insertBefore(foot, tbl.nextSibling);\n"
        "    }\n"
        "    var s = '" + FS + "';\n"
        "    foot.innerHTML = '<span style=\"' + s + '\">이동 이력 ' + rows.length.toLocaleString('ko-KR') + ' 건</span>';\n"
        "  }\n"
        "\n"
    )
    MV_ANCHOR = "  return { executeMove, loadHistory, renderHistory };"
    if MV_ANCHOR not in txt:
        ERRORS.append('tonbag.js: MovePage return anchor not found'); return
    txt = txt.replace(MV_ANCHOR, MV_HELPER + MV_ANCHOR, 1)

    # Call at end of renderHistory
    OLD_MV_END = "  }\n\n  return { executeMove, loadHistory, renderHistory };"
    NEW_MV_END = (
        "    _renderMoveFooter(moveHistory);\n"
        "  }\n\n"
        "  return { executeMove, loadHistory, renderHistory };"
    )
    if OLD_MV_END not in txt:
        ERRORS.append('tonbag.js: renderHistory end anchor not found'); return
    txt = txt.replace(OLD_MV_END, NEW_MV_END, 1)

    check(txt, ['tonbag-page-footer', 'move-history-footer'], 'tonbag.js')
    save(p, txt, orig)

# ══════════════════════════════════════════════════════════════════════════════
# 7. pages/log.js  (ES module)
#    - Add footer div to HTML template
#    - Update with row count after load
# ══════════════════════════════════════════════════════════════════════════════
def patch_log():
    p = JS_DIR / 'log.js'
    backup(p)
    txt = orig = p.read_text(encoding='utf-8')

    OLD_TMPL = '      <div class="empty" id="log-empty" style="display:none">로그 없음</div>'
    NEW_TMPL = (
        '      <div id="log-footer" style="' + FW + '"></div>\n'
        + OLD_TMPL
    )
    if OLD_TMPL not in txt:
        ERRORS.append('log.js: HTML template anchor not found'); return
    txt = txt.replace(OLD_TMPL, NEW_TMPL, 1)

    OLD_LOG_SHOW = "    table.style.display = '';\n    empty.style.display = 'none';\n  } catch (e) {\n    empty.textContent = `로그"
    NEW_LOG_SHOW = (
        "    table.style.display = '';\n"
        "    empty.style.display = 'none';\n"
        "    var _lfoot = document.getElementById('log-footer');\n"
        "    if (_lfoot) {\n"
        "      var _ls = '" + FS + "';\n"
        "      _lfoot.innerHTML = '<span style=\"'+_ls+'\">📝 로그 '+rows.length.toLocaleString('ko-KR')+' 건</span>';\n"
        "    }\n"
        "  } catch (e) {\n    empty.textContent = `로그"
    )
    if OLD_LOG_SHOW not in txt:
        ERRORS.append('log.js: table show anchor not found'); return
    txt = txt.replace(OLD_LOG_SHOW, NEW_LOG_SHOW, 1)

    check(txt, ['log-footer'], 'log.js')
    save(p, txt, orig)

# ══════════════════════════════════════════════════════════════════════════════
# 8. pages/scan.js  (IIFE)
#    - Add _renderScanFooter helper inside IIFE
#    - Call at end of renderHistory
# ══════════════════════════════════════════════════════════════════════════════
def patch_scan():
    p = JS_DIR / 'scan.js'
    backup(p)
    txt = orig = p.read_text(encoding='utf-8')

    HELPER = (
        "\n"
        "  function _renderScanFooter(hist) {\n"
        "    var foot = document.getElementById('scan-history-footer');\n"
        "    if (!foot) {\n"
        "      var tb = document.getElementById('scan-history-tbody');\n"
        "      if (!tb) return;\n"
        "      var tbl = tb.closest ? tb.closest('table') : tb.parentElement;\n"
        "      if (!tbl || !tbl.parentNode) return;\n"
        "      foot = document.createElement('div');\n"
        "      foot.id = 'scan-history-footer';\n"
        "      foot.style.cssText = '" + FW + "';\n"
        "      tbl.parentNode.insertBefore(foot, tbl.nextSibling);\n"
        "    }\n"
        "    var s = '" + FS + "';\n"
        "    var shown = hist.slice(0, 20);\n"
        "    var ok  = shown.filter(function(h){return h.success;}).length;\n"
        "    var ng  = shown.length - ok;\n"
        "    var _sg = 'display:inline-block;padding:2px 10px;margin-right:6px;border-radius:6px;font-size:12px;font-weight:700;';\n"
        "    foot.innerHTML =\n"
        "        '<span style=\"' + s + '\">스캔 ' + shown.length + '건 / 전체 ' + hist.length + '건</span>'\n"
        "      + '<span style=\"' + _sg + 'background:rgba(34,197,94,0.2);color:#22c55e;\">✅ 성공 ' + ok + '</span>'\n"
        "      + (ng > 0 ? '<span style=\"' + _sg + 'background:rgba(244,67,54,0.2);color:#f44336;\">❌ 실패 ' + ng + '</span>' : '');\n"
        "  }\n"
        "\n"
    )
    ANCHOR = "  return { init, processBarcode, quickAction, renderHistory };"
    if ANCHOR not in txt:
        ERRORS.append('scan.js: return anchor not found'); return
    txt = txt.replace(ANCHOR, HELPER + ANCHOR, 1)

    # Call at end of renderHistory
    OLD_SCH_END = "  }\n\n  function quickAction"
    NEW_SCH_END = "    _renderScanFooter(history);\n  }\n\n  function quickAction"
    if OLD_SCH_END not in txt:
        ERRORS.append('scan.js: renderHistory end anchor not found'); return
    txt = txt.replace(OLD_SCH_END, NEW_SCH_END, 1)

    check(txt, ['_renderScanFooter', 'scan-history-footer'], 'scan.js')
    save(p, txt, orig)

# ══════════════════════════════════════════════════════════════════════════════
# RUN ALL
# ══════════════════════════════════════════════════════════════════════════════
print('=== patch_all_footers.py ===')
patch_outbound()
patch_picked()
patch_return()
patch_allocation()
patch_dashboard()
patch_tonbag()
patch_log()
patch_scan()

print()
if ERRORS:
    print('[ERRORS] ' + str(len(ERRORS)) + ' anchor(s) not found:')
    for e in ERRORS: print('  - ' + e)
    sys.exit(1)
else:
    print('ALL DONE - 9 tables patched successfully')
    print('Tables with sticky footer totals now: 15/15')
