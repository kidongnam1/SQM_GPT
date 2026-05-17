# SQM v8.6.8 | PyWebView + FastAPI + SQLite

**작업 폴더:** `D:\program\SQM_inventory\SQM_v868_claan`
**GitHub:** `https://github.com/kidongnam1/sqm_3` (main)
**최종 갱신:** 2026-05-15

---

## STACK
PyWebView 5 · FastAPI 0.104 · Vanilla JS · SQLite WAL · Python 3.11

## CORE RULES
- **Rule 5 (강화 2026-05-15)** — Edit 툴 금지 조건:
  - ① 1000줄 이상 파일 (예: sqm-inline.js 7516줄, sqm-core.js 2000+줄)
  - ② IIFE 패턴 `(function(){...})();` 또는 `})();` 로 끝나는 파일
  - ③ 위 조건 해당 시 무조건 `scripts/patch_*.py` 스크립트로 처리
  - 📌 사고 사례 (2026-05-15): Edit 툴이 sqm-inline.js 끝 10줄(IIFE 닫힘)을 날림 → 복구 + Python 스크립트 재패치
- **Rule 6** — git commit/push은 Windows CMD에서만 (VM 금지)
- **방지책 ②** — 코드 + 주석 먼저 읽고 수정 (추측 금지)
- **방지책 ④** — 세션 시작 시 py_compile + node --check 전수검사
  - 최근 통과 기록: 2026-05-15 Python 412/412, JS 37/37 ✅
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
- ✅ sqm-inline.js 라우터 핫픽스 (2026-05-15) — case 'pending'/'available' 누락 → Preparing stub 버그 수정 (scripts/patch_sqm_inline_router.py)
- 🎯 다음: Phase 6 EXE 빌드 (5/15-16 주말)

## BACKLOG (Phase 6 EXE 빌드 이후 우선순위 순)
- **🥇 P2-1 라우터 단일화 리팩토링 (다음 스프린트 1순위)** — sqm-inline.js의 renderPage() 제거 + sqm-core.js로 통합. 현재 두 파일에 동일 라우터가 있어 새 사이드바 메뉴 추가 시 양쪽 동기화 필요. 이번 버그(case 'pending' 누락)의 **구조적 원인** — 재발 방지 핵심.
- **🥈 P2-2 Dead code 정리** ✅ **완료 (2026-05-15)** — 20개 백업 파일 _archive/ 로 이동 (scripts/cleanup_archive_backups.py)
- **🥉 P2-3 Playwright 회귀 테스트** — 사이드바 6개 탭(Pending/Available/Allocation/Picked/Return/Move) 클릭 후 page-container에 'Preparing:' 문자열 없는지 자동 검증. 이번 버그 같은 라우터 누락 회귀 자동 차단.
- **P2-4 정합성 자동 수정 버튼** — /api/integrity/check 결과의 TONBAG_COUNT_MISMATCH / ORPHAN_TONBAG / STATUS_MISMATCH 일괄 처리 SQL 자동 실행. 매번 손으로 안 고쳐도 되게.
- **P2-5 PyWebView 디버그 모드 토글** — 운영 빌드(F12 OFF) vs 개발 빌드(F12 ON) 분기. 향후 사고 시 콘솔 확인 가능해짐.

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
