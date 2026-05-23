# SQM 폴더 비교 보고서

- 비교 일자: 2026-05-17
- 기준 후보 A: `D:\program\SQM_inventory\SQM_v868_claan`
- 기준 후보 B: `D:\program\SQM_inventory\sqm_v869_clean`
- 비교 방식: `.git`, `node_modules`, `__pycache__`, pytest 캐시를 제외한 뒤 전체 파일 해시 비교 + 핵심 변경 파일 수동 검토

## 최종 판단

앞으로는 **`sqm_v869_clean`을 기준 폴더로 사용하는 것이 맞다.**

이유:

1. 실행 문서가 `run_v869_clean.bat`을 **단일 정식 실행기(canonical launcher)** 로 명시한다.
2. `run.bat`, `실행.bat`도 모두 `run_v869_clean.bat`을 호출하도록 바뀌어 실행 기준이 일원화됐다.
3. 프론트엔드가 대형 단일 파일에서 여러 모듈로 분리되어 유지보수성이 개선됐다.
4. 반품, 배정 되돌리기, Allocation 엑셀 파싱 등 실제 업무 흐름의 안정화 수정이 들어갔다.
5. 회귀 테스트와 smoke 검증이 강화되어 최신 작업본의 성격이 더 분명하다.

`SQM_v868_claan`은 이전 작업본에 가깝고, 임시 파일·백업 파일·쉘 찌꺼기 파일이 더 많이 남아 있다.

## 전체 비교 요약

| 항목 | 수치 |
|---|---:|
| `sqm_v869_clean` 파일 수 | 4,770 |
| `SQM_v868_claan` 파일 수 | 4,764 |
| 동일 파일 | 4,719 |
| `sqm_v869_clean` 전용 파일 | 25 |
| `SQM_v868_claan` 전용 파일 | 19 |
| 공통 파일 중 변경 파일 | 26 |

## 실제 기능 차이만 요약

| 영역 | `SQM_v868_claan` | `sqm_v869_clean` | 실제 영향 |
|---|---|---|---|
| 실행 방식 | `run.bat` / `실행.bat`가 직접 `main_webview.py` 실행 | `run_v869_clean.bat`이 정식 실행기, 다른 실행 파일은 이를 호출 | 잘못된 복사본에서 실행되는 위험 감소 |
| 프론트 구조 | `sqm-inline.js` 중심의 거대한 단일 구조 | 업로드/상품/도구/보조 모달/설정/무게 패널 모듈 분리 | 유지보수와 회귀 추적이 쉬워짐 |
| 반품 처리 | 반품 이력만 쌓이고 상태 불일치 가능 | `inventory`, `inventory_tonbag` 상태를 `RETURN`으로 갱신 | 반품 탭 미노출 같은 정합성 문제 방지 |
| Allocation 엑셀 파싱 | alias 실패 시 AI fallback 중심 | alias → 정본 `AllocationParser` → AI fallback | 고객사별 양식 파싱 안정성 향상 |
| 단계 되돌리기 | 전역 되돌리기 중심 | 특정 `lot_nos`만 선택 되돌리기 가능 | 실수 범위 축소, 안전한 복구 가능 |
| Picked 목록 | `inbound_date` 없음 | `inbound_date` 포함 | 피킹 화면에서 입고일 확인 가능 |
| Move 화면 | 톤백 바코드 입력 | LOT No 입력 | 이동 흐름이 LOT 기준으로 정리 |
| 프론트 API 기준 | API 주소가 고정값 위주 | `window.SQM_API_BASE` 또는 현재 origin 사용 | 실행 환경 유연성 증가 |
| UI 메시지 타입 | 일부 `warn` 사용 | `warning`으로 정리 | 토스트 표현 일관성 개선 |
| 테스트 | 기본 탭/500 검사 위주 | 자산 버전, 분리 모듈 로드, 모달 오픈, Move 입력, 회귀 테스트 추가 | 최신본 검증 강도 증가 |

## 신규 파일 (`sqm_v869_clean`에만 존재)

