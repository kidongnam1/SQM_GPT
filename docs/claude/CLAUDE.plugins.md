# CLAUDE.plugins.md — Claude CLI 9개 플러그인 + 4가지 작업 모드

> **로드 시점:** Claude CLI 사용 시 (Cowork에서는 자동 비활성)
> **작성:** 2026-05-09 — Ruby (Senior Software Architect Mode)
> **목적:** 9개 플러그인을 4가지 작업 모드로 단순화 + 컨텍스트 폭발 방지

---

## 📦 설치된 플러그인 9개

| # | 플러그인 | 버전 | 자동 트리거 | SQM 활용도 |
|:---:|---|---|:---:|:---:|
| 1 | **superpowers** | 5.1.0 | ✅ | 🟢 매우 높음 |
| 2 | **bkit** (gstack 포함) | 2.0.8 | ⚠️ 명시적 | 🟢 매우 높음 |
| 3 | **codex** (OpenAI 교차검증) | 1.0.4 | ⚠️ 명시적 | 🟡 중간 |
| 4 | **context7** (최신 API 문서) | unknown | ✅ | 🟢 매우 높음 |
| 5 | **code-review** (커밋 직전) | unknown | ✅ | 🟢 매우 높음 |
| 6 | **code-simplifier** | 1.0.0 | ⚠️ 명시적 | 🟡 중간 |
| 7 | **frontend-design** (React) | unknown | ⚠️ 명시적 | 🟡 중간 (SQM은 Vanilla JS) |
| 8 | **pyright-lsp** (Python 타입) | 1.0.0 | ✅ 백그라운드 | 🟢 매우 높음 |
| 9 | **telegram** (배포 알림) | 0.0.6 | ⚠️ 명시적 | 🟢 (마일스톤 시) |

---

## 🎯 4가지 작업 모드 — 한 번에 여러 플러그인 활성화

### 🎯 모드 ① — PLAN (계획)
**활성:** superpowers + bkit (gstack 포함)
**언제:** Phase 시작, 새 패치 계획, 리팩토링 결정
**효과:** "혼자 결정"이 아닌 "5명이 동시 검토" 시뮬레이션

```
[Claude Code]
/office-hours          ← bkit/gstack: 가정 명시 강제
/brainstorming         ← superpowers: 5단계 워크플로우
```

---

### 🛠️ 모드 ② — CODE (구현)
**활성:** context7 + pyright-lsp + code-simplifier + frontend-design
**언제:** 실제 코드 작성, 함수 추가, UI 변경
**효과:** "deprecated API 자신있게 사용" 사고 방지 + 타입 안전

```
[자동 작동 — 별도 명령 불필요]
- context7가 코딩 중 최신 API 문서 자동 조회
- pyright-lsp가 Python 타입 자동 검사
- /simplify (필요시) — 복잡한 코드 단순화
- /design (UI 변경 시) — React 디자인 자동 생성
```

---

### ✅ 모드 ③ — VERIFY (검증)
**활성:** code-review + bkit (qa) + codex
**언제:** 패치 완료 후, 커밋 직전, 배포 전
**효과:** **3중 검증** (Anthropic Claude + Anthropic code-review + OpenAI Codex)

```
[Claude Code]
/code-review           ← 변경 라인 자동 분석 (자동 트리거)
/qa                    ← bkit/gstack: 자동 QA 실행
/codex-review          ← Codex (OpenAI) 교차 검증
```

---

### 🚀 모드 ④ — SHIP (배포 + 회고)
**활성:** bkit (ship + retro) + telegram
**언제:** EXE 빌드 + 배포, LAYER 완성, Phase 마일스톤
**효과:** 배포 자동화 + 회고 기록 + 텔레그램 알림

```
[Claude Code]
/ship                  ← bkit/gstack: 테스트 우선 + 검증 가능 목표화
/retro                 ← bkit/gstack: 회고 자동 작성
/notify                ← telegram: 사장님 휴대폰으로 배포 알림
```

---

### 🐛 모드 ⑤ — DEBUG (디버깅, 보조)
**활성:** superpowers + codex
**언제:** 버그 추적, 에러 진단, 회귀 발생 시
**효과:** Superpowers 3-fail 모드 + Codex 교차 진단

