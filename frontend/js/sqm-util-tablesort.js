/* =======================================================================
   SQM Inventory - sqm-util-tablesort.js — 테이블 헤더 클릭 정렬
   Extracted from sqm-inline.js (Phase B-S3) — 2026-05-23
   Source: sqm-inline.js (현 line 224-261)
   ======================================================================= */
(function () {
  'use strict';
  if (window.__SQM_UTIL_TABLESORT_INSTALLED__) return;
  window.__SQM_UTIL_TABLESORT_INSTALLED__ = true;

  /* ===================================================
     1a. TABLE SORT — 컬럼 헤더 클릭으로 정렬 (v864.2 동일)
     사용법: <th> 에 자동 바인딩, 숫자/문자/날짜 자동 감지
     =================================================== */
  function enableTableSort(tableEl) {
    if (!tableEl || tableEl.dataset._sortBound) return;
    tableEl.dataset._sortBound = '1';
    var headers = tableEl.querySelectorAll('thead th');
    headers.forEach(function(th, colIdx) {
      th.style.cursor = 'pointer';
      th.style.userSelect = 'none';
      th.title = 'Click to sort';
      th.addEventListener('click', function() {
        var tbody = tableEl.querySelector('tbody');
        if (!tbody) return;
        var rows = Array.prototype.slice.call(tbody.querySelectorAll('tr'));
        var asc = th.dataset._sortDir !== 'asc';
        // 모든 th 리셋
        headers.forEach(function(h){ h.dataset._sortDir=''; h.textContent=h.textContent.replace(/ [▲▼]/g,''); });
        th.dataset._sortDir = asc ? 'asc' : 'desc';
        th.textContent = th.textContent + (asc ? ' ▲' : ' ▼');
        rows.sort(function(a, b) {
          var ca = (a.children[colIdx]||{}).textContent||'';
          var cb = (b.children[colIdx]||{}).textContent||'';
          // 숫자 감지
          var na = parseFloat(ca.replace(/,/g,'')), nb = parseFloat(cb.replace(/,/g,''));
          if (!isNaN(na) && !isNaN(nb)) return asc ? na-nb : nb-na;
          return asc ? ca.localeCompare(cb) : cb.localeCompare(ca);
        });
        rows.forEach(function(r){ tbody.appendChild(r); });
      });
    });
  }

  /* 페이지 렌더링 후 자동으로 테이블 정렬 바인딩 */
  var _sortObserver = new MutationObserver(function() {
    document.querySelectorAll('.data-table').forEach(enableTableSort);
  });
  _sortObserver.observe(document.documentElement, {childList:true, subtree:true});

  // 글로벌 노출 (sqm-inline.js 의 기존 호출 호환)
  window.enableTableSort = enableTableSort;
})();