### 기능/구조 관련
- `run_v869_clean.bat`
- `frontend/js/sqm-aux-modals.js`
- `frontend/js/sqm-product-modals.js`
- `frontend/js/sqm-settings-templates.js`
- `frontend/js/sqm-tools-modals.js`
- `frontend/js/sqm-upload-modals.js`
- `frontend/js/sqm-weight-panel.js`
- `tests/test_status_transition_contract.py`
- `tests/test_v869_stability_regressions.py`

### 검증 산출물
- `REPORTS/phase5_verify_20260517_*.json`
- `REPORTS/phase5_verify_20260517_*.md`
- `REPORTS/playwright_ui_smoke.json`
- `test-results/.../error-context.md`
- `v869_uvicorn_8766.err.log`
- `v869_uvicorn_8766.out.log`

## 이전 폴더에만 남아 있는 파일 (`SQM_v868_claan` 전용)

### 이전 작업 흔적
- `frontend/js/sqm-inventory.js.bak_pendingbtn`
- `frontend/js/sqm-inventory.js.bak_pendingempty`
- `scripts/fix_template_duplicates.py`
- `scripts/patch_fix_pending_btn.py`
- `scripts/patch_pending_empty.py`

### 임시/찌꺼기 파일
- `bin`, `cd`, `dir`, `echo`, `node`, `npm`, `rmdir`, `type`
- `list.txt`, `out.txt`, `test_out.txt`, `지정된`
- `~$M_PATCH_FINAL_REPORT_2026-05-06.md`
- `~$M_UI_Schema_Plan.docx`

## 변경 파일 전체 목록

### 루트
- `.gitignore`
- `HOW_TO_RUN.md`
- `package-lock.json`
- `package.json`
- `run.bat`
- `sqm_debug.log`
- `실행.bat`

### 백엔드
- `backend/api/actions3.py`
- `backend/api/allocation_api.py`
- `backend/api/queries.py`

### 데이터
- `data/db/sqm_inventory.db`
- `data/db/sqm_inventory.db-shm`
- `data/db/sqm_inventory.db-wal`

### 프론트엔드
- `frontend/index.html`
- `frontend/js/sqm-allocation.js`
- `frontend/js/sqm-core.js`
- `frontend/js/sqm-inline.js`
- `frontend/js/sqm-inventory.js`
- `frontend/js/sqm-logistics.js`
- `frontend/js/sqm-onestop-inbound.js`
- `frontend/js/sqm-picked.js`
- `frontend/js/sqm-tonbag.js`

### 테스트/로그
- `logs/sqm_inventory.log`
- `scripts/test_all_menus_playwright.py`
- `test-results/.last-run.json`
- `tests/sqm_regression.spec.js`

## 파일별 핵심 diff 요약

| 파일 | 핵심 변화 |
|---|---|
| `HOW_TO_RUN.md` | `run_v869_clean.bat`을 canonical launcher로 지정 |
| `run.bat`, `실행.bat` | 직접 실행 대신 `run_v869_clean.bat` 호출 |
| `frontend/index.html` | 신규 분리 모듈 6개 로드, JS 자산 버전 갱신 |
| `frontend/js/sqm-inline.js` | 약 2천 줄 감소, 모달/설정/무게 패널 코드 분리 |
| `backend/api/actions3.py` | 반품 시 실제 재고/톤백 상태를 `RETURN`으로 동기화 |
| `backend/api/allocation_api.py` | 정본 AllocationParser fallback, 선택 LOT 되돌리기, 필드 확장 |
| `backend/api/queries.py` | picked 목록에 `inbound_date` 추가 |
| `frontend/js/sqm-logistics.js` | SOLD→PICKED 선택 복구, Move 입력을 LOT 기준으로 전환 |
| `frontend/js/sqm-inventory.js` | inline onclick 인자 인코딩 안전성 개선, 빈 화면 스타일 단순화 |
| `frontend/js/sqm-allocation.js` | 중복 액션 제거, 경고 토스트 타입 정리 |
| `scripts/test_all_menus_playwright.py` | 전수 클릭형 검사에서 핵심 smoke 검증형으로 전환 |
| `tests/sqm_regression.spec.js` | 자산 버전/분리 모듈/모달/Move 회귀 검사 추가 |
| `.gitignore` | 테스트 결과와 phase5 report 산출물 무시 규칙 추가 |

## 핵심 코드 변화 상세

### 1. 실행 진입점 통일