```
[Claude Code]
/debugging             ← superpowers: 3번 실패 시 아키텍처 리뷰 강제
/codex-debug           ← Codex 교차 진단
```

---

## 🎛 PowerShell `$PROFILE` 함수 — 모드 전환 자동화

```powershell
# $PROFILE 파일에 추가 (notepad $PROFILE)

function sqm-plan {
    cd D:\program\SQM_inventory\SQM_v867_clean
    Write-Host "🎯 PLAN 모드 — superpowers + bkit/gstack" -ForegroundColor Cyan
    claude --plugin superpowers --plugin bkit
}

function sqm-code {
    cd D:\program\SQM_inventory\SQM_v867_clean
    Write-Host "🛠️ CODE 모드 — context7 + pyright + simplifier" -ForegroundColor Green
    claude --plugin context7 --plugin pyright-lsp --plugin code-simplifier
}

function sqm-verify {
    cd D:\program\SQM_inventory\SQM_v867_clean
    Write-Host "✅ VERIFY 모드 — code-review + bkit + codex" -ForegroundColor Yellow
    claude --plugin code-review --plugin bkit --plugin codex
}

function sqm-ship {
    cd D:\program\SQM_inventory\SQM_v867_clean
    Write-Host "🚀 SHIP 모드 — bkit + telegram" -ForegroundColor Magenta
    claude --plugin bkit --plugin telegram
}

function sqm-debug {
    cd D:\program\SQM_inventory\SQM_v867_clean
    Write-Host "🐛 DEBUG 모드 — superpowers + codex" -ForegroundColor Red
    claude --plugin superpowers --plugin codex
}
```

**설정 후 사용:**
```powershell
sqm-plan      # 계획 시
sqm-code      # 코딩 시
sqm-verify    # 검증 시
sqm-ship      # 배포 시
sqm-debug     # 디버깅 시
```

---

## 📋 슬래시 명령 빠른 참조

### 자주 쓰는 5개 (외울 것)

| 명령 | 출처 | 효과 |
|---|---|---|
| `/office-hours` | bkit/gstack | 작업 시작 전 가정 명시 강제 |
| `/brainstorming` | superpowers | 5단계 워크플로우 (Clarify→Design→Plan→Code→Verify) |
| `/code-review` | code-review | 변경 라인 자동 분석 |
| `/qa` | bkit/gstack | 자동 QA 실행 |
| `/ship` | bkit/gstack | 테스트 우선 + 검증 가능 배포 |

### bkit/gstack 50+ 스킬 카테고리

#### 계획 (Plan)
- `/office-hours` `/autoplan` `/plan-ceo-review` `/plan-design-review` `/plan-eng-review` `/plan-tune`

#### 개발 (Build)
- `/design-consultation` `/design-html` `/design-review` `/design-shotgun`
- `/devex-review` `/pair-agent` `/codex`

#### 검증 (Verify)
- `/review` `/qa` `/qa-only` `/careful` `/guard` `/health`
- `/canary` `/investigate` `/benchmark`

#### 배포/회고 (Ship & Learn)
- `/ship` `/land-and-deploy` `/document-release`
- `/freeze` `/unfreeze` `/landing-report`
- `/retro` `/learn`

---

## 🚀 SQM 실전 시나리오 — Phase 6 EXE 빌드 (5/15-16)

### [5/15 금 저녁] — 계획
```powershell
sqm-plan
```
```
/office-hours
"Phase 6 EXE 빌드 시작.
 1주 사용 발견사항 정리 + Python 3.14.2 호환성 우려.
 PyInstaller spec 검토 필요."
```
→ bkit/gstack가 가정 5개 강제 명시
→ superpowers가 5단계 워크플로우 시작

---

### [5/16 토 오전] — 코딩
```powershell
sqm-code
```
```
"build_v867.spec 작성 + PyInstaller 빌드 실행"
```
→ context7가 PyInstaller 6.2 최신 문서 자동 조회
→ pyright-lsp가 Python 타입 자동 검사
→ code-simplifier가 복잡한 spec 자동 단순화

---

