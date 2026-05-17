# 작업 지시서 — 모달 → 별도 PyWebView 윈도우 분리

**작성일:** 2026-05-11 21:08 KST
**작성자:** 루비 (이전 세션)
**대상:** 다음 세션의 Claude
**프로젝트:** SQM Inventory v8.6.7 (`D:\program\SQM_inventory\SQM_v868_claan`)
**브랜치:** main (commit 4a1a0d3)

---

## 0. 새 세션 시작 시 첫 행동

```text
1. 이 파일을 그대로 읽으십시오
2. CLAUDE.md (프로젝트 루트)를 읽으십시오
3. 리오님께 "B-라이트 / B-풀 / B-맥스" 옵션 확정 받으십시오
4. 확정 후 Phase 0부터 순서대로 실행하십시오
```

---

## 1. 사용자 요구사항 (리오님 최종 의도)

### 핵심 욕구
> "AI 채팅창 같은 팝업이 메인 SQM 창의 경계를 못 벗어나는데, 마우스로 자유롭게 드래그할 수 있게 해 달라."

### 결정된 사항
- ✅ **방법 ① 채택**: HTML 모달이 아닌 **별도 PyWebView 윈도우**로 분리
- ✅ **도킹/분리 토글 추가**: 사용자가 모달 ↔ 별도 윈도우 전환 가능
- ✅ **EXE 빌드(5/15~16) 전에 완료**
- ✅ **smoke test + pytest 병행**으로 단계별 검증
- ✅ **워크트리 격리** 후 작업 → 검증 통과 시 main으로 머지
- ⚠️ **옵션 미확정**: B-라이트 / B-풀 / B-맥스 중 리오님 확정 필요

---

## 2. 3가지 옵션 (다음 세션에서 리오님 확정 받을 것)

### 🟢 B-라이트 (루비 권장)
| 항목 | 내용 |
|---|---|
| 포함 | AI 채팅 분리 + 정합성 검사 분리 + 도킹/분리 토글 |
| 제외 | 재고 조회 (페이지라서 비용 큼) |
| 소요 | 약 3.5시간 |
| 리스크 | 낮음 |
| EXE 빌드 일정 | 안전 |

### 🟡 B-풀
| 항목 | 내용 |
|---|---|
| 포함 | 위 3개 + 재고 **보고서 모달**만 분리 |
| 제외 | 재고 페이지 전체 |
| 소요 | 약 5시간 |
| 리스크 | 중간 |

### 🔴 B-맥스
| 항목 | 내용 |
|---|---|
| 포함 | 위 3개 + 재고 조회 페이지 통째 분리 |
| 소요 | 6.5~8.5시간 |
| 리스크 | 높음 (페이지 상태 동기화 문제) |
| EXE 빌드 일정 | 부담 |

---

## 3. 핵심 발견 (코드 위치)

```text
AI 채팅
  - 진입점:  frontend/js/sqm-inline.js 6209  (button #aihub-chat)
  - 함수:    showAiChatModal()              (sqm-inline.js 6122)
  - 구조:    동적으로 <div id="sqm-ai-chat-panel"> 생성 → body에 append
            (index.html에 정적 모달 X)

정합성 검사
  - 진입점:  onIntegrityCheck, tb-integrity, #adv-int (sqm-inline.js 6497/6554/6093)
  - 함수:    renderInfoModal(title, '/api/action/integrity-check')  (sqm-inline.js 6346)
  - 구조:    공용 #sqm-modal 재활용 (sqm-inline.js 2741~2755)

재고 조회 (B-맥스 옵션일 때만)
  - 진입점:  onInventoryList, tb-inventory (sqm-inline.js 6490/6553)
  - 함수:    loadInventoryPage() (sqm-inline.js 807)
  - 구조:    ⚠️ 모달이 아니라 라우트 페이지 — #page-container에 그려짐

PyWebView 진입점
  - 파일:    main_webview.py
  - 클래스:  SqmPywebviewApi (line 319~405)
  - 윈도우:  webview.create_window (line 407~427)
  - 버그:    exit_app 메서드 누락 (line 289 부근) — 동시 수정 권장
```

---

## 4. 구현 방식 (확정된 설계)

### 4.1 PyWebView 다중 윈도우
- `SqmPywebviewApi` 클래스에 신규 메서드 3개 추가:
  - `open_detached_window(window_key: str)`
  - `close_detached_window(window_key: str)`
  - `broadcast_event(event_name: str, payload: dict)`
