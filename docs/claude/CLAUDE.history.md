# CLAUDE.history.md — 학습 로그 + 사고 이력

> **로드 시점:** 새 사고 발생 시 / 회고 시 / Phase 로드맵 확인 시
> **작성:** 2026-05-08 — Ruby (Senior Software Architect Mode)

---

## 🚨 자주 하는 실수 방지책

| # | 방지책 | 내용 |
|:---:|---|---|
| ① | 설계 결정 이유 기록 | 수정마다 "왜"를 함께 기록 ("당연하다"도 대상) |
| ② | 코드 읽기 전 수정 금지 | 버그같다 판단해도 → 코드 + 주석 먼저 확인 |
| ③ | 300줄↑ 작은 수정도 Edit 툴 금지 | 예외 없음 — 항상 Python 스크립트 (Rule 5) |
| ④ | 세션 시작 직후 전수검사 | py_compile + node --check 즉시 (Linux mount staleness) |

---

## 📚 Ruby 학습 로그

| 날짜 | 틀린 판단 | 올바른 방향 | 반영 |
|------|-----------|-------------|------|
| 2026-05-02 | Rule A 위반 — 질문 먼저 | 추천 먼저 후 질문 | Rule A 재확인 |
| 2026-05-04 | [Question]/[Intent]/시간 누락 | 매 응답 헤더 필수 | Rule E 추가 |
| 2026-05-04 | GIT_INDEX_FILE 커밋 → 400파일 삭제 | git은 CMD에서만 | Rule 6 추가 |
| 2026-05-04 | 전수검사 미실시 → truncated 방치 | 세션 종료 전 전수검사 | Rule 5 강화 |
| 2026-05-05 | CLAUDE.md v865 표기 방치 | 폴더명과 버전 일치 | 전면 재작성 |
| 2026-05-05 | 코드 주석 미확인 → flip-flop 3회 | 수정 전 코드+주석 먼저 | 방지책 ② 추가 |
| 2026-05-05 | StreamingResponse PyWebView 비호환 | exports/ + os.startfile() | 설계결정 기록 |
| 2026-05-05 | Linux mount staleness → 오인 | 즉시 py_compile + node --check | 방지책 ④ 추가 |
| 2026-05-05 | confirm_outbound() 미동기화 | 역방향 전수검사로 탐지 | commit 6b9ec31 |
| 2026-05-06 | 단일 검증으로 P1 검토 | 6-pass 검증 (3개 버그 추가) | 6-pass SOP 자산화 |
| 2026-05-08 | CLAUDE.md 단일 거대 파일 | 5분할 + ON/OFF 운영 | docs/claude/ 분할 |
| 2026-05-08 | gstack URL 추측 제공(`gstack-skills`) → 404 | web_search로 검증 후 인용 (`garrytan/gstack`) | URL 제공 시 web_search 의무 |
| 2026-05-08 | PowerShell `Get-Content` 한글 mojibake | UTF-8 파일을 cp949로 읽음 → `-Encoding UTF8` 옵션 | 향후 검증 명령에 항상 명시 |
| 2026-05-08 | Python 3.14.2 사용 중 (CLAUDE.md 규정 = 3.11) | 부팅 정상 작동 확인 + 모니터링 | 호환성 이슈 발생 시 즉시 다운그레이드 |

---

## 🗺 Phase 로드맵

| Phase | 내용 | 상태 |
|:---:|---|:---:|
| Phase 0 | Safety Net (pytest, smoke) | ✅ |
| Phase 1 | UI Manifest + 85 기능 매핑 | ✅ |
| Phase 1c | UI 요소 복구 | ✅ |
| Phase 2 | TOP 3 엔드포인트 | ✅ |
| Phase 3 | Dashboard KPI 실데이터 | ✅ |
| Phase 4 | 사이드바 9탭 + 메뉴 60개 | ✅ |
| Phase 5 | 회귀 테스트 자동화 | ✅ |
| **Phase 6** | **EXE 빌드 (PyInstaller)** | 🟡 다음 |
| Phase 7 | 사장님 실사용 1주 | ⏳ |
| Phase 8 | 🏆 v8.6.7 공식 릴리스 | 🎯 |

**진행률:** 약 92%

---

## 🐛 주요 버그 수정 (v866 → v867)

### 2026-05-05 — 양방향 입출고 정합성
- Bug ① outbound_mixin.py LOT mode UNIQUE 위반 → 1행 INSERT
- Bug ② sqm-allocation.js `_allocState` undefined → 모듈 내 선언
- Bug ③ queries.py allocation-summary inventory JOIN
- Bug ④ outbound_mixin.py LOT mode RESERVED 미갱신
- Bug ⑤ Dashboard AVAILABLE 오버카운트 → tonbag 레벨 집계

### 2026-05-06 — LAYER 1 비동기 패치 (6-pass)
- P1 main_webview.py — Splash 즉시 표시
- P2 ollama_manager.py — 비동기화
- P3 database.py — db_execute_async + ThreadPoolExecutor
- P11 uvicorn 로거 propagate=False

### 2026-05-08 — 발견 ①② + CLAUDE.md 분할
- 발견 ① main_webview.py v8.6.6 → v8.6.7 (6곳)
- 발견 ② /api/dashboard/alerts 엔드포인트
- CLAUDE.md → 5분할 (압축 + layer2 + test + history + full)
- commit `65cc27d`

---

## 📦 핵심 산출물 (절대 삭제 금지)

`docs/handoff/` — 2026-04-21 추출

| 파일 | 용도 |
|---|---|
| `v864_2_structure.json` | UI 구조 (메뉴 5/탭 9/툴바 7) |
| `feature_matrix.json` | 85개 기능 완전 매핑 |
| `design_tokens.json` | 156색상 + 17테마 |

---

## 🛠 기술 스택 상세

| 계층 | 기술 |
|---|---|
| Desktop Shell | PyWebView 5.1.0 |
| Backend | FastAPI 0.104.1 + Uvicorn 0.24.0 |
| Frontend | Vanilla HTML/CSS/JS |
| Data | pandas 2.1.3 + openpyxl + SQLite WAL |
| AI | Google Gemini (PDF 파싱) |
| Packaging | PyInstaller 6.2.0 |

**❌ 금지:** React/Vue/Svelte, TypeScript, Tailwind, Docker

---

## 🔧 v864.2 비즈니스 로직 (수정 금지 — Rule 1)

- `engine_modules/`, `features/`, `parsers/`, `utils/`
- 이유: v864.2는 실사용 검증 코드. 리팩토링 = 버그 양산

---

## 🤖 루비(Ruby) 행동 규칙

### Rule A — 추천 먼저, 질문 그 다음
형식: "**루비의 추천:** [선택지] — 이유 / 확인: [A/B/C]"

### Rule B — 추천 강도
- 기술 결정: 강하게 → "이렇게 하세요"
- 비즈니스: → "이게 유리, 사장님 상황 우선"

### Rule C — 즉시 학습 + 자동 기록
"이전 [X]였는데 [Y]가 맞음 — 다음부터 반영"

### Rule D — 확신 없음 명시
60% 이하 → "확신 없음 (약 X%)"

### Rule E — 응답 포맷
- 첫 줄: `[Question][Intent][Response]` + 시각
- 마지막: 영어/베트남어 1문장 + 발음
