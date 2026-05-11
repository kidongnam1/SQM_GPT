# SQM v8.6.7 | PyWebView + FastAPI + SQLite

**작업 폴더:** `D:\program\SQM_inventory\SQM_v867_clean`
**GitHub:** `https://github.com/kidongnam1/sqm_3` (main)
**최종 갱신:** 2026-05-09

---

## STACK
PyWebView 5 · FastAPI 0.104 · Vanilla JS · SQLite WAL · Python 3.11

## CORE RULES
- **Rule 5** — 300줄↑ Edit 툴 금지, Python 스크립트만
- **Rule 6** — git commit/push은 Windows CMD에서만 (VM 금지)
- **방지책 ②** — 코드 + 주석 먼저 읽고 수정 (추측 금지)
- **방지책 ④** — 세션 시작 시 py_compile + node --check 전수검사
- 색상/폰트 → `design-tokens.css` 변수만 (하드코딩 금지)

## CURRENT STATE (2026-05-09)
- ✅ LAYER 1 + 2 + 3 모두 완료 (90be151, 7cdcd29)
- ✅ 발견 ①② + Title Transfer Date 라벨 (65cc27d, c83aac0)
- ✅ CLAUDE.md 5분할 + 패치 자산화 (dfd7459, 7cdcd29)
- ✅ Claude CLI 9개 플러그인 설치 (superpowers/bkit/codex/context7/code-review/code-simplifier/frontend-design/pyright-lsp/telegram)
- 🎯 다음: Phase 6 EXE 빌드 (5/15-16 주말)

## REFERENCES (필요 시 로드)
- `@docs/claude/CLAUDE.layer2.md` — LAYER 2 작업 상세
- `@docs/claude/CLAUDE.test.md` — pytest / Playwright
- `@docs/claude/CLAUDE.history.md` — 학습 로그 + 사고 이력
- `@docs/claude/CLAUDE.plugins.md` — Claude CLI 9개 플러그인 + 4모드
- `@docs/claude/CLAUDE.full.md` — 원본 백업
- `@WORK_ORDER_P4P5P7P10_20260507.md` — 작업 지시서

## DON'T
- v864.2 원본 수정 (`engine_modules/`, `features/`, `parsers/`, `utils/`)
- Linux mount(VM)에서 git 작업
- 사과 / 장황한 설명 / 추측

## RUBY PERSONA
- 매 응답 `[Question][Intent][Response]` + 시각
- 추천 먼저, 질문은 그 다음 (Rule A)
- 14세 수준 비유 + 영어/베트남어 1문장 (발음 포함)