- 모듈 전역 dict: `_DETACHED_WINDOWS: dict[str, webview.Window] = {}`
- 윈도우 간 통신: **백엔드 SQLite를 단일 진실 원천**으로 (양쪽 HTTP fetch)

### 4.2 도킹/분리 토글
- 헤더 우측(X 버튼 좌측)에 `<button class="sqm-dock-toggle" data-window-key="...">📌</button>`
- 상태 저장: **localStorage** (SQLite 사용 X)
  - 키: `sqm_dock_state_ai_chat`, `sqm_dock_state_integrity` 등
  - 값: `'docked'` | `'detached'`
- 토글 동작:
  - 모달 상태에서 클릭 → `pywebview.api.open_detached_window(key)` → 모달 close
  - 별도창에서 클릭 → 부모창에 신호 → 모달 재오픈 → 자기 자신 close
- 앱 시작 시 `on_loaded`에서 localStorage 읽어서 자동 복원

---

## 5. 영향 파일 목록 (정확한 위치)

### 5.1 수정
| 파일 | 줄 | 변경 |
|---|---|---|
| `main_webview.py` | 319~405 | `SqmPywebviewApi` 메서드 3개 추가 |
| `main_webview.py` | 407~427 | `_DETACHED_WINDOWS` 전역 dict 추가 |
| `main_webview.py` | 289 부근 | `exit_app` 메서드 누락 버그 수정 (선택) |
| `frontend/js/sqm-inline.js` | 6122~6157 | `showAiChatModal()` 헤더에 토글 버튼 추가 |
| `frontend/js/sqm-inline.js` | 6122 직전 | 헬퍼 함수 4개 신규 정의 (약 60줄) |
| `frontend/js/sqm-inline.js` | 2741~2755 | 공용 모달 헤더에 토글 (분기 필요) |
| `frontend/js/sqm-inline.js` | 6346 부근 | `renderInfoModal()` integrity 분기 |
| `backend/api/__init__.py` | 407~412 부근 | 정적 라우트 `/detached/{key}` 추가 |

### 5.2 신규 생성
| 파일 | 용도 |
|---|---|
| `frontend/detached/ai_chat.html` | AI 채팅 보조 창 |
| `frontend/detached/integrity.html` | 정합성 검사 보조 창 |
| `frontend/detached/inventory.html` | B-맥스 옵션 시만 |
| `frontend/js/detached_common.js` | 공통 헬퍼 |
| `frontend/css/detached.css` | 보조 창 스타일 |

---

## 6. CLAUDE.md 규칙 준수

### 위반 없음 ✅
- `engine_modules/`, `features/`, `parsers/`, `utils/` 전혀 건드리지 않음

### 주의 ⚠️
- `main_webview.py` 수정 시 약 60줄 추가 → **300줄 미만이므로 Edit 도구 사용 가능**
- `frontend/js/sqm-inline.js` (5853줄짜리) → **모든 수정은 Python 스크립트로 in-place patch 필수** (Edit 도구 금지, Rule 5)
- git commit/push은 **Windows CMD에서만** (Rule 6)
- 색상은 `design-tokens.css` 변수만 사용 (하드코딩 금지)

---

## 7. Phase별 작업 순서 (B-라이트 기준)

### Phase 0 — 사전 검증 (15분)
```bash
python -m py_compile main_webview.py
node --check frontend/js/sqm-inline.js
# 베이스라인 통과 확인
```

### Phase 1 — AI 채팅 분리 (90분)
- `SqmPywebviewApi.open_detached_window` 구현
- `frontend/detached/ai_chat.html` 신규 생성
- `showAiChatModal()`에 토글 버튼 추가
- localStorage 키 정의
- **테스트**: `pytest tests/test_ai_fallback_router.py`
- **smoke**: 메뉴 클릭 → 새 창 열림 → AI 응답 정상

### Phase 2 — 정합성 검사 분리 (60분)
- 정합성 모달에 토글 적용
- `frontend/detached/integrity.html` 신규
- `renderInfoModal` 분기 처리
- **테스트**: `pytest tests/test_smoke_workflow.py`
- **smoke**: 정합성 검사 모달 → 분리 → 정상 동작