### [5/16 토 오후] — 검증
```powershell
sqm-verify
```
```
/code-review        ← 변경 라인 자동 분석
/qa                 ← Playwright + pytest 자동 실행
/codex-review       ← OpenAI Codex 교차 검증
```
→ **3중 검증 통과 = production-ready**

---

### [5/16 토 저녁] — 배포 + 회고
```powershell
sqm-ship
```
```
/ship             ← EXE 배포 자동화
/retro            ← 회고 자동 작성 (CLAUDE.history.md 갱신)
/notify           ← 텔레그램으로 배포 완료 알림
```

---

## 📊 컨텍스트 부담 측정

| 모드 | 활성 플러그인 수 | 추정 토큰 | 200K 대비 |
|---|:---:|:---:|:---:|
| 모드 ① PLAN | 2개 | ~3,500 | 1.75% |
| 모드 ② CODE | 4개 | ~4,500 | 2.25% |
| 모드 ③ VERIFY | 3개 | ~4,000 | 2.0% |
| 모드 ④ SHIP | 2개 | ~2,000 | 1.0% |
| 모드 ⑤ DEBUG | 2개 | ~3,000 | 1.5% |
| **9개 모두** | 9개 | **~10,000** | **5.0%** |

**의미:**
- 모드 분리 = 컨텍스트 부담 평균 2-3% (이상적)
- 9개 모두 활성 = 5% (코드까지 합치면 25-30% 즉시 소비, 위험)

---

## ⚠️ 주의사항 + 트러블슈팅

### 명령 충돌
- `/review` (superpowers) vs `/review` (bkit) → 모드 분리로 자동 해결
- 만약 충돌 발생 시 → `--plugin <name>` 명시로 강제 지정

### 자동 트리거 비활성화
필요 시 특정 플러그인만 일시 비활성화:
```bash
claude --no-plugin frontend-design
```

### codex 비용 관리
- OpenAI API 비용 발생 (Codex)
- 월 예산 cap 권장: $20
- 설정: `https://platform.openai.com/account/billing/limits`

### telegram bot 설정
1회 설정 필요:
```bash
# Telegram에서 BotFather에게 /newbot
# 받은 token을 환경변수로
$env:TELEGRAM_BOT_TOKEN = "your_bot_token_here"
$env:TELEGRAM_CHAT_ID = "your_chat_id"
```

---

## 🎯 SQM 작업 빈도별 활용 매트릭스

| 작업 빈도 | 플러그인 | 비고 |
|---|---|---|
| 🔴 매일 (자동) | context7, pyright-lsp | 의식 없이 자동 동작 |
| 🟠 주 2-3회 | superpowers, code-review | 코드 작업 시 |
| 🟡 주 1회 | bkit `/office-hours` `/qa` `/ship` | 패치/배포 시 |
| 🟢 월 1-2회 | codex, code-simplifier, frontend-design | 큰 변경 시 |
| 🔵 마일스톤마다 | telegram `/notify` | Phase 완료 시 |

---

## 🏆 마스터 5가지 슬래시 명령 (SQM 핵심)

대표님은 50+ 슬래시 명령 중 **이 5개만** 마스터하시면 충분:

1. **`/office-hours`** — 작업 시작 전 가정 강제 (어제 6-pass SOP 정신)
2. **`/brainstorming`** — 5단계 워크플로우 (Phase 6 계획 시)
3. **`/code-review`** — 커밋 직전 자동 검증
4. **`/qa`** — Playwright + pytest 자동 실행
5. **`/retro`** — LAYER/Phase 완료 후 회고 자동 작성

---

## 📚 참고 자료

- `@CLAUDE.md` — SQM 핵심 규칙 (압축판)
- `@docs/claude/CLAUDE.layer2.md` — LAYER 2 작업 상세
- `@docs/claude/CLAUDE.test.md` — 테스트 규칙
- `@docs/claude/CLAUDE.history.md` — 학습 로그 + 모니터링 (Python 3.14.2)
- `@docs/claude/CLAUDE.full.md` — 원본 백업
- gstack GitHub: https://github.com/garrytan/gstack
- Superpowers GitHub: https://github.com/obra/superpowers-marketplace

---

**Ruby (Senior Software Architect Mode) — Claude CLI 플러그인 사용 가이드 — 2026-05-09**
