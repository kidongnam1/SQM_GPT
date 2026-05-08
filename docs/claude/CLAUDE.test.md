# CLAUDE.test.md — 테스트 규칙

> **로드 시점:** pytest / Playwright E2E / 회귀 검증 시
> **작성:** 2026-05-08 — Ruby (Senior Software Architect Mode)

---

## 🧪 pytest 회귀 테스트 자산

| 파일 | 테스트 수 | 용도 |
|---|:---:|---|
| `tests/test_phase5_parity.py` | 44 | v864.2 ↔ v8.6.7 패리티 |
| `tests/test_sample_parity.py` | 6 | 샘플 정합성 |
| `tests/test_e2e_playwright.py` | 12 | E2E 자동화 |
| `tests/test_frontend_connection.py` | 4 | HTTP 스모크 |

**실행:**
```powershell
cd D:\program\SQM_inventory\SQM_v867_clean
python -m pytest tests/ -v
```

---

## 🌐 Playwright E2E 자동화

### 1회 셋업 (~5분)
```powershell
pip install playwright pytest-playwright
playwright install chromium
```

### 매 패치 후 회귀 (1분)
```powershell
# 별도 터미널: SQM 시작
python main_webview.py

# 다른 터미널: 테스트
python -m pytest tests/test_e2e_playwright.py -v
```

### 자동화 항목 (12개)
- TestItem4InventoryData (5개) — 페이지 / 메뉴바 / KPI / JS 모듈
- TestItem5InboundMenu (2개) — 입고 메뉴
- TestItem6OutboundMenu (2개) — 출고 메뉴 + sidebar-counts
- TestItem7ExcelExport (1개) — 파일 → 내보내기
- TestRegressionP1P2P3 (2개) — 콘솔 에러 / idempotency

### 자동화 불가 (수동 4개)
1. PyWebView 시작 시간
2. 스플래시 시각 확인
3. 메인 페이지 자동 전환
4. 창 닫기 + 좀비 프로세스

---

## 🎯 MANUAL_SMOKE_CHECKLIST 8개 항목

| # | 항목 | 자동화 |
|:---:|---|:---:|
| 1 | 시작 시간 < 1초 (스플래시) | ❌ |
| 2 | 스플래시 → 메인 6~10초 | ❌ |
| 3 | 메인 페이지 표시 | ❌ |
| 4 | 재고 데이터 정상 | ✅ |
| 5 | 입고 메뉴 다이얼로그 | ✅ |
| 6 | 출고 메뉴 다이얼로그 | ✅ |
| 7 | 엑셀 내보내기 | ✅ 부분 |
| 8 | 창 닫기 + 좀비 0 | ❌ |

---

## 🛡 6-Pass 검증 방법론

어제 (2026-05-06) 적용 사례 → 단일 검증으로 놓쳤을 3개 버그 발견:
- 1차 → 5차 단계마다 새로운 결함 탐지
- CRITICAL JS recursion (3차)
- MAJOR `_navigated` 2-state (2차)
- MEDIUM atexit (2차)

자산 보고서:
- `REPORT_1차~456차_2026-05-06.md`
- `AUDIT_2차~6차_*.md` (총 15개)

---

## 📋 Definition of Done

1. ✅ JS syntax — `node --check`
2. ✅ Python syntax — `py_compile` 전수
3. ✅ 기능 일치 — v864.2와 같은 입력 → 같은 출력
4. ✅ 에러 처리 — 실패 시 Toast 알림
5. ✅ 롤백 가능 — git revert로 단일 기능 되돌림