### Phase 3 — 통합 및 정리 (30분)
- 부모 ↔ 보조 동기화 (`broadcast_event`)
- 앱 종료 시 모든 자식 창 close
- localStorage 영속성 검증

### Phase 4 — 최종 검증 (30분)
- 전체 `pytest -x`
- `python main_webview.py` 수동 smoke test
- PyInstaller `--add-data frontend/detached` 빌드 호환성 확인

---

## 8. Phase별 git commit 메시지 (제안)

```text
Phase 1 완료 후:
  feat(modal): AI chat detached window + dock/undock toggle

Phase 2 완료 후:
  feat(modal): integrity check detached window

Phase 3 완료 후:
  feat(modal): cross-window broadcast + cleanup on exit

Phase 4 완료 후 (옵션 B-풀/B-맥스만):
  feat(modal): inventory report/page detached window
```

> ⚠️ **git commit은 반드시 Windows CMD에서**. Linux mount(VM)에서 시도 금지 (Rule 6).

---

## 9. 리스크 Top 3 (대응 방안 포함)

### 리스크 1 — JS API 공유 문제
- 현상: `SqmPywebviewApi`가 `webview.windows[0]` 가정 (line 344~346)
- 영향: 보조 창에서 엑셀 다운로드 호출 시 부모 창에 다이얼로그 뜸
- 대응: 각 메서드에서 호출 윈도우 식별 필요. JS에서 `window_key` 인자 명시 전달.

### 리스크 2 — 재고 조회 페이지 상태 동기화
- 현상: 페이지 상태(필터/정렬/스크롤) 두 창 사이 미동기
- 영향: 사용자 혼란
- 대응: **B-라이트 채택 시 해당 없음**. B-풀/B-맥스 채택 시만 적용.

### 리스크 3 — PyInstaller EXE 빌드 누락
- 현상: 신규 `frontend/detached/*.html` 파일이 `--add-data` 누락 시 EXE에서 404
- 대응: `*.spec` 또는 `build_*.bat` 동시 갱신. `main_webview.py`의 `FRONTEND_DIR` (line 24)이 frozen 경로 처리 중 — 보조 창도 같은 처리 필요.

---

## 10. 성공 기준 (Definition of Done)

- [ ] B-라이트(또는 선택된 옵션) 모든 Phase 완료
- [ ] `pytest -x` 전수 통과
- [ ] `python -m py_compile main_webview.py` 통과
- [ ] `node --check frontend/js/sqm-inline.js` 통과
- [ ] 리오님이 직접 SQM 실행 → AI 채팅 분리 → 메인 창 밖으로 이동 확인
- [ ] 도킹/분리 토글 양방향 정상 동작
- [ ] 앱 재시작 시 마지막 상태 복원
- [ ] PyInstaller로 EXE 빌드 → 분리 윈도우 정상 동작
- [ ] git commit 4개 (또는 옵션별 개수) 완료
- [ ] CLAUDE.md 현행화 (Status 섹션에 본 작업 반영)

---

## 11. 다음 세션 시작 시 첫 4가지 질문 (리오님께)

1. **옵션 확정**: B-라이트 / B-풀 / B-맥스 중 어느 것?
2. **워크트리 사용 여부**: 별도 워크트리 격리 후 작업 → 검증 후 머지? 또는 main에 직접 작업?
3. **각 Phase 끝마다 확인**: 리오님이 직접 SQM 실행해서 확인하시겠는지, 또는 끝까지 진행 후 한 번에?
4. **시작 시각**: 지금 시작? 또는 EXE 빌드(5/15~16) 며칠 전부터?

---

## 12. 참고 자료

- `CLAUDE.md` (프로젝트 루트) — 핵심 규칙 5개, Status 설계, DON'T 리스트
- `docs/claude/CLAUDE.history.md` — 학습 로그
- `WORK_ORDER_P4P5P7P10_20260507.md` — 이전 작업 지시서 (참고용)
- 본 파일 — `WORK_ORDER_MODAL_SEPARATION_20260511.md`

---

## 13. 한 줄 요약

> "AI 채팅과 정합성 검사 모달을 별도 PyWebView 윈도우로 분리하고,
>  도킹/분리 토글로 사용자가 전환 가능하게 만든다.
>  소요 3.5시간(B-라이트), EXE 빌드 전 완료."

---

# PART 2 — Pending 입고 확정 UI (PENDING → AVAILABLE)

