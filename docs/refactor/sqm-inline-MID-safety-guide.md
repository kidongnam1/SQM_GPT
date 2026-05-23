# sqm-inline.js MID 위험 슬라이스 안전 가이드 (S5-S8)

**작성일:** 2026-05-23
**적용 대상:** Phase B-S5, S6, S7, S8 (🟡 MID 위험)
**전제 조건:** S1-S4 (🟢 LOW) 완료 — sqm-inline.js 현재 5,392줄

> ⚠️ **이 문서를 다음 세션 시작 시 반드시 먼저 읽으세요.**
> LOW 단계와 본질이 다릅니다. 묶음 처리 금지, 단독 commit, Codex 의무 검토.

---

## 1. 핵심 원칙 4가지

### 1.1 묶음 금지 — 한 번에 한 슬라이스
LOW(S1-S4)는 4개 묶어서 안전했지만, MID는 다릅니다.
- **사고 시 영향 격리** — 한 슬라이스가 깨져도 다른 슬라이스 무관
- **단일 `git revert` 로 깔끔 롤백**
- **디버깅 변수 최소화** — 무엇이 깨졌는지 즉시 식별

→ S5, S6, S7, S8 각각 **단독 commit** + 단독 push.

### 1.2 사전 의존성 측량 강화
각 슬라이스 시작 전, 별도 측량 문서 의무 작성:
```
docs/refactor/sqm-inline-S5-deps.md
docs/refactor/sqm-inline-S6-deps.md
docs/refactor/sqm-inline-S7-deps.md
docs/refactor/sqm-inline-S8-deps.md
```

각 문서에 포함:
- 추출 대상 함수가 **사용하는** 외부 변수/함수 (스코프 탈출 확인)
- 추출 대상 함수가 **어디서 호출되는지** (grep count + 위치)
- IIFE 외부와 공유되는 상태 (`_zFloatTop`, `localStorage` 키 등)
- 외부에서 직접 조작하는 `window.*` 변수
- HTML 인라인 onclick에서의 참조 여부

### 1.3 Codex 이중 검토 의무화
S1-S4와 달리 MID는 **Codex가 패치 스크립트도 리뷰**:

| 시점 | Codex 역할 |
|---|---|
| 의존성 측량 후 | "내가 빠뜨린 의존 있는지?" 검토 |
| 패치 스크립트 작성 후 | "이 스크립트가 깨뜨릴 가능성?" 검토 |
| 적용 후 | "결과 코드에 문제 있는지?" 검토 |
| 의심점 발견 | 즉시 rollback |

### 1.4 Playwright 회귀 자동화
앱 실행 + 수동 확인을 넘어, **각 슬라이스에 회귀 spec 추가**:
- `tests/sqm-S5-download.spec.js` — 엑셀 저장/열기
- `tests/sqm-S6-toast-api.spec.js` — 토스트 + API 호출
- `tests/sqm-S7-context-esc.spec.js` — 우클릭 메뉴 + ESC
- `tests/sqm-S8-modal-drag.spec.js` — 모달 드래그/리사이즈

---

## 2. 슬라이스별 위험 + 대응

### S5 — 다운로드 헬퍼

**대상 함수**: `sqmShouldOpenXlsxAfterSave`, `sqmSuggestedXlsxName`, `sqmDownloadFileUrl`, `window.sqmSetOpenXlsxAfterSave`
**예상 위치**: 현재 line 16-115 정도 (S1-S4 후)

| 위험 | 대응 |
|---|---|
| `localStorage` 의존 (`sqm_open_xlsx_after_save` 키) | 추출 후 새 모듈에서 동일 키 사용. **키 이름 변경 금지** |
| PyWebView 네이티브 다운로드 호출 (`window.pywebview.api.*`) | 외부 API 인터페이스 그대로 유지 — 변경 금지 |
| `window.sqmSetOpenXlsxAfterSave` 외부 노출 (HTML 인라인 onclick 가능) | 노출 유지 |
| `apiCall`/`apiGet` 사용 (S6와 의존성) | S6 추출 후라면 window.apiCall 폴백, 그 전이면 단순 |

