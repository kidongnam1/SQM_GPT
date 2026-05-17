# SQM v8.6.8 — 공통 화면 스키마 (UI Schema Standard)

> **작성일:** 2026-05-17  
> **목적:** 모든 페이지/컴포넌트가 동일한 설계 도면을 따르도록 규칙 명문화  
> **전수 검사 기준:** sqm-inventory.js / sqm-inline.js / sqm-picked.js / sqm-logistics.js / sqm-tonbag.js / sqm-allocation.js  

---

## 📌 핵심 원칙

| # | 규칙 |
|---|------|
| 1 | 색상은 **반드시 CSS 변수** `var(--xxx)` 사용 — hex 하드코딩 금지 |
| 2 | 모든 데이터 테이블은 **data-table** 클래스 사용 |
| 3 | 모든 숫자 셀은 **mono-cell** 클래스 사용 |
| 4 | 페이지 로딩/에러/빈 데이터는 **표준 3종 패턴** 준수 |
| 5 | 버튼은 **5종 표준 클래스**만 사용 |
| 6 | 새로고침은 `window.renderPage('xxx')` 통일 |

---

## 1. 색상 시스템 — CSS 변수 매핑표

> **전수 검사 결과:** sqm-inventory.js 124개, sqm-inline.js 176개, sqm-picked.js 27개 — hex 하드코딩 발견  
> **현황:** JS에서 var() 사용 vs hex 비율이 파일마다 다름 (inventory: 68/124, inline: 385/176)

### 1-A. 반드시 변수로 교체해야 할 하드코딩 목록

| 하드코딩 hex | 올바른 CSS 변수 | 용도 | 발견 횟수 |
|-------------|---------------|------|-----------|
| `#94a3b8` | `var(--text-muted)` | 보조 텍스트, # 순번, 날짜 | **83회** |
| `#3b82f6` | `var(--accent)` | LOT 번호, 강조 링크 | 32회 |
| `#22c55e` | `var(--success)` | AVAILABLE 상태, 성공 | 37회 |
| `#ef4444` | `var(--danger)` | 에러, 삭제, 위험 | 26회 |
| `#eab308` | `var(--warning)` | SAMPLE, 경고, 노란색 | 35회 |
| `#f59e0b` | `var(--warning)` | PENDING 관련, 주황 | 33회 |
| `#a855f7` | `var(--status-reserved)` | RESERVED 상태 | 8회 |
| `#555` | `var(--text-secondary)` | 비활성 텍스트 | 22회 |
| `#888` | `var(--text-muted)` | 흐린 텍스트 | 8회 |
| `#fff` | `var(--text-inverse)` | 흰색 텍스트 | 38회 |
| `#1e293b` | `var(--bg-input)` | 다크 배경 | 18회 |
| `#0f172a` | `var(--bg-root)` | 루트 배경 | 10회 |
| `#334155` | `var(--border-default)` | 테두리 | 29회 |

### 1-B. 상태별 표준 색상

```css
/* STATUS 컬러 (design-system.css 정의) */
PENDING   → var(--warning)         /* #f59e0b 계열 주황 */
AVAILABLE → var(--status-available) /* #22c55e 녹색 */
RESERVED  → var(--status-reserved)  /* #a855f7 보라 */
PICKED    → var(--status-picked)    /* #eab308 노란 */
SOLD      → var(--status-outbound)  /* #42a5f5 하늘 */
RETURN    → var(--status-return)    /* 별도 정의 */
SAMPLE    → #eab308 (임시 — 변수 추가 필요)
```

---

## 2. 데이터 테이블 표준 구조

### 2-A. 표준 HTML 골격