**추가일:** 2026-05-11 21:21 KST
**관계:** Part 1 (모달 분리)과 **별개 작업**. 같은 세션에서 처리하되 git commit은 분리.
**총 변경 라인:** 약 100줄 (Rule 5 안전)

---

## P2-1. 목적

CLAUDE.md의 STATUS 설계 (2026-05-11 확정)에서:
```text
PENDING   → 포트 입항, 창고 미반입 (파싱 직후)
AVAILABLE → 창고 반입 확정 (재고 집계 시작)
```

현재 Pending 페이지에 **PENDING → AVAILABLE 전환 UI가 없음**.
백엔드 API(`/api/inbound/confirm/{lot}`)는 존재(commit 053fa7a)하지만 프론트 진입점 부재.

→ **Pending 페이지 각 행에 작업 버튼 추가**.

---

## P2-2. 위치

```text
모든 코드: frontend/js/sqm-inventory.js
  - loadPendingPage() 부근 (line 462~477)
  - 파일 끝 })() 직전 (신규 함수 2개)

백엔드 안전장치: backend/api/inbound.py
  - confirm_inbound() 함수 안 (line 2244 부근)
```

---

## P2-3. 단계별 구현 (6단계)

### ① Pending 테이블 헤더에 "⚙️" 컬럼 추가
**파일:** `frontend/js/sqm-inventory.js` (line 462~465 부근)

```javascript
// 기존
+ '<th>#</th><th>LOT</th><th>Product</th><th>Grade</th>'
+ '<th>Qty</th><th>Unit</th><th>BL No</th><th>Vessel</th>'
+ '<th>Arrival Date</th><th>등록일</th>'

// 변경 — 마지막에 작업 컬럼 1개 추가
+ '<th>#</th><th>LOT</th><th>Product</th><th>Grade</th>'
+ '<th>Qty</th><th>Unit</th><th>BL No</th><th>Vessel</th>'
+ '<th>Arrival Date</th><th>등록일</th><th style="width:48px;text-align:center">⚙️</th>'
```

### ② 각 행 마지막에 "⋯" 버튼 셀 추가
**파일:** `frontend/js/sqm-inventory.js` (line 477 부근)

```javascript
// 기존 row 렌더링 마지막
+ '<td class="mono-cell" style="color:var(--text-muted)">' + escapeHtml((r.created_at||'').slice(0,10)) + '</td>'
+ '</tr>';

// 변경 — 작업 버튼 td 1개 추가
+ '<td class="mono-cell" style="color:var(--text-muted)">' + escapeHtml((r.created_at||'').slice(0,10)) + '</td>'
+ '<td style="text-align:center">'
+   '<button class="btn btn-ghost btn-xs pending-action-btn"'
+     ' data-lot="' + escapeHtml(r.lot_no||'') + '"'
+     ' data-port="' + escapeHtml(r.port_date || r.arrival_date || '') + '"'
+     ' style="padding:2px 8px;font-size:14px;cursor:pointer">⋯</button>'
+ '</td>'
+ '</tr>';
```

### ③ `c.innerHTML = html;` 직후 버튼 이벤트 바인딩
**위치:** `loadPendingPage()` 안 `c.innerHTML = html;`과 `setTimeout` 사이

```javascript
c.querySelectorAll('.pending-action-btn').forEach(function(btn){
  btn.addEventListener('click', function(ev){
    ev.stopPropagation();
    window.showPendingActionMenu(btn);
  });
});
```

### ④ 컨텍스트 메뉴 함수 (파일 끝 `})()` 직전)

```javascript
// ════════════════════════════════════════════════════════════════════
// PENDING → AVAILABLE 입고 확정 UI (Option A: context menu + modal)
// ════════════════════════════════════════════════════════════════════
window.showPendingActionMenu = function(btn) {
  var lot      = btn.dataset.lot  || '';
  var portDate = btn.dataset.port || '';
  window._openContextMenu(btn, [
    { icon:'📋', label:'LOT 상세 보기', kbd:'Enter',
      fn:function(){ if (window.showLotDetail) window.showLotDetail(lot); } },
    { icon:'📄', label:'LOT 번호 복사', kbd:'Ctrl+C',
      fn:function(){
        if (navigator.clipboard) navigator.clipboard.writeText(lot);
        window.showToast && window.showToast('info', 'LOT 복사: ' + lot);
      } },
    '-',
    { icon:'✅', label:'입고 확정 → AVAILABLE', kbd:'A', color:'#22c55e',
      fn:function(){ window.showPendingConfirmModal(lot, portDate); } },
  ]);
};
```

