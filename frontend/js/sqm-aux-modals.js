(function () {
  'use strict';

  var API = window.API;
  var apiGet = window.apiGet;
  var apiPost = window.apiPost;
  var extractRows = window.extractRows;
  var escapeHtml = window.escapeHtml;
  var showDataModal = window.showDataModal;
  var showToast = window.showToast;
  var _sqmSyncModalHeaderFromContent = window._sqmSyncModalHeaderFromContent;

  /* ── AI 채팅 모달 ─────────────────────────────────────── */
  function showAiChatModal() {
    var panelId = 'sqm-ai-chat-panel';
    if (document.getElementById(panelId)) {
      document.getElementById(panelId).style.display = 'flex';
      return;
    }
    var examples = ['전체 재고 현황', '제품별 재고', '저재고 LOT', '리튬카보네이트 재고', 'SAP별 현황'];
    var exBtns = examples.map(function(q) {
      return '<button type="button" class="btn btn-ghost" style="font-size:.78rem;padding:3px 8px" onclick="window._aiChatSend('+JSON.stringify(q)+')">' + escapeHtml(q) + '</button>';
    }).join('');

    var panel = document.createElement('div');
    panel.id = panelId;
    panel.style.cssText = 'position:fixed;right:20px;bottom:20px;width:420px;max-height:580px;'
      + 'background:var(--bg-card,#1a2233);border:1px solid var(--border,#2a3a5c);border-radius:12px;'
      + 'box-shadow:0 8px 32px rgba(0,0,0,.5);display:flex;flex-direction:column;z-index:9999;overflow:hidden';
    panel.innerHTML =
      '<div style="background:var(--primary,#2563eb);padding:10px 14px;display:flex;justify-content:space-between;align-items:center">'
      + '<span style="font-weight:700;color:#fff">🤖 AI 재고 조회</span>'
      + '<div style="display:flex;gap:4px;align-items:center">'
      + '<button id="ai-detach-btn" style="background:transparent;border:1px solid rgba(255,255,255,.35);color:#fff;border-radius:4px;padding:2px 8px;cursor:pointer;font-size:13px" onclick="window._sqmDetachAiChat()" title="별도 창으로 분리">&#x29C9;</button>'
      + '<button onclick="document.getElementById(\''+panelId+'\').style.display=\'none\'" style="background:none;border:none;color:#fff;font-size:1.2rem;cursor:pointer;line-height:1">×</button>'
      + '</div>'
      + '</div>'
      + '<div id="ai-chat-history" style="flex:1;overflow-y:auto;padding:12px;display:flex;flex-direction:column;gap:8px;min-height:200px">'
      + '<div style="color:var(--text-muted);font-size:.84rem">안녕하세요! 재고를 자연어로 질문해보세요.</div>'
      + '</div>'
      + '<div style="padding:6px 10px;border-top:1px solid var(--border,#2a3a5c);display:flex;flex-wrap:wrap;gap:4px">' + exBtns + '</div>'
      + '<div style="padding:10px;border-top:1px solid var(--border,#2a3a5c);display:flex;gap:8px">'
      + '<input id="ai-chat-input" type="text" placeholder="질문을 입력하세요..." autocomplete="off"'
      + ' style="flex:1;padding:8px 10px;background:var(--bg-hover,#0d1b2e);color:var(--text,#e2e8f0);border:1px solid var(--border,#2a3a5c);border-radius:6px;font-size:.9rem">'
      + '<button onclick="window._aiChatSend()" class="btn btn-primary" style="padding:8px 14px">전송</button>'
      + '</div>';
    document.body.appendChild(panel);

    document.getElementById('ai-chat-input').addEventListener('keydown', function(e) {
      if (e.key === 'Enter') window._aiChatSend();
    });
  }
  window.showAiChatModal = showAiChatModal;

  window._aiChatSend = function(preset) {
    var inp = document.getElementById('ai-chat-input');
    var msg = preset || (inp ? inp.value.trim() : '');
    if (!msg) return;
    if (inp && !preset) inp.value = '';

    var hist = document.getElementById('ai-chat-history');
    if (!hist) return;

    // 사용자 말풍선
    var uDiv = document.createElement('div');
    uDiv.style.cssText = 'align-self:flex-end;background:var(--primary,#2563eb);color:#fff;padding:7px 12px;border-radius:10px 10px 2px 10px;max-width:85%;font-size:.88rem';
    uDiv.textContent = msg;
    hist.appendChild(uDiv);

    // 로딩
    var aDiv = document.createElement('div');
    aDiv.style.cssText = 'align-self:flex-start;background:var(--bg-hover,#0d1b2e);color:var(--text,#e2e8f0);padding:7px 12px;border-radius:10px 10px 10px 2px;max-width:85%;font-size:.88rem';
    aDiv.textContent = '⏳ 조회 중…';
    hist.appendChild(aDiv);
    hist.scrollTop = hist.scrollHeight;

    apiPost('/api/ai/chat', { message: msg }).then(function(res) {
      aDiv.innerHTML = '';
      var answer = (res && res.answer) ? res.answer : '응답 없음';
      // 줄바꿈 처리
      answer.split('\n').forEach(function(line, i) {
        if (i > 0) aDiv.appendChild(document.createElement('br'));
        aDiv.appendChild(document.createTextNode(line));
      });
      if (res && res.row_count > 0) {
        var meta = document.createElement('div');
        meta.style.cssText = 'margin-top:5px;font-size:.75rem;color:var(--text-muted)';
        meta.textContent = '📊 ' + res.row_count + '건 · ' + (res.elapsed_ms||0) + 'ms';
        aDiv.appendChild(meta);
      }
      hist.scrollTop = hist.scrollHeight;
    }).catch(function(e) {
      aDiv.style.color = 'var(--danger,#f87171)';
      aDiv.textContent = '❌ 오류: ' + (e.message || String(e));
      hist.scrollTop = hist.scrollHeight;
    });
  };

  function showAiToolsHubModal() {
    var h = [
      '<div style="max-width:420px;padding:4px 0">',
      '  <h2 style="margin:0 0 12px 0">🤖 AI / 선사 도구</h2>',
      '  <p style="color:var(--text-muted);font-size:.86rem;margin-bottom:16px">자주 쓰는 항목을 모았습니다.</p>',
      '  <div style="display:flex;flex-direction:column;gap:10px">',
      '    <button type="button" class="btn btn-primary" id="aihub-chat">💬 AI 재고 채팅</button>',
      '    <button type="button" class="btn btn-primary" id="aihub-carrier">🚢 선사 프로파일 (BL 등록)</button>',
      '    <button type="button" class="btn btn-primary" id="aihub-gemini-set">🔐 Gemini API 설정</button>',
      '    <button type="button" class="btn btn-ghost" id="aihub-gemini-test">🧪 Gemini 연결 테스트</button>',
      '  </div>',
      '  <div style="margin-top:16px;text-align:right"><button type="button" class="btn btn-ghost" onclick="document.getElementById(\'sqm-modal\').style.display=\'none\'">닫기</button></div>',
      '</div>'
    ].join('\n');
    showDataModal('', h);
    document.getElementById('aihub-chat').addEventListener('click', function(){ document.getElementById('sqm-modal').style.display='none'; window.showAiChatModal(); });
    document.getElementById('aihub-carrier').addEventListener('click', function(){ document.getElementById('sqm-modal').style.display='none'; window.showCarrierProfileModal(); });
    document.getElementById('aihub-gemini-set').addEventListener('click', function(){ document.getElementById('sqm-modal').style.display='none'; window.showGeminiApiSettingsModal(); });
    document.getElementById('aihub-gemini-test').addEventListener('click', function(){ document.getElementById('sqm-modal').style.display='none'; window.showGeminiApiTestModal(); });
  }
  window.showAiToolsHubModal = showAiToolsHubModal;

  function showReportTemplatesHubModal() {
    function renderFiles(items) {
      var box = document.getElementById('rt-file-list');
      if (!box) return;
      if (!items || !items.length) {
        box.innerHTML = '<div class="empty" style="padding:12px">업로드된 양식 파일이 없습니다 (.xlsx · .pdf 등)</div>';
        return;
      }
      var tbl = '<table class="data-table"><thead><tr><th>파일명</th><th>크기</th><th>수정일</th><th></th></tr></thead><tbody>';
      items.forEach(function(it){
        var nm = it.name || '';
        tbl += '<tr><td style="font-weight:600;word-break:break-all">'+escapeHtml(nm)+'</td><td class="mono-cell">'+(it.size_bytes!=null?Math.round(it.size_bytes/1024)+' KB':'-')+'</td><td style="font-size:.82rem">'+escapeHtml(it.modified_at||'-')+'</td>'
          + '<td><button type="button" class="btn btn-ghost rt-del" style="padding:4px 8px;font-size:.8rem;color:var(--danger,#c62828)" data-enc="'+encodeURIComponent(nm)+'">삭제</button></td></tr>';
      });
      tbl += '</tbody></table>';
      box.innerHTML = tbl;
      box.querySelectorAll('.rt-del').forEach(function(btn){
        btn.addEventListener('click', function(){
          var enc = btn.getAttribute('data-enc');
          var name = enc ? decodeURIComponent(enc) : '';
          if (!name || !window.sqmConfirm('파일을 삭제할까요?')) return;
          fetch(API + '/api/report-templates/file?name=' + encodeURIComponent(name), { method: 'DELETE' })
            .then(function(r){ return r.json(); })
            .then(function(res){
              if (res && res.ok === false) { showToast('error', res.error || '삭제 실패'); return; }
              showToast('success', '삭제됨');
              refreshList();
            }).catch(function(e){ showToast('error', String(e.message||e)); });
        });
      });
    }

    function refreshList() {
      apiGet('/api/report-templates/list').then(function(res){
        var d = res.data || res || {};
        renderFiles(d.items || []);
      }).catch(function(){
        var box = document.getElementById('rt-file-list');
        if (box) box.innerHTML = '<div class="empty">목록 조회 실패</div>';
      });
    }

    var h = [
      '<div style="max-width:520px;padding:4px 0">',
      '  <h2 style="margin:0 0 10px 0">📂 보고서 양식 · 데이터</h2>',
      '  <p style="color:var(--text-muted);font-size:.86rem;margin-bottom:12px">',
      '    <code>data/report_templates/</code> 에 보관되는 업로드 양식입니다. 일·월·재고 집계는 아래 버튼으로 확인합니다.',
      '  </p>',
      '  <div style="margin-bottom:14px;padding:12px;background:var(--bg-hover);border-radius:8px;border:1px solid var(--border)">',
      '    <div style="font-weight:600;margin-bottom:8px">양식 파일 업로드</div>',
      '    <input type="file" id="rt-file" accept=".xlsx,.xls,.pdf,.docx,.csv,.html" style="margin-bottom:8px"/>',
      '    <button type="button" class="btn btn-primary" id="rt-upload">업로드</button>',
      '  </div>',
      '  <h3 style="font-size:1rem;margin:0 0 8px">저장된 양식</h3>',
      '  <div id="rt-file-list" style="max-height:220px;overflow:auto;border:1px solid var(--border);border-radius:8px;margin-bottom:14px"><div class="empty" style="padding:12px">⏳ 로딩 중...</div></div>',
      '  <div style="display:flex;flex-direction:column;gap:8px">',
      '    <button type="button" class="btn btn-primary" id="rt-daily">📊 일일 현황 데이터</button>',
      '    <button type="button" class="btn btn-primary" id="rt-monthly">📅 월간 실적 데이터</button>',
      '    <button type="button" class="btn btn-ghost" id="rt-inv">📦 재고 현황 보고서(집계)</button>',
      '  </div>',
      '  <div style="margin-top:16px;text-align:right"><button type="button" class="btn btn-ghost" onclick="document.getElementById(\'sqm-modal\').style.display=\'none\'">닫기</button></div>',
      '</div>'
    ].join('\n');
    showDataModal('', h);
    document.getElementById('rt-daily').addEventListener('click', function(){ document.getElementById('sqm-modal').style.display='none'; window.renderInfoModal('일일 보고서', '/api/q2/report-daily'); });
    document.getElementById('rt-monthly').addEventListener('click', function(){ document.getElementById('sqm-modal').style.display='none'; window.renderInfoModal('월간 보고서', '/api/q2/report-monthly'); });
    document.getElementById('rt-inv').addEventListener('click', function(){ document.getElementById('sqm-modal').style.display='none'; window.renderInfoModal('재고 현황 보고서', '/api/q/inventory-report'); });
    document.getElementById('rt-upload').addEventListener('click', function(){
      var fi = document.getElementById('rt-file');
      if (!fi || !fi.files || !fi.files[0]) { showToast('warning', '파일을 선택하세요'); return; }
      var fd = new FormData();
      fd.append('file', fi.files[0]);
      fetch(API + '/api/report-templates/upload', { method: 'POST', body: fd })
        .then(function(r){ return r.json(); })
        .then(function(res){
          if (res && res.ok === false) { showToast('error', res.error || '업로드 실패'); return; }
          showToast('success', res.message || '업로드 완료');
          fi.value = '';
          refreshList();
        }).catch(function(e){ showToast('error', String(e.message||e)); });
    });
    refreshList();
  }
  window.showReportTemplatesHubModal = showReportTemplatesHubModal;

  function showReportHistoryAuditModal() {
    showDataModal('📋 보고서·작업 이력', '<div style="padding:20px;text-align:center">⏳ 로딩 중...</div>');
    apiGet('/api/q/audit-log?limit=150').then(function(res){
      var rows = extractRows(res);
      if (!rows.length) {
        document.getElementById('sqm-modal-content').innerHTML = '<h2>📋 보고서·작업 이력</h2><div class="empty">감사 로그가 없습니다</div>';
        _sqmSyncModalHeaderFromContent();
        return;
      }
      var prefer = rows.filter(function(r){
        var t = ((r.event_type || '') + ' ' + (String(r.event_data || ''))).toUpperCase();
        return t.indexOf('PDF') >= 0 || t.indexOf('REPORT') >= 0 || t.indexOf('SOLD') >= 0 || t.indexOf('INBOUND') >= 0;
      });
      var show = prefer.length ? prefer.slice(0, 80) : rows.slice(0, 80);
      var tbl = '<table class="data-table"><thead><tr><th>시간</th><th>유형</th><th>요약</th></tr></thead><tbody>';
      show.forEach(function(r){
        var ts = escapeHtml(r.created_at || r.ts || '-');
        var et = escapeHtml(r.event_type || '-');
        var ed = r.event_data != null ? String(r.event_data) : '';
        if (ed.length > 120) ed = ed.slice(0, 117) + '…';
        tbl += '<tr><td style="white-space:nowrap;font-size:.82rem">' + ts + '</td><td><span class="tag">' + et + '</span></td><td style="font-size:.82rem;max-width:280px;word-break:break-all">' + escapeHtml(ed) + '</td></tr>';
      });
      tbl += '</tbody></table>';
      document.getElementById('sqm-modal-content').innerHTML = [
        '<h2 style="margin-bottom:8px">📋 보고서·작업 이력</h2>',
        '<p style="color:var(--text-muted);font-size:.85rem;margin-bottom:10px">audit_log 기준 최근 ' + show.length + '건 (PDF·보고서·입출고 관련 우선 표시)</p>',
        tbl
      ].join('');
      _sqmSyncModalHeaderFromContent();
    }).catch(function(e){
      document.getElementById('sqm-modal-content').innerHTML = '<h2>이력</h2><div class="empty">조회 실패</div>';
      _sqmSyncModalHeaderFromContent();
    });
  }
  window.showReportHistoryAuditModal = showReportHistoryAuditModal;

  function renderInfoModal(title, endpoint) {
    showDataModal(title,'<div style="padding:20px;text-align:center">⏳ 로딩 중...</div>');
    apiGet(endpoint).then(function(res){
      var d=res.data||res||{};
      var html;
      if (endpoint === '/api/info/version') {
        var note = d.build_note ? String(d.build_note).split('\n').slice(0, 18).join('\n') : '';
        html = ''
          + '<div class="metrics-grid" style="grid-template-columns:repeat(2,minmax(180px,1fr));margin-bottom:14px">'
          + '<div class="metric-card"><div class="metric-label">프로그램</div><div class="metric-value" style="font-size:1.15rem">' + escapeHtml(d.app_name || 'SQM 재고관리 시스템') + '</div></div>'
          + '<div class="metric-card"><div class="metric-label">버전</div><div class="metric-value" style="font-size:1.4rem">v' + escapeHtml(d.version || '-') + '</div></div>'
          + '<div class="metric-card"><div class="metric-label">릴리즈 날짜</div><div class="metric-value" style="font-size:1rem">' + escapeHtml(d.release_date || '-') + '</div></div>'
          + '<div class="metric-card"><div class="metric-label">빌드 날짜</div><div class="metric-value" style="font-size:1rem">' + escapeHtml(d.build_date || '-') + '</div></div>'
          + '</div>';
        if (note) {
          html += '<h3 style="margin:10px 0 8px">변경 요약</h3><pre style="white-space:pre-wrap;max-height:260px;overflow:auto;background:var(--bg-muted,#f6f8fa);border:1px solid var(--panel-border);border-radius:8px;padding:12px;font-size:.86rem;line-height:1.5">' + escapeHtml(note) + '</pre>';
        }
      } else if (typeof d==='string') {
        html='<pre style="white-space:pre-wrap;font-size:.9rem">'+escapeHtml(d)+'</pre>';
      } else if (Array.isArray(d)) {
        html='<table class="data-table"><tbody>'+d.map(function(row){
          if (typeof row==='object'&&row!==null)
            return '<tr>'+Object.values(row).map(function(v){ return '<td>'+escapeHtml(String(v))+'</td>'; }).join('')+'</tr>';
          return '<tr><td>'+escapeHtml(String(row))+'</td></tr>';
        }).join('')+'</tbody></table>';
      } else {
        // v868 fix (2026-05-15): 객체/배열을 [object Object]로 표시하던 버그 수정
        // issues(배열), stats(객체) 등 중첩 데이터를 보기 좋게 포맷
        var _fmtVal = function(v) {
          if (v === null || v === undefined) return '-';
          if (Array.isArray(v)) {
            if (v.length === 0) return '(빈 배열)';
            // 배열 안이 객체면 nested table, 원시값이면 콤마 join
            if (typeof v[0] === 'object' && v[0] !== null) {
              var keys = Object.keys(v[0]);
              var head = '<thead><tr>'+keys.map(function(k){return '<th style="font-size:.8rem;padding:4px 8px">'+escapeHtml(k)+'</th>';}).join('')+'</tr></thead>';
              var body = '<tbody>'+v.map(function(row){
                return '<tr>'+keys.map(function(k){
                  var cell = row[k];
                  return '<td style="font-size:.8rem;padding:4px 8px">'+escapeHtml(cell === null || cell === undefined ? '-' : (typeof cell === 'object' ? JSON.stringify(cell) : String(cell)))+'</td>';
                }).join('')+'</tr>';
              }).join('')+'</tbody>';
              return '<table class="data-table" style="margin:0;font-size:.85rem">'+head+body+'</table>';
            }
            return v.map(function(x){return String(x);}).join(', ');
          }
          if (typeof v === 'object') {
            return '<table class="data-table" style="margin:0;font-size:.85rem"><tbody>'+Object.entries(v).map(function(kv2){
              return '<tr><td style="font-weight:600;padding:3px 8px">'+escapeHtml(kv2[0])+'</td><td style="padding:3px 8px">'+escapeHtml(String(kv2[1]))+'</td></tr>';
            }).join('')+'</tbody></table>';
          }
          return escapeHtml(String(v));
        };
        html='<table class="data-table"><tbody>'+Object.entries(d).map(function(kv){
          return '<tr><td style="font-weight:600;width:40%;vertical-align:top">'+escapeHtml(kv[0])+'</td><td>'+_fmtVal(kv[1])+'</td></tr>';
        }).join('')+'</tbody></table>';
      }
      document.getElementById('sqm-modal-content').innerHTML='<h2 style="margin-bottom:16px">'+escapeHtml(title)+'</h2>'+html;
      _sqmSyncModalHeaderFromContent();
    }).catch(function(e){
      document.getElementById('sqm-modal-content').innerHTML='<h2>'+escapeHtml(title)+'</h2><div class="empty">Load failed: '+escapeHtml(e.message||String(e))+'</div>';
      _sqmSyncModalHeaderFromContent();
    });
  }
  window.renderInfoModal = renderInfoModal;

  window.showLotDetail = function(lotNo) {
    if (!lotNo) return;
    showDataModal('LOT Detail: '+lotNo,'<div style="padding:20px;text-align:center">⏳ 로딩 중...</div>');
    apiGet('/api/action/lot-detail/'+encodeURIComponent(lotNo)).then(function(res){
      var d=res.data||res||{};
      var html='<table class="data-table"><tbody>'+Object.entries(d).map(function(kv){
        return '<tr><td style="font-weight:600;width:40%">'+escapeHtml(kv[0])+'</td><td>'+escapeHtml(String(kv[1]))+'</td></tr>';
      }).join('')+'</tbody></table>';
      document.getElementById('sqm-modal-content').innerHTML='<h2 style="margin-bottom:16px">LOT Detail: '+escapeHtml(lotNo)+'</h2>'+html;
      _sqmSyncModalHeaderFromContent();
    }).catch(function(e){
      document.getElementById('sqm-modal-content').innerHTML='<h2>LOT Detail: '+escapeHtml(lotNo)+'</h2><div class="empty">Load failed: '+escapeHtml(e.message||String(e))+'</div>';
      _sqmSyncModalHeaderFromContent();
    });
  };

})();