```html
<div style="overflow-x:auto">
  <table class="data-table">
    <thead>
      <tr>
        <!-- ① 체크박스 열 (선택 기능 있는 경우만) -->
        <th style="width:32px;text-align:center">
          <input type="checkbox" onclick="window.xxxToggleAll(this)">
        </th>
        <!-- ② 순번 열 (모든 테이블 필수) -->
        <th style="color:var(--text-muted);text-align:center;width:36px">#</th>
        <!-- ③ 데이터 열들 -->
        <th>LOT</th>
        <th>Product</th>
        ...
        <!-- ④ 액션 열 (작업 버튼 있는 경우만, 항상 마지막) -->
        <th style="width:60px"></th>
      </tr>
    </thead>
    <tbody>
      <!-- 데이터 행 -->
    </tbody>
    <tfoot>
      <tr style="background:var(--panel);font-weight:700">
        <td colspan="[체크박스+#+데이터 열 수]" style="text-align:right;padding:8px 10px">
          합계 (N LOT)
        </td>
        <td class="mono-cell" style="text-align:right">합계값</td>
        ...
      </tr>
    </tfoot>
  </table>
</div>
```

### 2-B. 테이블 컬럼별 표준 스타일

| 컬럼 종류 | `<th>` 스타일 | `<td>` 스타일 |
|-----------|--------------|--------------|
| **체크박스** | `width:32px;text-align:center` | `text-align:center` |
| **순번 (#)** | `color:var(--text-muted);text-align:center;width:36px` | `class="mono-cell" style="color:var(--text-muted);text-align:center"` |
| **LOT No** | `text-align:left` | `class="mono-cell cell-left" style="color:var(--accent);font-weight:600"` |
| **숫자/중량** | `text-align:right` | `class="mono-cell" style="text-align:right"` |
| **날짜** | — | `class="mono-cell" style="color:var(--text-muted)"` |
| **상태 뱃지** | — | `<span class="tag" style="background:rgba(xxx,0.15);color:xxx">STATUS</span>` |
| **일반 텍스트** | — | `class="mono-cell"` |
| **액션 버튼 셀** | `width:60px` | `style="white-space:nowrap;padding:6px 10px"` |

### 2-C. 테이블 클래스 규칙

```
✅ class="data-table"          ← 모든 데이터 테이블 표준
❌ class="sqm-table"           ← 사용 금지 (2곳 발견, 교체 필요)
❌ class="data-table onestop-preview-table"  ← 별도 수식어 금지
```

### 2-D. 현재 # 컬럼 width 불일치 현황 (⚠️ 수정 필요)

> **전수 검사 결과:** 32px / 36px 혼재

| 파일 | 현재 width | 표준 |
|------|-----------|------|
| sqm-inline.js (alloc sub, picked) | 32px | → **36px** 통일 필요 |
| sqm-inventory.js | 32px | → **36px** 통일 필요 |
| sqm-picked.js | 32px | → **36px** 통일 필요 |
| sqm-logistics.js, sqm-tonbag.js | 32px | → **36px** 통일 필요 |
| **표준** | **36px** | ✅ |

---

## 3. 페이지 섹션 컨테이너 표준

### 3-A. 페이지 최상위 구조

```javascript
// 표준 페이지 컨테이너
'<section style="padding:12px 16px">'
  + '<div style="display:flex;align-items:center;gap:12px;margin-bottom:8px;flex-wrap:wrap">'
    // 제목
    + '<h2 style="margin:0;font-size:16px;color:var(--accent)">🔷 페이지 제목</h2>'
    // 요약 정보
    + '<span style="font-size:12px;color:var(--text-muted)">N건 · 합계 XXX MT</span>'
    // 모드 버튼 그룹 (있는 경우)
    + '<div style="display:flex;gap:4px">' + modeButtons + '</div>'
    // 액션 버튼들
    + '<button class="btn" ...>액션</button>'
    // 새로고침 (항상 맨 오른쪽)
    + '<button class="btn btn-ghost" style="font-size:12px;margin-left:auto" '
    + 'onclick="window.renderPage(\'xxx\')">🔄 새로고침</button>'
  + '</div>'
  + '<div style="overflow-x:auto"><table class="data-table">...'
'</section>'
```

### 3-B. Toolbar gap 표준

```
✅ gap:12px   ← 페이지 상단 툴바 (섹션 헤더)
✅ gap:8px    ← 버튼 그룹 내부
✅ gap:4px    ← 모드 버튼 그룹 (LOT별/컨테이너별/입고일별)
❌ gap:6px, gap:10px  ← 사용 금지 (6곳 발견)
```

---

## 4. 버튼 표준 5종

### 4-A. 버튼 클래스 규칙

| 클래스 | 용도 | 색상 |
|--------|------|------|
| `btn btn-primary` | 주요 액션 (저장, 확정) | `var(--accent)` 파란색 배경 |
| `btn btn-secondary` | 보조 액션 (취소, 되돌리기) | 회색 배경 |
| `btn btn-ghost` | 새로고침, 소프트 액션 | 투명 배경 |
| `btn btn-ghost btn-xs` | 행 내 인라인 소형 버튼 | 투명 소형 |
| `btn btn-danger` | 삭제, 위험 액션 | `var(--danger)` 빨간색 |

### 4-B. 현재 비표준 클래스 (⚠️ 교체 필요)

```
❌ btn btn-sm        → btn btn-ghost btn-xs 로 교체
❌ btn btn-wip       → 제거 또는 btn btn-secondary 로 교체
❌ btn btn-warning   → 인라인 style로 var(--warning) 표현
❌ btn tpl-edit-btn  → 커스텀 클래스 금지, 표준 5종만
```

### 4-C. 모드 버튼 (뷰 전환) 표준 패턴

```javascript
// 표준 모드 버튼 헬퍼 (각 JS 파일에 동일하게 적용)
function _xxxModeBtn(val, label) {
  var cur = window._xxxViewMode || 'lot';
  var active = val === cur
    ? 'background:var(--accent);color:#fff;border-color:var(--accent);'
    : 'background:var(--bg-input);color:var(--text-muted);border-color:var(--border-default);';
  return '<button class="btn" style="font-size:12px;padding:4px 10px;' + active + '" '
    + 'onclick="window._xxxViewMode=\'' + val + '\';window.renderPage(\'xxx\')">' + label + '</button>';
}
// 사용
_xxxModeBtn('lot', 'LOT별') + _xxxModeBtn('container', '컨테이너별') + _xxxModeBtn('date', '입고일별')
```

---

## 5. 로딩 / 빈 데이터 / 에러 표준 3종 패턴

### 5-A. 로딩 중 (페이지 최초 진입)

```javascript
// ✅ 표준 로딩 메시지
c.innerHTML = '<div class="loading-spinner" style="padding:40px;text-align:center;color:var(--text-muted)">⏳ XXX 로딩 중...</div>';

// ❌ 비표준 (사용 금지)
// "⏳ 로딩..."  ← 말줄임표 X
// "⏳ Loading..."  ← 영어 X
// "⏳ 로딩..."  ← class 없음 X
```

> **전수 검사 발견 비표준:** `로딩...` / `Loading...` / `로딩 중...` / `데이터 로딩 중...` — 12가지 표현 혼재

### 5-B. 빈 데이터

```javascript
// ✅ 표준 빈 데이터 메시지
c.innerHTML = '<div class="empty" style="padding:60px;text-align:center;color:var(--text-muted)">📭 XXX 데이터 없음</div>';

// ❌ 비표준 (사용 금지)
// padding:12px   ← 너무 작음
// padding:40px   ← 비표준
// 영어 "No xxx data"   ← 한국어 통일
// color 없는 경우      ← 항상 var(--text-muted)
```

> **전수 검사 발견:** `No logs` / `No return data` / `No tonbag data` — 영어 빈 데이터 3곳

### 5-C. 에러

```javascript
// ✅ 표준 에러 메시지
c.innerHTML = '<div class="empty" style="padding:60px;text-align:center;color:var(--danger)">❌ XXX 조회 실패: ' + escapeHtml(e.message || String(e)) + '</div>';
showToast('error', 'XXX 조회 실패');

// ❌ 비표준
// color:var(--danger) 없는 에러   ← 색상 누락
// "Load failed:"  ← 영어 X
```

---

## 6. Toast 알림 표준

### 6-A. 타입 4종

```javascript
showToast('success', '✅ 작업 완료 메시지');
showToast('error',   '❌ 실패 원인: ' + e.message);
showToast('warning', '⚠️ 경고 메시지');
showToast('info',    'ℹ️ 정보 메시지');

// ❌ 'warn'  ← 비표준 (현재 3곳 사용중, 'warning'으로 교체)
```

### 6-B. 메시지 규칙

```
✅ 한국어 우선
✅ 성공: '↩️ 3건 → PENDING 복구 완료'
✅ 에러: 'XXX 실패: ' + e.message  (원인 포함)
❌ 'Move (coming soon)'  ← 미구현 placeholder 토스트 금지
❌ 'Scan (coming soon)'  ← 동일
```

---

## 7. 모달 표준

### 7-A. 현황 (⚠️ 가장 심각한 불일치)

> **전수 검사:** sqm-inline.js에만 90개+ `sqm-modal` 사용, 다른 파일들은 모달 없거나 2개 이하

**모달이 필요한 파일별 현황:**

| 파일 | sqm-modal 사용 | 상태 |
|------|---------------|------|
| sqm-inline.js | 90개+ | ✅ 표준 사용 |
| sqm-logistics.js | 2개 | ⚠️ 부분 사용 |
| sqm-inventory.js | 0개 | ❌ confirm() 브라우저 기본 사용 |
| sqm-picked.js | 0개 | ❌ confirm() 브라우저 기본 사용 |
| sqm-tonbag.js | 0개 | ❌ confirm() 브라우저 기본 사용 |

### 7-B. 표준 모달 패턴

```javascript
// ✅ 표준 확인 모달 (브라우저 confirm() 금지)
var overlay = document.createElement('div');
overlay.className = 'sqm-modal';
overlay.innerHTML = `
  <div class="sqm-modal-box">
    <h3 style="margin:0 0 8px;font-size:15px">🔔 제목</h3>
    <p style="font-size:13px;color:var(--text-muted)">설명 내용</p>
    <div style="display:flex;gap:8px;justify-content:flex-end;margin-top:16px">
      <button class="btn btn-secondary" onclick="this.closest('.sqm-modal').remove()">취소</button>
      <button class="btn btn-primary" onclick="doAction(); this.closest('.sqm-modal').remove()">확인</button>
    </div>
  </div>`;
document.body.appendChild(overlay);

// ❌ 금지
// if (!confirm('...'))  ← 현재 47곳 사용 중 (전체 교체 필요)
// window.confirm(...)
```

> **전수 검사 발견:** `if (!confirm(...)` 총 47곳 — inventory(4), inline(25), picked(1), logistics(1), tonbag(16)

---

## 8. 에러 핸들링 표준

### 8-A. apiGet/apiPost catch 표준 패턴

```javascript
// ✅ 페이지 로드 에러
apiGet('/api/xxx').then(function(res) {
  // 성공 처리
}).catch(function(e) {
  if (window.getCurrentRoute() !== route) return;  // 이미 이탈한 경우 무시
  c.innerHTML = '<div class="empty" style="padding:60px;text-align:center;color:var(--danger)">❌ XXX 조회 실패: ' + escapeHtml(e.message || String(e)) + '</div>';
  showToast('error', 'XXX 조회 실패');
});

// ✅ 액션 에러
apiPost('/api/xxx', data).then(function(res) {
  showToast('success', '✅ 완료');
  window.renderPage('xxx');
}).catch(function(e) {
  showToast('error', '실패: ' + (e.message || String(e)));
});
```

> **전수 검사:** catch 구조가 파일마다 다름 — inventory(14), inline(124), picked(2), logistics(13), tonbag(74)

---

## 9. 새로고침 버튼 표준

```javascript
// ✅ 표준 (모든 파일 통일)
'<button class="btn btn-ghost" style="font-size:12px;margin-left:auto" '
+ 'onclick="window.renderPage(\'xxx\')">🔄 새로고침</button>'

// ❌ 비표준 (교체 필요)
// onclick="renderPage('xxx')"          ← window. 없는 직접 호출 (P2-1 이후 오류 가능)
// onclick="window.loadXxxPage()"       ← loadPage 직접 호출 (renderPage 통해야 함)
// onclick="window._bmaRefresh()"       ← 커스텀 함수 (renderPage 래핑 권장)
```

---

## 10. 행 인덱스(순번) 표준

```javascript
// ✅ 표준 — map/forEach 인덱스 사용
rows.map(function(r, _i) {
  return '<tr>'
    + '<td class="mono-cell" style="color:var(--text-muted);text-align:center">' + (_i+1) + '</td>'
    + ...
}).join('');

rows.forEach(function(r, _i) {
  html += '<tr>'
    + '<td class="mono-cell" style="color:var(--text-muted);text-align:center">' + (_i+1) + '</td>'
    + ...
});

// ❌ 금지 (외부 카운터 변수 사용)
// var idx = 0;
// rows.forEach(function(r) { html += '<td>' + (++idx) + '</td>'; });
```

---

## 11. 공통 스키마가 필요한 추가 영역 (전수 검사 결과)

### 🔴 긴급 (기능 영향)

| 항목 | 현황 | 권고 |
|------|------|------|
| **모달 표준화** | 47곳 브라우저 confirm() 사용 | sqm-modal 교체 |
| **showToast 'warn'** | 3곳 비표준 타입 사용 | 'warning'으로 교체 |
| **sqm-table 클래스** | 2곳 비표준 테이블 | data-table 교체 |
| **renderPage 직접 호출** | sqm-inline 내부 다수 | window.renderPage() 통일 |

### 🟡 중요 (UI 일관성)

| 항목 | 현황 | 권고 |
|------|------|------|
| **# 컬럼 width** | 32px/36px 혼재 (5개 파일) | 36px 통일 |
| **빈 데이터 영어** | No logs, No return data, No tonbag data (3곳) | 한국어 통일 |
| **로딩 텍스트** | 12가지 표현 혼재 | `⏳ XXX 로딩 중...` 통일 |
| **툴바 gap** | 6px/8px/10px/12px 혼재 | 12px/8px/4px 3단계만 |
| **에러 핸들링** | catch 패턴 파일마다 다름 | 표준 패턴 적용 |

### 🟢 장기 (코드 품질)

| 항목 | 현황 | 권고 |
|------|------|------|
| **색상 하드코딩** | hex 총 438건 (5개 파일) | CSS 변수 전환 |
| **인라인 스타일** | 모든 스타일이 JS 내 인라인 | CSS 클래스 추출 |
| **에러 메시지** | 한국어/영어 혼재 | 한국어 통일 |
| **섹션 padding** | 12px 16px (대체로 통일) | 유지 |

---

## 12. 파일별 스키마 준수 현황 점수표

| 파일 | 색상변수 | 테이블 | 모달 | 로딩패턴 | 에러처리 | 종합 |
|------|---------|--------|------|---------|---------|------|
| sqm-inventory.js | 🟡 (68/124) | ✅ | ❌ | 🟡 | 🟡 | **C+** |
| sqm-inline.js | 🟡 (385/176) | ✅ | ✅ | 🟡 | 🟡 | **B** |
| sqm-picked.js | ❌ (17/27) | ✅ | ❌ | ❌ | ❌ | **D** |
| sqm-logistics.js | 🟡 (52/42) | ✅ | 🟡 | 🟡 | 🟡 | **C** |
| sqm-tonbag.js | 🟡 (300/69) | ✅ | ❌ | 🟡 | 🟡 | **C+** |

> 색상변수 점수 기준: ✅ var() > 90% / 🟡 50~90% / ❌ < 50%

---

## 13. 신규 화면 제작 체크리스트

새 페이지/컴포넌트 만들 때 반드시 확인:

```
[ ] 테이블 class="data-table" 사용했는가?
[ ] 첫 번째 열: 체크박스 (선택 기능 필요시)
[ ] 두 번째 열: # 순번 width:36px, var(--text-muted)
[ ] 모든 숫자 셀: class="mono-cell"
[ ] LOT 셀: color:var(--accent), font-weight:600
[ ] 로딩 메시지: class="loading-spinner" + "⏳ XXX 로딩 중..."
[ ] 빈 데이터: class="empty", padding:60px, var(--text-muted), 한국어
[ ] 에러: class="empty", var(--danger), showToast('error', ...)
[ ] 버튼: 표준 5종 클래스만
[ ] 새로고침: window.renderPage('xxx')
[ ] 색상: var(--xxx) CSS 변수만 (hex 금지)
[ ] 모달: sqm-modal 사용 (confirm() 금지)
[ ] tfoot: colspan 정확히 (체크박스+#+열수 합산)
```

---

*최종 갱신: 2026-05-17 | Ruby (루비) 작성*