이전 폴더는 `run.bat`와 `실행.bat`가 각각 직접 `python main_webview.py`를 실행했다. 새 폴더는 이 둘이 모두 `run_v869_clean.bat`으로 위임한다.

효과:
- 실제 실행 루트가 한 곳으로 고정된다.
- 오래된 복사본에서 구버전 자산을 잘못 서빙하는 문제를 줄인다.

### 2. 프론트엔드 모듈 분리

`frontend/js/sqm-inline.js`가 7,635줄에서 5,615줄로 줄었고, 아래 파일들이 새로 생겼다.

- `sqm-upload-modals.js`
- `sqm-aux-modals.js`
- `sqm-tools-modals.js`
- `sqm-product-modals.js`
- `sqm-settings-templates.js`
- `sqm-weight-panel.js`

효과:
- 파일 하나에 몰린 책임을 줄였다.
- 이후 수정 시 영향 범위 파악이 쉬워졌다.
- 새 회귀 테스트가 분리 모듈 로드 여부를 직접 검사한다.

### 3. 반품 상태 정합성 보강

`actions3.return_create()`는 이제 이력만 남기지 않고, 반품 대상 LOT와 톤백의 상태도 `RETURN`으로 변경한다.

효과:
- `return_history`에는 있는데 실제 화면에는 반품으로 안 보이는 불일치 가능성을 줄인다.

### 4. Allocation 파싱 안정화

`allocation_api.py`는 alias 매핑이 실패했을 때 곧바로 AI에 넘기지 않고, 기존 강한 파서인 `AllocationParser`를 먼저 사용한다.

처리 순서:
1. 일반 alias 매핑
2. 정본 `AllocationParser`
3. Gemini AI fallback

효과:
- Song/Jakarta/Woo 같은 이미 잘 지원하던 양식은 AI 없이도 더 안정적으로 처리한다.
- 파싱 실패율과 AI 의존도를 낮춘다.

### 5. 선택 LOT만 되돌리기

`revert-step` API가 `lot_nos`를 받는다. 프론트에서도 특정 출고 완료 LOT만 `SOLD → PICKED`로 되돌릴 수 있게 바뀌었다.

효과:
- 전체 배정을 건드리지 않고 문제 건만 복구 가능하다.
- 운영 실수의 폭을 줄인다.

### 6. Move 화면 기준 변경

이전에는 톤백 바코드를 입력받았고, 새 버전은 `LOT No`를 입력받는다. 호출 API도 `/api/action2/inventory-move`로 바뀌었다.

효과:
- 현재 구현된 백엔드 흐름과 프론트 입력 기준을 맞춘 것으로 보인다.

### 7. 테스트 전략 변경

기존 smoke 스크립트는 메뉴 전체를 광범위하게 눌렀다. 새 버전은 릴리스 직전 빠르게 돌릴 수 있는 핵심 검증으로 바뀌었다.

검사 예:
- 올바른 JS 자산 버전 로드
- 핵심 탭 렌더링
- 분리 모듈 전역 함수 존재
- 모달 실제 오픈
- 500 응답 없음

효과:
- 속도와 신뢰성의 균형이 좋아졌다.

## DB 차이

두 폴더의 DB 스키마는 동일하다.

- 테이블 수: 둘 다 37개
- 주요 테이블 구조: 동일

다만 데이터는 완전히 같지 않다.

| 테이블 | `SQM_v868_claan` | `sqm_v869_clean` |
|---|---:|---:|
| `inbound_template` | 14 | 13 |

WAL 파일 크기도 다르므로, 두 폴더는 코드뿐 아니라 현재 데이터 상태도 완전한 복제본은 아니다.

## 권장 운영 원칙

1. 앞으로 개발·실행 기준은 `sqm_v869_clean`으로 통일한다.
2. `SQM_v868_claan`은 당장 삭제하지 말고, 한동안 **비교용 백업/참조본**으로만 보관한다.
3. 새 작업은 `run_v869_clean.bat`으로 실행해 확인한다.
4. DB 데이터를 기준본으로 합치기 전에는 두 폴더를 번갈아 실행하지 않는다.

## 최종 한 줄 요약

`SQM_v868_claan`은 이전 작업본, `sqm_v869_clean`은 **정리·안정화가 반영된 최신 기준본**이다.
