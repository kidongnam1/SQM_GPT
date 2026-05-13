/* =======================================================================
   sqm-listview.js  (v8.6.8)
   재고 메뉴 — LOT / 톤백 리스트 화면 모달

   기존 동작:
     [LOT 리스트 Excel] 클릭 → 엑셀 파일 바로 다운로드
     [톤백리스트 Excel] 클릭 → 엑셀 파일 바로 다운로드

   변경 동작:
     클릭 → 화면 안에 테이블 표시 + 우측 상단 [📥 엑셀 다운로드] 버튼
     사용자가 데이터 확인 후 필요하면 엑셀로 내보내기

   API:
     GET /api/action/lot-list-json
     GET /api/action2/tonbag-list-json?lot_no=...
   ======================================================================= */
(function () {
  'use strict';
  if (window.__SQM_LISTVIEW_INSTALLED__) return;
  window.__SQM_LISTVIEW_INSTALLED__ = true;

  /* ── 의존성 폴백 (sqm-inline.js 에서 제공) ── */
  function _api()         { return (typeof API !== 'undefined') ? API : ''; }
  function _toast(t, msg) { if (window.showToast) window.showToast(t, msg); }
  function _esc(s) {
    if (window.escapeHtml) return window.escapeHtml(s);
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;')
      .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }
  function _dlUrl(url, label) {
    if (typeof window.sqmDownloadFileUrl === 'function') {
      window.sqmDownloadFileUrl(url, label);
    } else {
      window.open(url, '_blank');
    }
  }

  /* ── 컬럼 정의 ── */
  var LOT_COLS = [
    { k: 'sap_no',        h: 'SAP NO',     w: 110 },
    { k: 'bl_no',         h: 'BL NO',      w: 130 },
    { k: 'container_no',  h: 'Container',  w: 130 },
    { k: 'product',       h: '제품명',     w: 200 },
    { k: 'lot_no',        h: 'LOT NO',     w: 130, mono: true, bold: true },
    { k: 'lot_sqm',       h: 'LOT SQM',    w: 110 },
    { k: 'net_weight',    h: '순중량(kg)',  w: 100, align: 'right', num: true },
    { k: 'current_weight',h: '현재(kg)',    w: 100, align: 'right', num: true },
    { k: 'tonbag_count',  h: '톤백수',      w: 70,  align: 'right' },
    { k: 'status',        h: '상태',        w: 90,  align: 'center', badge: 'status' },
    { k: 'inbound_date',  h: '입고일',      w: 100, align: 'center' },
    { k: 'arrival_date',  h: '도착일',      w: 100, align: 'center' },
    { k: 'warehouse',     h: '창고',        w: 60,  align: 'center' },
    { k: 'vessel',        h: '선박',        w: 130 },
    { k: 'do_no',         h: 'D/O NO',     w: 120 },
    { k: 'remarks',       h: '비고',       w: 160 },
  ];

  var TONBAG_COLS = [
    { k: 'sap_no',       h: 'SAP NO',     w: 110 },
    { k: 'bl_no',        h: 'BL NO',      w: 130 },
    { k: 'container_no', h: 'Container',  w: 130 },
    { k: 'product',      h: '제품명',     w: 200 },
    { k: 'tonbag_uid',   h: '톤백 UID',    w: 160, mono: true },
    { k: 'sub_lt',       h: 'Sub LT',     w: 70,  align: 'right' },
    { k: 'tonbag_no',    h: '톤백 번호',   w: 90,  align: 'center' },
    { k: 'weight_kg',    h: '중량(kg)',    w: 90,  align: 'right', num: true },
    { k: 'status',       h: '상태',        w: 90,  align: 'center', badge: 'status' },
    { k: 'location',     h: '위치',        w: 130, mono: true },
    { k: 'inbound_date', h: '입고일',      w: 100, align: 'center' },
    { k: 'sold_to',      h: '출고대상',    w: 130 },
    { k: 'sale_ref',     h: 'Sale Ref',   w: 130 },
    { k: 'remarks',      h: '비고',       w: 160 },
    { k: 'warehouse',    h: '창고',        w: 60,  align: 'center' },
  ];

  /* ── 상태 배지 색상 ── */
  var STATUS_COLORS = {
    AVAILABLE: { bg: '#1b5e20', fg: '#a5d6a7' },
    RESERVED:  { bg: '#0d47a1', fg: '#90caf9' },
    PICKED:    { bg: '#f57f17', fg: '#fff9c4' },
    SOLD:      { bg: '#424242', fg: '#e0e0e0' },
    PENDING:   { bg: '#1565c0', fg: '#bbdefb' },
    RETURN:    { bg: '#b71c1c', fg: '#ffcdd2' },
    DEPLETED:  { bg: '#37474f', fg: '#cfd8dc' },
    SHIPPED:   { bg: '#212121', fg: '#9e9e9e' },
  };

  function _formatCell(val, col) {
    if (val == null || val === '') return '';
    if (col.num) {
      var n = Number(val);
      if (!isNaN(n)) return n.toLocaleString('ko-KR', { maximumFractionDigits: 2 });
    }
    if (col.badge === 'status') {
      var c = STATUS_COLORS[String(val).toUpperCase()] || { bg: '#37474f', fg: '#cfd8dc' };
      return '<span style="display:inline-block;padding:1px 8px;border-radius:10px;'
        + 'background:' + c.bg + ';color:' + c.fg + ';font-size:10px;font-weight:700;">'
        + _esc(val) + '</span>';
    }
    return _esc(val);
  }

  /* ── 공통 모달 ── */
  var _modalEl = null;
  function _ensureModal() {
    if (_modalEl && document.body.contains(_modalEl)) {
      _modalEl.style.display = 'flex';
      return _modalEl;
    }
    var d = document.createElement('div');
    d.id = 'sqm-listview-modal';
    d.style.cssText = ''
      + 'position:fixed;top:50px;left:50%;transform:translateX(-50%);'
      + 'width:min(1400px,96vw);height:84vh;background:var(--bg-card);'
      + 'border:2px solid var(--accent,#4fc3f7);border-radius:10px;'
      + 'box-shadow:0 8px 40px rgba(0,0,0,.6);z-index:10040;'
      + 'display:flex;flex-direction:column;overflow:hidden;';
    d.innerHTML = ''
      + '<div id="sqm-listview-hdr" style="cursor:move;background:var(--bg-hover);'
      +     'border-radius:10px 10px 0 0;padding:8px 14px;display:flex;'
      +     'align-items:center;gap:10px;flex-shrink:0;border-bottom:1px solid var(--panel-border);">'
      + '  <span id="sqm-listview-title" style="font-size:15px;font-weight:700;color:var(--accent);">📋 리스트</span>'
      + '  <span id="sqm-listview-count" style="font-size:11px;color:var(--text-muted);"></span>'
      + '  <input id="sqm-listview-filter" type="text" placeholder="🔎 빠른 검색 (LOT/제품/SAP/BL...)" '
      +       'style="margin-left:auto;padding:4px 10px;background:var(--bg);color:var(--fg);'
      +             'border:1px solid var(--border);border-radius:6px;font-size:12px;width:240px;">'
      + '  <button id="sqm-listview-excel" class="btn btn-primary" '
      +       'style="padding:4px 12px;font-size:12px;">📥 엑셀 다운로드</button>'
      + '  <button id="sqm-listview-refresh" class="btn" style="padding:4px 10px;font-size:12px;">↻ 새로고침</button>'
      + '  <button id="sqm-listview-close" '
      +       'style="background:none;border:none;font-size:18px;cursor:pointer;'
      +             'color:var(--text-muted);padding:0 4px;">×</button>'
      + '</div>'
      + '<div id="sqm-listview-body" style="flex:1 1 auto;overflow:auto;padding:10px 14px;">'
      + '  <div style="text-align:center;color:var(--text-muted);padding:40px;">⏳ 로딩 중...</div>'
      + '</div>'
      + '<div id="sqm-listview-foot" style="padding:6px 14px;border-top:1px solid var(--panel-border);'
      +     'background:var(--bg-hover);font-size:11px;color:var(--text-muted);flex-shrink:0;">'
      + '</div>';
    document.body.appendChild(d);
    _modalEl = d;
    /* 닫기 */
    document.getElementById('sqm-listview-close').onclick = function() { d.style.display = 'none'; };
    /* 드래그 (있으면 사용) */
    if (typeof window._makeDraggableResizable === 'function') {
      window._makeDraggableResizable(d, document.getElementById('sqm-listview-hdr'));
    }
    return d;
  }

  /* ── 렌더 ── */
  function _renderTable(cols, rows, container) {
    if (!rows || rows.length === 0) {
      container.innerHTML = '<div style="text-align:center;color:var(--text-muted);padding:40px;">📭 데이터가 없습니다.</div>';
      return;
    }
    var thead = cols.map(function(c) {
      var align = c.align ? 'text-align:' + c.align + ';' : '';
      return '<th style="padding:6px 8px;background:var(--bg-hover);color:var(--accent);'
        + 'font-size:11px;font-weight:700;border-bottom:2px solid var(--accent);'
        + 'position:sticky;top:0;z-index:1;white-space:nowrap;' + align
        + (c.w ? 'min-width:' + c.w + 'px;' : '') + '">' + _esc(c.h) + '</th>';
    }).join('');
    var tbody = rows.map(function(r, ri) {
      var tds = cols.map(function(c) {
        var v = _formatCell(r[c.k], c);
        var style = 'padding:4px 8px;border-bottom:1px solid var(--panel-border);'
          + 'font-size:12px;white-space:nowrap;';
        if (c.align)  style += 'text-align:' + c.align + ';';
        if (c.mono)   style += 'font-family:Consolas,monospace;';
        if (c.bold)   style += 'font-weight:700;';
        return '<td style="' + style + '">' + v + '</td>';
      }).join('');
      var rowBg = ri % 2 === 0 ? '' : 'background:rgba(255,255,255,.02);';
      return '<tr style="' + rowBg + '">' + tds + '</tr>';
    }).join('');
    container.innerHTML = ''
      + '<table style="width:100%;border-collapse:collapse;">'
      + '<thead><tr>' + thead + '</tr></thead>'
      + '<tbody>' + tbody + '</tbody>'
      + '</table>';
  }

  function _applyFilter(rows, q) {
    var qq = String(q || '').trim().toLowerCase();
    if (!qq) return rows;
    return rows.filter(function(r) {
      for (var k in r) {
        if (r[k] != null && String(r[k]).toLowerCase().indexOf(qq) >= 0) return true;
      }
      return false;
    });
  }

  /* ─────────────────────────────────────────────────────────────────────
     공개 함수: LOT 리스트 모달
     ───────────────────────────────────────────────────────────────────── */
  window.showLotListModal = function() {
    var m = _ensureModal();
    m.style.display = 'flex';
    document.getElementById('sqm-listview-title').textContent = '📊 LOT 리스트';
    var body = document.getElementById('sqm-listview-body');
    var foot = document.getElementById('sqm-listview-foot');
    var cnt  = document.getElementById('sqm-listview-count');
    body.innerHTML = '<div style="text-align:center;color:var(--text-muted);padding:40px;">⏳ 로딩 중...</div>';
    cnt.textContent = '';
    foot.textContent = '';

    var url = _api() + '/api/action/lot-list-json';
    var allRows = [];

    function _load() {
      body.innerHTML = '<div style="text-align:center;color:var(--text-muted);padding:40px;">⏳ 로딩 중...</div>';
      fetch(url).then(function(r) { return r.json(); })
        .then(function(res) {
          var rows = (res && res.data && res.data.rows) || res.rows || [];
          allRows = rows;
          cnt.textContent = '— ' + rows.length + ' 건';
          _renderTable(LOT_COLS, rows, body);
          foot.textContent = '※ 엑셀 다운로드는 우상단 버튼 사용 · 전체 ' + rows.length + ' LOT';
        })
        .catch(function(e) {
          body.innerHTML = '<div style="text-align:center;color:var(--danger,#f44336);padding:40px;">'
            + '❌ 로딩 실패: ' + _esc(e.message || e) + '</div>';
          _toast('error', 'LOT 리스트 로딩 실패');
        });
    }

    document.getElementById('sqm-listview-excel').onclick = function() {
      _dlUrl(_api() + '/api/action/export-lot-excel', 'LOT 리스트 Excel');
    };
    document.getElementById('sqm-listview-refresh').onclick = _load;
    var fInp = document.getElementById('sqm-listview-filter');
    fInp.value = '';
    fInp.oninput = function() {
      _renderTable(LOT_COLS, _applyFilter(allRows, this.value), body);
    };

    _load();
  };

  /* ─────────────────────────────────────────────────────────────────────
     공개 함수: 톤백 리스트 모달
     ───────────────────────────────────────────────────────────────────── */
  window.showTonbagListModal = function(lotNo) {
    var m = _ensureModal();
    m.style.display = 'flex';
    var ttl = '🎒 톤백 리스트';
    if (lotNo) ttl += ' — ' + lotNo;
    document.getElementById('sqm-listview-title').textContent = ttl;
    var body = document.getElementById('sqm-listview-body');
    var foot = document.getElementById('sqm-listview-foot');
    var cnt  = document.getElementById('sqm-listview-count');
    body.innerHTML = '<div style="text-align:center;color:var(--text-muted);padding:40px;">⏳ 로딩 중...</div>';
    cnt.textContent = '';
    foot.textContent = '';

    var url = _api() + '/api/action2/tonbag-list-json' + (lotNo ? '?lot_no=' + encodeURIComponent(lotNo) : '');
    var allRows = [];

    function _load() {
      body.innerHTML = '<div style="text-align:center;color:var(--text-muted);padding:40px;">⏳ 로딩 중...</div>';
      fetch(url).then(function(r) { return r.json(); })
        .then(function(res) {
          var rows = (res && res.data && res.data.rows) || res.rows || [];
          allRows = rows;
          cnt.textContent = '— ' + rows.length + ' 건';
          _renderTable(TONBAG_COLS, rows, body);
          foot.textContent = '※ 엑셀 다운로드는 우상단 버튼 사용 · 전체 ' + rows.length + ' 톤백';
        })
        .catch(function(e) {
          body.innerHTML = '<div style="text-align:center;color:var(--danger,#f44336);padding:40px;">'
            + '❌ 로딩 실패: ' + _esc(e.message || e) + '</div>';
          _toast('error', '톤백 리스트 로딩 실패');
        });
    }

    document.getElementById('sqm-listview-excel').onclick = function() {
      var dlUrl = _api() + '/api/action2/export-tonbag-excel' + (lotNo ? '?lot_no=' + encodeURIComponent(lotNo) : '');
      _dlUrl(dlUrl, '톤백리스트 Excel');
    };
    document.getElementById('sqm-listview-refresh').onclick = _load;
    var fInp = document.getElementById('sqm-listview-filter');
    fInp.value = '';
    fInp.oninput = function() {
      _renderTable(TONBAG_COLS, _applyFilter(allRows, this.value), body);
    };

    _load();
  };

})();
