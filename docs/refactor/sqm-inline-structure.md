# sqm-inline.js 구조 측량 보고서 (Phase A)

**작성일:** 2026-05-23
**작성:** Ruby (Claude Opus 4.7)
**파일:** `frontend/js/sqm-inline.js`
**총 줄수:** 5,635줄 (wc -l 기준)
**파일 패턴:** IIFE (`(function(){ ... })();`)

> ⚠️ **Rule 5 대상**: 1000줄 초과 + IIFE → Edit 도구 금지, `scripts/patch_*.py`만 사용

---

## 1. IIFE 경계

| 위치 | 줄 | 내용 |
|---|---|---|
| 헤더 주석 | 1-5 | `/* SQM Inventory v8.6.5 - sqm-inline.js */` |
| **IIFE 시작** | **6** | `(function () {` |
| `'use strict'` | 7 | strict mode |
| 중복 실행 가드 | 8-9 | `if (window.__SQM_INLINE_INSTALLED__) return;` |
| 본문 시작 | 11 | (내부 IIFE: Tooltip) |
| 본문 끝 | 5634 | `}` (마지막 함수) |
| **IIFE 종료** | **5635** | `})();` |

🚨 **취약점**: 마지막 줄 `})();`이 깨지면 전체 IIFE 무효 — 2026-05-15 사고 원인.

---

## 2. 섹션 인덱스 (47개)

`/* ===` 패턴으로 구분된 주요 섹션.

| # | 시작줄 | 섹션 | 추정 크기 |
|---|---|---|---|
| 1 | 11 | **CUSTOM TOOLTIP SYSTEM** (내부 IIFE) | ~140줄 |
| 2 | 152 | sqmShouldOpenXlsxAfterSave / 다운로드 헬퍼 | ~110줄 |
| 3 | 265 | dbg / 디버그 패널 | ~70줄 |
| 4 | 331 | (helper) | ~25줄 |
| 5 | 355 | enableTableSort | ~35줄 |
| 6 | 395 | 컨텍스트 메뉴, escapeHtml | ~165줄 |
| 7 | 555 | 토스트 시스템 | ~80줄 |
| 8 | 635 | apiCall / apiGet / apiPost | ~65줄 |
| 9 | 698 | (helper) | ~5줄 |
| 10 | 732 | 테마 / closeAllMenus | ~40줄 |
| 11 | 767 | showPage / renderPage / loadStubPage | ~55줄 |
| 12 | 822 | 대시보드 / KPI / 상태 카드 | ~245줄 |
| 13 | 1068 | 정합성 체크 | ~340줄 |
| 14 | 1407-1415 | (helper 그룹) | ~10줄 |
| 15 | 2071 | Picked 페이지 / 페이지 시작 | ~115줄 |
| 16 | 2173 | (helper) | ~125줄 |
| 17 | 2298 | Outbound 페이지 헤더 | ~10줄 |
| 18 | 2305 | Outbound 페이지 본체 | ~105줄 |
| 19 | 2409 | Return 페이지 | ~40줄 |
| 20 | 2450 | Move 페이지 | ~60줄 |
| 21 | 2512 | Log 페이지 | ~50줄 |
| 22 | 2560 | Scan 페이지 | ~130줄 |
| 23 | 2692 | Tonbag 페이지 | ~45줄 |
| 24 | 2736 | 모달 인프라 (드래그/리사이즈/title-bar) | ~140줄 |
| 25 | 2875 | (구분) | ~5줄 |
| 26 | 2879 | OneStop Outbound 모달 핵심 | ~410줄 |
| 27 | 3295 | OneStop Outbound 모달 (Tab 2) | ~195줄 |
| 28 | 3491 | OneStop Outbound 모달 (Tab 3, scan) | ~420줄 |
| 29 | 3916-3921 | (helper) | ~10줄 |
| 30 | 4030 | DO Update 모달 | ~80줄 |
| 31 | 4109 | Apply Approved Allocation 모달 | ~55줄 |
| 32 | 4159 | (helper) | ~5줄 |
| 33 | 4288 | Quick Outbound Paste 모달 | ~110줄 |
| 34 | 4399 | Outbound Confirm 모달 | ~120줄 |
| 35 | 4520 | Approval Queue 모달 | ~30줄 |
| 36 | 4549 | Restore 모달 | ~55줄 |
| 37 | 4604 | Window Size 저장/복원 | ~25줄 |
| 38 | 4629 | Return Dialog | ~95줄 |
| 39 | 4722 | Lot Allocation Audit 모달 | ~40줄 |
| 40 | 4762 | Test DB Reset 모달 | ~55줄 |
| 41 | 4816 | (구분) | ~5줄 |
| 42 | 4822 | 알람 / 상태바 | ~220줄 |
| 43 | (5046) | (다운로드 헬퍼들) | ~110줄 |
| 44 | (5154) | dispatchAction (액션 디스패처) | ~45줄 |
| 45 | (5199) | bindAll (이벤트 바인딩) | ~135줄 |
| 46 | (5336) | refresh excel status / boot | ~90줄 |
| 47 | (5489) | Inbound Template 관리 (AI 템플릿) | ~145줄 |