**사고 시나리오**:
- 엑셀 저장 안 됨
- 설정 토글 무반응
- 파일명 자동 생성 실패

**검증 시나리오**:
- Excel 저장 → 옵션 ON/OFF 토글
- 저장 후 자동 열림 여부 (Windows 기본 앱)
- 파일명 형식 확인

### S6 — 토스트 + API 헬퍼

**대상**: `ensureToastContainer`, `showToast`, `apiCall`, `apiGet`, `apiPost`, `attempt` (재시도 로직)
**예상 위치**: 현재 line 290-440 정도

| 위험 | 대응 |
|---|---|
| `showToast` 사용처 100+회 | **window.showToast 노출 필수** |
| `apiCall/apiGet/apiPost` 의존도 최고 | **반드시 단독 슬라이스** + window 노출 |
| **추천: S6을 S6a (토스트만) + S6b (API만)으로 분리** | 두 단독 commit |
| fetch 의존 — 백엔드 5초 timeout 동작 | retry 로직 (현재 line 655-697 부근) 변경 없이 추출 |
| 토스트 컨테이너 DOM (`#toast-container`) | DOM ID 유지 |

**사고 시나리오 — 최악**:
- API 추출 실패 → **모든 API 호출 실패** → 앱 사실상 사망
- 즉시 rollback 필수

**검증 시나리오**:
- 토스트 표시 (success/error/warning 3종)
- API GET (예: 재고 조회)
- API POST (예: 출고 처리)
- 네트워크 끊김 시 retry 확인 (개발자 도구로 Network 차단)

→ **이 슬라이스는 S6a, S6b 2개 세션 권장**

### S7 — 컨텍스트 메뉴 + ESC 가드

**대상**: `showContextMenu`, `hideContextMenu`, ESC 키 글로벌 핸들러
**예상 위치**: 현재 line 150-300 정도

| 위험 | 대응 |
|---|---|
| `window._escModalCount`, `window._escModalTimer` IIFE 외부 공유 | **노출 그대로 유지** — 다른 JS 파일도 사용 가능 |
| `showContextMenu` 호출 — `dispatchAction` 등에서 부름 | `window.showContextMenu` 노출 |
| ESC 키 글로벌 핸들러 — 우선순위 로직 (컨텍스트 메뉴 → 모달 → 메뉴 드롭다운) | 변경 없이 추출 |
| `_ctxMenu` 내부 상태 | 새 모듈 IIFE 안에 동봉 |

**사고 시나리오**:
- 우클릭 메뉴 안 뜸
- ESC가 잘못된 우선순위로 닫힘 (예: 메뉴는 안 닫고 모달 닫음)
- 키보드 입력 중 ESC가 모달 닫음 (입력 차단 깨짐)

**검증 시나리오**:
- 우클릭 → 컨텍스트 메뉴 표시 → 메뉴 외 클릭 시 사라짐
- 모달 열림 → ESC → 모달 닫힘
- 모달 안 입력 필드 포커스 → ESC → 모달 닫힘 (의도된 동작)

### S8 — 모달 인프라 (드래그/리사이즈)

**대상**: `_bringToFront`, `_makeDraggableResizable`, `_sqmExtractModalHeadingText`, `_sqmSyncModalHeaderFromContent`, `_sqmSetModalTitleBar`, `ensureModal`, `showDataModal`
**예상 위치**: 현재 line 2500-2700 정도

| 위험 | 대응 |
|---|---|
| **`window._sqmZ` IIFE 외부 공유** (다른 JS 파일도 사용) | **절대 변경 금지**, 그대로 유지 |
| `_makeDraggableResizable` 외부 노출 (`window._makeDraggableResizable`) | 새 모듈에서 동일 노출 |
| 페이지 모달들 (OneStop, Carrier, BatchMove 등) 가 의존 | 인터페이스 보존 |
| `_zFloatTop` 내부 상태 | 새 모듈에 동봉 |

**사고 시나리오**:
- 모달 드래그 안 됨
- 리사이즈 핸들 동작 안 함
- z-index 꼬임 (새 모달이 이전 모달 뒤로 숨음)
- 모달 타이틀 동기화 안 됨