### ⑤ 입고 확정 모달 함수 (`showPendingActionMenu` 바로 아래)

```javascript
window.showPendingConfirmModal = function(lot, portDate) {
  var today     = new Date().toISOString().slice(0,10);
  var portLabel = portDate ? portDate : '(미상)';
  var html = [
    '<div style="max-width:420px;padding:4px 0">',
    '  <h2 style="margin:0 0 12px 0">✅ 입고 확정 — ' + escapeHtml(lot) + '</h2>',
    '  <div style="margin-bottom:14px;padding:10px;background:var(--bg-hover);border-radius:6px;font-size:.86rem">',
    '    포트 입항일: <strong>' + escapeHtml(portLabel) + '</strong>',
    '  </div>',
    '  <div style="display:grid;grid-template-columns:140px 1fr;gap:12px;align-items:center;margin-bottom:16px">',
    '    <label style="font-weight:600">실제 창고 반입일 *</label>',
    '    <input type="date" id="pc-inbound-date" value="' + today + '"',
    '           style="padding:7px;background:var(--bg-hover);color:var(--text);border:1px solid var(--border);border-radius:5px;width:100%">',
    '    <label style="font-weight:600">입고 유형 *</label>',
    '    <div style="display:flex;gap:14px">',
    '      <label style="display:flex;align-items:center;gap:5px;cursor:pointer">',
    '        <input type="radio" name="pc-type" value="DIRECT" checked> DIRECT (직반입)',
    '      </label>',
    '      <label style="display:flex;align-items:center;gap:5px;cursor:pointer">',
    '        <input type="radio" name="pc-type" value="BOND"> BOND (보세창고 경유)',
    '      </label>',
    '    </div>',
    '  </div>',
    '  <div style="display:flex;gap:8px;justify-content:flex-end;border-top:1px solid var(--border);padding-top:12px">',
    '    <button id="pc-cancel-btn"  class="btn btn-ghost">취소</button>',
    '    <button id="pc-confirm-btn" class="btn btn-primary" style="background:#22c55e">✅ 확정</button>',
    '  </div>',
    '</div>'
  ].join('\n');
  window.showDataModal('', html);
  document.getElementById('pc-cancel-btn').addEventListener('click', function(){
    document.getElementById('sqm-modal').style.display = 'none';
  });
  document.getElementById('pc-confirm-btn').addEventListener('click', function(){
    var dateEl = document.getElementById('pc-inbound-date');
    var date   = (dateEl && dateEl.value) ? dateEl.value : '';
    var typeEl = document.querySelector('input[name="pc-type"]:checked');
    var type   = typeEl ? typeEl.value : 'DIRECT';
    // ── 검증 ──
    if (!date) {
      window.showToast && window.showToast('warning', '실제 창고 반입일을 선택하세요');
      return;
    }
    if (portDate && date < portDate) {
      if (!confirm('⚠️ 반입일이 포트 입항일(' + portDate + ')보다 이릅니다.\n계속하시겠습니까?')) return;
    }
    if (date > today) {
      if (!confirm('⚠️ 미래 날짜(' + date + ')입니다.\n계속하시겠습니까?')) return;
    }
    // ── 백엔드 호출 ──
    window.apiPost('/api/inbound/confirm/' + encodeURIComponent(lot), {
      inbound_date: date,
      inbound_type: type
    })
    .then(function(){
      window.showToast && window.showToast('success', lot + ' → AVAILABLE 입고 확정 완료');
      document.getElementById('sqm-modal').style.display = 'none';
      if (window.loadPendingPage) window.loadPendingPage();
    })
    .catch(function(e){
      window.showToast && window.showToast('error', '입고 확정 실패: ' + (e.message || String(e)));
    });
  });
};
```

### ⑥ 백엔드 안전장치 — `backend/api/inbound.py`
**위치:** `confirm_inbound()` 함수 안 (line 2244 부근)