---

## 3. 페이지/모듈 매핑

### 3.1 페이지 로더 (Top-level handlers)
- `loadDashboard()` / `loadKpi()` / `loadDashboardTables()` — 대시보드
- `loadInventoryPage()` — 재고
- `loadAllocationPage()` — 배정
- `loadPickedPage()` — 피킹
- `loadInboundPage()` — 입고
- `loadOutboundPage()` — 출고
- `loadReturnPage()` — 반품
- `loadMovePage()` — 이동
- `loadLogPage()` — 로그
- `loadScanPage()` — 스캔
- `loadTonbagPage()` — 톤백

### 3.2 모달들
| 모달 함수 | 줄 위치 | 추정 크기 |
|---|---|---|
| `showOneStopOutboundModal` | 2933 | ~1000줄 (가장 큼) |
| `showQuickOutboundModal` | 3767 | ~150줄 |
| `showBatchMoveApprovalModal` | 3924 | ~110줄 |
| `showDoUpdateModal` | 4033 | ~80줄 |
| `showApplyApprovedAllocationModal` | 4112 | ~55줄 |
| `showCarrierProfileModal` | 4166 | ~130줄 |
| `showQuickOutboundPasteModal` | 4291 | ~110줄 |
| `showOutboundConfirmModal` | 4402 | ~120줄 |
| `showApprovalQueueModal` | 4523 | ~30줄 |
| `showRestoreModal` | 4552 | ~55줄 |
| `showReturnDialog` | 4632 | ~95줄 |
| `showLotAllocationAuditModal` | 4725 | ~40줄 |
| `showTestDbResetModal` | 4765 | ~55줄 |
| `showTonbagModal` | 1297 (window.) | ~60줄 |

### 3.3 유틸리티 모듈 (독립성 높음)
| 기능 | 줄 위치 | 추정 크기 | 외부 의존 |
|---|---|---|---|
| **Tooltip 시스템** | 11-150 | ~140줄 | DOM만 |
| **enableTableSort** | 359-394 | ~35줄 | DOM만 |
| **dbg 패널** | 274-343 | ~70줄 | DOM만 |
| **escapeHtml** | 601 | ~5줄 | 없음 |
| **showToast** | 607-639 | ~30줄 | DOM만 |
| **apiCall / apiGet / apiPost** | 640-697 | ~60줄 | fetch |
| **컨텍스트 메뉴** | 559-600 | ~40줄 | DOM |
| **테마 시스템** | 714-735 | ~20줄 | localStorage, document.body |
| **드래그/리사이즈 모달** | 2741-2900 | ~160줄 | DOM, window |

---

## 4. window.* 글로벌 노출 (외부 API)

IIFE 안에서 `window.foo = function(...)` 으로 외부에 노출하는 핸들러들.