**검증 시나리오**:
- 모달 열기 → 드래그 → 위치 이동 확인
- 모달 리사이즈 코너 드래그 → 크기 변경
- 모달 2개 동시 열기 → 클릭으로 z-index 전환
- 모달 닫기 → 다시 열기 (저장된 크기 복원)

---

## 3. 표준 안전 절차 (17단계 체크리스트)

LOW의 13단계에서 **4단계 추가**:

```
1. ☐ 의존성 측량 문서 작성 (sqm-inline-S<N>-deps.md)          [NEW]
2. ☐ 측량 문서를 Codex가 검토 + 빠진 의존 지적                 [NEW]
3. ☐ patch_*.py 작성
4. ☐ Codex가 patch 스크립트 리뷰 (3가지 안전장치 검증)         [강화]
5. ☐ dry-run 통과
6. ☐ 백업 자동 생성 (bak_S<N>_YYYYMMDD_HHMMSS)
7. ☐ 실제 적용
8. ☐ node --check 양 파일 통과
9. ☐ outer IIFE 닫힘 확인 (tail -1 = `})();`)
10. ☐ 줄수 검증 (사후 == 사전 - 추출줄수 - 잔재줄수)
11. ☐ window.* 노출 잔재 grep (0건)                             [강화]
12. ☐ index.html 로딩 순서 확인
13. ☐ 앱 실행 → 수동 기능 테스트
14. ☐ F12 콘솔 에러 0건 확인                                    [강화]
15. ☐ Playwright 회귀 통과 (해당 슬라이스용 spec 추가)          [강화]
16. ☐ git commit (단독, 다른 슬라이스와 묶지 않음)
17. ☐ Codex 사후 코드 리뷰                                      [NEW]
```

---

## 4. 다음 세션 시작 시 권장 순서

### 첫 5분 — 컨텍스트 복원
1. `CLAUDE.md` 읽기 (특히 Rule 5)
2. `docs/refactor/sqm-inline-structure.md` (Phase A 측량)
3. `docs/refactor/sqm-inline-split-plan.md` (Phase B 설계)
4. **이 문서** (MID 가이드)

### 다음 30-60분 — 의존성 측량
1. **현재 sqm-inline.js (5,392줄)** 상태 확인 (`wc -l`, `tail -1`)
2. S5 대상 함수 위치 grep (`sqmShouldOpenXlsxAfterSave`, `sqmDownloadFileUrl` 등)
3. `docs/refactor/sqm-inline-S5-deps.md` 작성:
   - 호출처 매핑 (grep + count)
   - localStorage 키 인덱스
   - PyWebView API 의존 목록
   - window.* 노출 인터페이스
4. **Codex 검토 요청** — 측량 문서 검토 + 빠진 의존 지적

### 다음 30-60분 — patch 스크립트
1. `scripts/patch_split_download_S5.py` 작성
2. **Codex 검토 요청** — 스크립트 안전장치 검증
3. dry-run → 실제 적용 → 자동 검증 → 사용자 검증 → commit + push

### 한 슬라이스 후 — 강제 휴식
1. 통과 후 다음 슬라이스로 넘어가기 전 **30분 휴식 권장**
2. 컨텍스트 누적으로 인한 실수 방지
3. 또는 다음 세션으로 미루기

---

## 5. 일정 가이드

| 슬라이스 | 측량 | 스크립트 | 적용+검증 | 한 슬라이스 총 |
|---|---|---|---|---|
| S5 다운로드 | 30분 | 1시간 | 1시간 | **2.5시간** |
| S6a 토스트만 | 20분 | 30분 | 30분 | **1.5시간** |
| S6b API만 | 1시간 | 2시간 | 1시간 | **4시간** (최위험) |
| S7 컨텍스트 | 30분 | 1시간 | 1시간 | **2.5시간** |
| S8 모달 인프라 | 1시간 | 2시간 | 1.5시간 | **4.5시간** |
| **합계** | | | | **약 15시간 / 3-5세션** |

→ 한 세션에 1-2개 슬라이스가 적절. 강행하지 말 것.

---

## 6. 사고 패턴 정리

