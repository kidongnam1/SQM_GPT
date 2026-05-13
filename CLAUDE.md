# SQM v8.6.8 | PyWebView + FastAPI + SQLite

**작업 폴더:** `D:\program\SQM_inventory\SQM_v868_claan`
**GitHub:** `https://github.com/kidongnam1/sqm_3` (main)
**최종 갱신:** 2026-05-11

---

## STACK
PyWebView 5 · FastAPI 0.104 · Vanilla JS · SQLite WAL · Python 3.11

## CORE RULES
- **Rule 5** — 300줄↑ Edit 툴 금지, Python 스크립트만
- **Rule 6** — git commit/push은 Windows CMD에서만 (VM 금지)
- **방지책 ②** — 코드 + 주석 먼저 읽고 수정 (추측 금지)
- **방지책 ④** — 세션 시작 시 py_compile + node --check 전수검사
- 색상/폰트 → `design-tokens.css` 변수만 (하드코딩 금지)

## STATUS 설계 (확정 2026-05-11)
```
PENDING   → 포트 입항, 창고 미반입 (파싱 직후)
AVAILABLE → 창고 반입 확정 (재고 집계 시작)
RESERVED  → 배정됨
PICKED    → 출고 작업 중 (취소 가능)
SOLD      → 차량 출발 = 거래 종료 (OUTBOUND 흡수, 취소 불가)
RETURN    → 반품
```
- `movement_type='OUTBOUND'` (stock_movement 이동 유형) — STATUS 아님, 유지
- `port_date` / `inbound_type('DIRECT'|'BOND')` 컬럼 inventory 테이블에 추가됨

## CURRENT STATE (2026-05-11)
- ✅ LAYER 1 + 2 + 3 모두 완료 (90be151, 7cdcd29)
- ✅ 발견 ①② + Title Transfer Date 라벨 (65cc27d, c83aac0)
- ✅ CLAUDE.md 5분할 + 패치 자산화 (dfd7459, 7cdcd29)
- ✅ Claude CLI 9개 플러그인 설치 (superpowers/bkit/codex/context7/code-review/code-simplifier/frontend-design/pyright-lsp/telegram)
- ✅ PENDING 입고 대기 워크플로우 (053fa7a) — port_date/inbound_type 컬럼, /pending /confirm API
- ✅ OUTBOUND→SOLD 통합 (b2d136e) — Python 40+파일 + JS 6파일, STATUS 6개로 단순화
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

## 용어 · 협업 — 「루비」
- **루비**: 사용자가 Cursor/이 AI를 부르는 **애칭**(호칭). 예전 문서의 `RUBY PERSONA` 응답 템플릿 이름과는 **다름**.
- **루비 제안대로**: 별도 지시가 없으면 AI가 제안한 순서·도구·절차·우선순위를 **기본으로 따름**. (이 파일의 **CORE RULES / DON'T**, `AGENTS.md`, 방지책과 **충돌하면 프로젝트 규칙 우선**.)

> 과거 `[Question][Intent][Response]`·비유·영/베트남어 고정 포맷은 **쓰지 않음** — 「루비」는 애칭만 해당.