### 4.1 재고 (inv)
- `invApplyFilter`, `invClearFilter`, `invCopyLot`, `invCopyRow`
- `invQuickOutbound`, `invQuickReturn`, `invShowLotHistory`
- `showTonbagModal`, `_filterTonbagModal`

### 4.2 배정 (alloc)
- `_toggleAllocGroup`, `allocUploadExcel`, `allocApplyApproved`
- `allocShowApprovalQueue`, `allocWipToast`, `allocFilterBy`
- `allocToggleAll`, `allocToggleRow`, `allocCancelSelected`
- `allocPickSelected`, `allocConfirmSelected`, `allocResetAll`
- `allocCancelBySaleRef`, `allocOpenLotOverview`, `allocExportExcel`
- `allocRevertStep`, `allocResetSelected`, `allocEditCell`
- `allocContextMenu`, `toggleAllocDetail`, `cancelAllocation`

### 4.3 OneStop Outbound (oo)
- `ooSwitchTab`, `ooAddProofFiles`, `ooRemoveProofFile`
- `ooAddManualActual`, `ooInsertSample`, `ooClearPaste`, `ooParseDraft`
- `ooToggleLotExpand`, `ooToggleTonbag`, `ooSelectAllForLot`
- `ooDeselectForLot`, `ooSelectAllLots`, `ooDeselectAll`
- `ooExpandAll`, `ooRandomSelect`, `ooMoveToScan`
- `ooHandleScanFile`, `ooClearScan`, `ooAddManualScan`
- `ooRunValidation`, `ooMoveToFinalize`, `ooFinalize`, `ooViewAuditLog`

### 4.4 출고/Picked
- `togglePickedDetail`, `toggleOutboundDetail`, `executeMove`

### 4.5 기타
- `sqmSetOpenXlsxAfterSave`, `_sqmSetModalTitleBar`
- `_runIntegrityDiagnostic`, `_bmaRefresh`, `_batchMoveAction`
- `_cpSave`, `_cpEdit`, `_cpDelete`

총 **약 60개 글로벌 함수** 노출.

---

## 5. IIFE 내부 상태 변수 (실측)

### 5.1 모듈별 캡슐 상태 (해당 모듈 추출 시 같이 가야 함)
| 변수 | 줄 | 사용 모듈 | 추출 영향 |
|---|---|---|---|
| `_tip`, `_observer`, `_active`, `_showTimer` | 18, 58, 101, 102 | Tooltip | Tooltip 모듈에 동봉 — 안전 |
| `_dbgLogs`, `_dbgMax`, `_dbgEl` | 270-272 | 디버그 패널 | 디버그 모듈에 동봉 |
| `_sortObserver` | 390 | 테이블 정렬 | 테이블 정렬 모듈에 동봉 |
| `_escLastAt` | 403 | ESC 가드 | 단독 추출 시 동봉 |
| `_ctxMenu` | 558 | 컨텍스트 메뉴 | 동봉 |
| `_menuJustOpened` | 735 | 메뉴 | 동봉 |
| `_kpiTimer` | 825 | KPI 폴링 | 동봉 |
| `_scanHistory` | 2613 | 스캔 페이지 | 동봉 |
| `_pdfFile`, `_pdfB64` | 2651 | 스캔/PDF | 동봉 |
| `_tplBlFile`, `_tplDoFile`, `_tplPreviewData` | 5485-5487 | 인바운드 템플릿 | 동봉 |