### 패턴 A: window.* 노출 빠뜨림
**증상**: `ReferenceError: showToast is not defined` 콘솔 에러
**원인**: 추출 후 `window.showToast = showToast` 라인 빠뜨림
**대응**: 새 모듈 footer 점검, dry-run에서 grep으로 사전 확인

### 패턴 B: IIFE 외부 변수 변경
**증상**: 다른 JS 파일 동작 깨짐 (예: `_sqmZ` 사용)
**원인**: 외부 공유 변수를 새 모듈로 옮김
**대응**: IIFE 외부 변수는 절대 추출 대상에 포함시키지 말 것

### 패턴 C: localStorage 키 변경
**증상**: 사용자 설정 초기화됨
**원인**: 추출 시 키 이름 정리한다고 변경
**대응**: 키 이름은 그대로 유지. 정리는 별도 마이그레이션으로

### 패턴 D: 호출 순서 의존
**증상**: 페이지 로드 시 에러 (`Cannot read property of undefined`)
**원인**: 새 모듈이 sqm-inline.js의 어떤 변수에 의존 (IIFE 로드 순서)
**대응**: 새 모듈은 자체완결 필수. 외부 의존은 window.* 만

### 패턴 E: 이벤트 리스너 중복 등록
**증상**: 동일 이벤트가 2번 발생 (예: 토스트 2번 뜸)
**원인**: 추출 시 boot/bindAll에서 등록되던 리스너를 새 모듈에서도 등록
**대응**: 이벤트 리스너 등록은 한 곳에서만. 새 모듈은 함수 정의만.

---

## 7. 진척 체크리스트

```
Phase B 전체 (11단계):
- [x] S1: Tooltip (LOW)         커밋 3afae5e
- [x] S2: escapeHtml (LOW)      커밋 b76f073 (묶음)
- [x] S3: enableTableSort (LOW) 커밋 b76f073 (묶음)
- [x] S4: dbg 디버그 패널 (LOW) 커밋 b76f073 (묶음)
- [ ] S5: 다운로드 헬퍼 (MID)
- [ ] S6a: 토스트 (MID)
- [ ] S6b: API 헬퍼 (MID, 최위험)
- [ ] S7: 컨텍스트 메뉴 + ESC (MID)
- [ ] S8: 모달 인프라 (MID)
- [ ] S9: 페이지 핸들러들 (HIGH)
- [ ] S10: OneStop Outbound (HIGH, 최대)
- [ ] S11: 잔여 정리 (HIGH)

진척: 4/11 (36%, 모두 LOW)
다음 목표: 8/11 (73%, MID 완료) — 3-5세션 분량
```

---

## 8. 사고 발생 시 즉시 대응

### 8.1 자동 검증 단계에서 실패 (node --check 실패 등)
```powershell
python scripts/patch_split_<slice>.py --rollback
```
즉시 백업 복원. 원인 분석 후 스크립트 수정 → 재시도.

### 8.2 앱 실행 단계에서 깨짐
1. 즉시 앱 종료
2. F12 콘솔 에러 메시지 캡처 (어느 함수가 missing인지)
3. rollback 실행
4. 원인 분석:
   - window.* 노출 빠뜨림? → 새 모듈 footer 점검
   - 의존성 측량 빠뜨림? → S<N>-deps.md 보강
   - 외부 공유 변수 침범? → 추출 범위 축소

### 8.3 commit 후 발견된 사고
```bash
git revert <slice-commit-hash>
git push origin main
git push sqm_gpt main
```
원인 분석 후 재작성 → 새 commit으로 재시도.

---

## 9. 참고 자료

- 측량 데이터: `docs/refactor/sqm-inline-structure.md`
- 분할 계획: `docs/refactor/sqm-inline-split-plan.md`
- S1 사례: `scripts/patch_split_tooltip_S1.py` + commit `3afae5e`
- S2-S4 사례: `scripts/patch_split_utility_S234.py` + commit `b76f073`

---

## 변경 이력

| 일자 | 변경 | 작성 |
|---|---|---|
| 2026-05-23 | 초안 작성 (S5-S8 안전 가이드, 17단계 체크리스트, 사고 패턴 5가지) | Ruby |