```python
# ── 기존 (위험: 입력 없으면 오늘 날짜로 조용히 통과) ──
inbound_date = (payload.get("inbound_date") or "").strip()
if not inbound_date:
    inbound_date = datetime.now().strftime("%Y-%m-%d")

# ── 변경 후 ──
inbound_date = (payload.get("inbound_date") or "").strip()
if not inbound_date:
    raise HTTPException(400, "inbound_date 필수 — 실제 창고 반입일을 입력하세요")

# 형식·범위 검증
try:
    _d = datetime.strptime(inbound_date, "%Y-%m-%d").date()
except ValueError:
    raise HTTPException(400, f"inbound_date 형식 오류: {inbound_date} (YYYY-MM-DD)")
if _d > datetime.now().date():
    raise HTTPException(400, f"inbound_date 가 미래({inbound_date})입니다")
```

> 추가 검증으로 `port_date`보다 이른 날짜 거부도 가능하지만, 프론트엔드에서 `confirm()`으로 처리 중이라 백엔드는 미래 차단만 해도 충분.

---

## P2-4. 변경 분량 요약

| 파일 | 라인 | 비고 |
|------|------|------|
| `sqm-inventory.js` 헤더 수정 | +1 | TH 1개 |
| `sqm-inventory.js` 행 td 추가 | +6 | 작업 버튼 td |
| `sqm-inventory.js` 버튼 바인딩 | +5 | querySelectorAll |
| `sqm-inventory.js` 메뉴 함수 | +17 | showPendingActionMenu |
| `sqm-inventory.js` 모달 함수 | +65 | showPendingConfirmModal |
| `inbound.py` 검증 강화 | +6 (−2) | silently TODAY 제거 |
| **합계** | **~100줄** | Rule 5 (300줄) 안전 |

---

## P2-5. 검증 시나리오 (적용 후 smoke test)

```text
1. PyWebView 재시작 → Pending 페이지 진입
2. 행마다 우측 ⋯ 버튼 보임 → 클릭 → 메뉴 펼침 ✓
3. "✅ 입고 확정 → AVAILABLE" 클릭 → 모달 뜸 ✓
4. 날짜 비우고 확정 → 토스트 "실제 창고 반입일을 선택하세요" ✓
5. 포트 입항일보다 이른 날짜 → confirm 경고 → 취소 가능 ✓
6. 미래 날짜 → confirm 경고 → 취소 가능 ✓
7. 정상 날짜 + DIRECT → AVAILABLE 전환, Pending 목록에서 사라짐 ✓
8. 백엔드 직접 호출(curl 등) 시 date 없으면 400 에러 ✓
```

---

## P2-6. git commit (Windows CMD에서)

```bash
git add frontend/js/sqm-inventory.js backend/api/inbound.py
git commit -m "feat(pending): PENDING → AVAILABLE 입고 확정 UI + 백엔드 안전장치"
```

---

## P2-7. Part 1과의 관계

```text
Part 1 (모달 분리)과 Part 2 (Pending 입고 확정 UI)는 별개 작업.

권장 진행 순서:
  1. Part 2 먼저 (간단, 100줄, 30~45분)
  2. Part 1 (B-라이트, 3.5시간)

이유:
  - Part 2가 더 작고 위험도 낮음 → 첫 git commit으로 빠른 성공
  - Part 2가 sqm-inventory.js만 만지고, Part 1은 sqm-inline.js를 만짐
    → 충돌 없음
  - Part 2는 EXE 빌드와 무관 → 언제 해도 안전
```

---

## P2-8. 새 세션에서 추가 확인할 4가지

1. `frontend/js/sqm-inventory.js`의 `loadPendingPage()` 정확한 라인 번호 (현재 462~477 추정)
2. `window._openContextMenu` 헬퍼가 실제 존재하는지 (다른 페이지에서 사용 중인지)
3. `window.showDataModal` 헬퍼 존재 확인
4. `window.apiPost` 헬퍼 존재 확인 (또는 `apiCall` 등 다른 이름인지)

→ 위 4개 헬퍼가 없으면 P2-3 ④⑤단계 일부 수정 필요.

---

## P2-9. 한 줄 요약

> "Pending 페이지 각 행에 ⋯ 작업 버튼 추가.
>  클릭 → 메뉴 → 입고 확정 모달 → 날짜·유형 입력 → AVAILABLE 전환.
>  백엔드는 silently TODAY fallback 제거.
>  소요 30~45분."

---

**작성 완료. Part 1 + Part 2 모두 새 세션에서 처리 가능.**