### 5.2 페이지 간 공유 상태 (분리 시 위험 ↑)
| 변수 | 줄 | 영향 | 추출 시 처리 |
|---|---|---|---|
| `_currentRoute` | 770 | 라우팅 전반 | 라우터 모듈로 분리 시 export 필요 |
| `_invAllRows` | 1213 | 재고 필터 캐시 | 재고 페이지 모듈에 동봉 |
| **`_allocState`** | **1435** | 배정 페이지 다중 함수 | 배정 페이지 모듈로 함께 묶어야 함 (단일 객체 캡슐) |
| `_allocExpandedLot` | 2020 | 배정 detail toggle | 배정 페이지에 동봉 |
| `_pickedExpandedLot` | 2130 | 피킹 detail toggle | 피킹 페이지에 동봉 |
| `_inboundAllRows` | 2181 | 입고 필터 캐시 | 입고 페이지에 동봉 |
| `_outboundExpandedLot` | 2366 | 출고 detail toggle | 출고 페이지에 동봉 |
| **`_ooState`** | **2891** | OneStop 모달 거대 상태 | OneStop 모달 1000줄과 단일 묶음 (분리 매우 어려움) |

### 5.3 window.* 외부 공유 (HTML onclick 등에서 직접 조작 — 깨지면 즉시 사용자 사고)
| 노출 변수 | 사용처 | 영향 |
|---|---|---|
| `window._escModalCount`, `window._escModalTimer` | ESC 가드 (line 415-422) | IIFE 외부에서도 카운트 공유 |
| `window._allocViewMode` | **HTML onclick 인라인 코드가 직접 변경** (line 1447) | ⚠️ 외부 인터페이스 - 깨면 즉시 사고 |
| `window._sqmZ` | 모달 z-index, IIFE 외부 다른 JS와 공유 (line 2739) | 추출 시 그대로 유지 필수 |
| `window._cpEditId` | Carrier Profile 모달 (line 4235, 4245, 4260) | Carrier 모듈에 동봉 |
| `window._bmaRefresh`, `window._batchMoveAction` | Batch Move 모달 콜백 | 모달 모듈에 동봉 |
| `window._inboundFilter` | HTML onclick (line 2237) | 입고 페이지 모듈에 동봉 |
| `window._bringToFront`, `window._sqmSyncModalHeaderFromContent`, `window._makeDraggableResizable` | 모달 인프라 외부 노출 | 모달 인프라 모듈로 분리 시 export 필요 |

### 5.4 이벤트 리스너 수
- `addEventListener` + 인라인 `on*` 핸들러: **82개**
- 대부분 `boot()` 함수와 `bindAll()` 함수에 집중
- **이벤트 바인딩이 깨지면 UI 무반응** → 추출 시 boot/bindAll 함수의 호출 순서 보존 필수

---

## 6. 추출 난이도 평가

### 🟢 LOW (독립성 높음, 외부 의존 없음)
1. **Tooltip 시스템** (line 11-150) — 자체 IIFE, 추출 그대로 가능 ★★★★★
2. **enableTableSort** (line 359-394) — 함수 1개, DOM only ★★★★★
3. **escapeHtml** (line 601-605) — 순수 함수 ★★★★★
4. **dbg 패널** (line 274-343) — 자체 완결 ★★★★

### 🟡 MEDIUM (의존성 있으나 명확)
5. **showToast** — 다른 모듈에서 호출하지만 단방향 ★★★★
6. **apiCall / apiGet / apiPost** — 의존도 가장 높음 (거의 모든 모듈) ★★★
7. **컨텍스트 메뉴** — DOM 전역 의존 ★★★
8. **드래그/리사이즈 모달 인프라** — 모달 시스템 기반 ★★★

### 🔴 HIGH (큰 상태 공유, 다중 의존)
9. **페이지 로더 (loadXxxPage)** — IIFE 내부 상태 의존, 페이지 간 호출 ★★
10. **OneStop Outbound 모달** — 1000줄 단일 모달, 내부 상태 거대 ★

---

## 7. 다음 단계 (Phase B로)

이 측량 데이터를 기반으로 **분할 설계** 단계로 이동:
- 우선 추출할 슬라이스 결정
- 추출 방식 (extract 후 IIFE 유지 vs ES module 전환)
- 회귀 테스트 전략
- patch_*.py 스크립트 설계
- Codex 협업 패턴 확정

→ `sqm-inline-split-plan.md` 작성으로 이어짐.
