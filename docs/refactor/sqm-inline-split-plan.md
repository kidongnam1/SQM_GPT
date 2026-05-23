# sqm-inline.js 분할 설계 (Phase B)

**작성일:** 2026-05-23
**기반 측량:** `sqm-inline-structure.md`
**Codex 이중 검토:** ✅ 완료 (2026-05-23)
**상태:** 설계 확정, 구현 대기

---

## 1. 분할 전략 (전체 그림)

5,635줄 IIFE를 **9단계 슬라이스**로 분할. 가장 안전한 것부터 가장 위험한 것 순서.

| 단계 | 슬라이스 | 줄수 | 위험 | 누적 진척 |
|---|---|---|---|---|
| **S1** | **Tooltip 시스템** (line 11-142) | ~132줄 | 🟢 LOW | 2.3% |
| **S2** | escapeHtml + 기본 유틸 (line 601-606) | ~5줄 | 🟢 LOW | 2.4% |
| **S3** | enableTableSort (line 359-394) | ~35줄 | 🟢 LOW | 3.0% |
| **S4** | dbg 디버그 패널 (line 270-343) | ~70줄 | 🟢 LOW | 4.3% |
| **S5** | 다운로드 헬퍼 (line 152-263) | ~110줄 | 🟡 MID | 6.2% |
| **S6** | 토스트 + API 헬퍼 (line 555-697) | ~140줄 | 🟡 MID | 8.7% |
| **S7** | 컨텍스트 메뉴 + ESC 가드 (line 395-554) | ~165줄 | 🟡 MID | 11.6% |
| **S8** | 모달 인프라 (드래그/리사이즈, line 2736-2900) | ~165줄 | 🟡 MID | 14.5% |
| **S9** | 페이지 핸들러들 (개별 모듈로) | ~3,500줄 | 🔴 HIGH | 80%+ |
| **S10** | OneStop Outbound 모달 (line 2879-3914) | ~1,035줄 | 🔴 HIGH | 98%+ |
| **S11** | 잔여 정리 (boot/bindAll/dispatchAction) | ~잔여 | 🔴 HIGH | 100% |

> 🚨 **원칙**: S1~S8까지 모두 통과해야 S9 진입. S9는 PDCA 사이클 별도 운영.

---

## 2. 첫 슬라이스 (S1) — Tooltip 시스템 상세 설계

### 2.1 추출 대상 — line 11-142 (132줄)
완벽한 내부 IIFE. outer IIFE의 변수 0개 사용. 완전 격리.

**자체 변수:** `_tip`, `_observer`, `_active`, `_showTimer`
**자체 함수:** `convertTitles`, `_pos`, `_show`, `_hide`
**노출:** DOM `#sqm-tooltip` element + `data-sqm-tip` 속성 컨벤션
**의존:** `document`, `window`, `MutationObserver`, `setTimeout` (모두 글로벌)

### 2.2 결과 파일 구조

**새 파일: `frontend/js/sqm-tooltip.js`** (135줄, 자체 IIFE 유지)
```javascript
/* =======================================================================
   SQM Inventory - sqm-tooltip.js
   Extracted from sqm-inline.js (line 11-142) 2026-05-XX
   Original: 2026-04-21 Ruby
   ======================================================================= */
(function () {
  'use strict';
  if (window.__SQM_TOOLTIP_INSTALLED__) return;
  window.__SQM_TOOLTIP_INSTALLED__ = true;

  // ── 추출된 Tooltip IIFE 코드 (line 11-142 원본 그대로) ──
  /* ===================================================
     CUSTOM TOOLTIP SYSTEM (SQM Dark Theme)
     ... (132줄 원본) ...
  */
  (function initSqmTooltip() {
    // ... 원본 본문 ...
  })();
})();
```

**수정: `frontend/js/sqm-inline.js`**
- line 11-142 삭제 (132줄)
- 후속 줄번호 -132 시프트
- IIFE 닫힘 line 5635 → line 5503으로 이동

**수정: `frontend/index.html`**
- `<script src="js/sqm-inline.js?v=...">` 줄 **앞에** 다음 추가:
  ```html
  <script src="js/sqm-tooltip.js?v=20260523a"></script>
  ```

### 2.3 patch_*.py 스크립트 설계

**파일: `scripts/patch_split_tooltip_S1.py`**

```python
"""
Phase B-S1: Extract Tooltip system from sqm-inline.js

Strategy: triple-safe
1. Read sqm-inline.js as bytes
2. Verify exact start/end byte signatures (line 11 marker, line 142 marker)
3. Verify outer IIFE closing line 5635 is intact BEFORE and AFTER edit
4. Backup original with timestamp
5. Write new sqm-tooltip.js
6. Rewrite sqm-inline.js without lines 11-142
7. Update index.html
8. Verify byte-level: IIFE closing intact, line count = original - 132

Idempotent: detects if already extracted (checks for __SQM_TOOLTIP_INSTALLED__)
Rollback: timestamped .bak files for all 3 modified files
"""

import re, shutil, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INLINE = ROOT / 'frontend' / 'js' / 'sqm-inline.js'
TOOLTIP = ROOT / 'frontend' / 'js' / 'sqm-tooltip.js'
HTML = ROOT / 'frontend' / 'index.html'

# 패턴 (정확한 줄 매칭)
TOOLTIP_START_LINE = 11
TOOLTIP_END_LINE = 142
EXPECTED_TOOLTIP_FIRST = '  /* ==='
EXPECTED_TOOLTIP_LAST_BEFORE = '  })();'  # inner IIFE close
EXPECTED_OUTER_IIFE_CLOSE = '})();'  # last line of file

def safe_extract():
    # ... 구현 ...
    pass

if __name__ == '__main__':
    safe_extract()
```

**핵심 안전장치:**
1. **줄번호 + 내용 이중 검증** — line 11이 `/* ===`로 시작, line 142가 `})();`로 끝나야 진행
2. **outer IIFE 닫힘 보호** — 수정 전후 마지막 줄이 `})();`인지 확인
3. **자동 백업** — `sqm-inline.js.bak_S1_20260523_HHMMSS`
4. **idempotent** — 이미 추출됐으면 무동작
5. **rollback 스크립트** — 별도 `scripts/rollback_S1.py` 동시 생성

### 2.4 회귀 테스트 전략

| 테스트 | 도구 | 검증 |
|---|---|---|
| **Node syntax check** | `node --check sqm-tooltip.js && node --check sqm-inline.js` | 두 파일 모두 파싱 OK |
| **HTML 로딩 순서** | grep `<script src="js/sqm-tooltip.js"` index.html | sqm-inline.js 앞에 있음 |
| **outer IIFE 무결성** | tail -1 sqm-inline.js = `})();` | ✅ |
| **줄수 검증** | wc -l: 새 sqm-inline.js = 5635 - 132 ± 5 | 오차 허용 |
| **앱 실행 수동 테스트** | `.\run_v869_clean.bat` | 마우스 hover로 툴팁 표시 확인 |
| **Playwright 회귀** | `npx playwright test tests/sqm_regression.spec.js` | 기존 회귀 통과 |
| **Playwright 신규 (Tooltip)** | 신규 spec 추가 | data-sqm-tip 요소 hover → 툴팁 표시 |

### 2.5 Codex 협업 패턴

| Phase | 역할 분담 |
|---|---|
| **설계** | Claude 1차 → Codex 검토 → 합의 (이미 완료) |
| **patch_*.py 작성** | Claude 작성 → Codex 코드 리뷰 (3가지 안전장치 검증) |
| **실행 전 dry-run** | Claude dry-run 결과 → Codex 결과 분석 |
| **실행 후 검증** | Claude 검증 → 의심 시 Codex 재검토 |

---

## 3. 위험 통제 매뉴얼

### 3.1 절대 지키는 3가지
1. **모든 patch_*.py는 line 5635 `})();` 무결성 사전·사후 검증**
2. **시간 스탬프 백업** — `xxx.bak_S<N>_YYYYMMDD_HHMMSS`
3. **앱 실행 검증 통과 전에는 다음 슬라이스로 안 넘어감**

### 3.2 사고 발생 시 (line 5635 가 깨졌을 때)
- 즉시 `scripts/rollback_S1.py` 실행
- bak 파일에서 복원
- git restore도 옵션 (commit 전이면)

### 3.3 진행 검증 체크리스트 (각 슬라이스마다)
```
☐ patch_*.py 작성 완료
☐ Codex 리뷰 통과
☐ dry-run 결과 정상
☐ 백업 파일 생성 확인
☐ 실제 적용
☐ node --check 양 파일 통과
☐ outer IIFE 닫힘 확인 (tail -1)
☐ 줄수 검증
☐ index.html 로딩 순서 확인
☐ 앱 실행 → 수동 기능 테스트
☐ Playwright 회귀 통과
☐ git commit (점진 진척 기록)
☐ 다음 슬라이스로
```

---

## 4. 다음 세션 시작 시 행동

이 문서를 읽으면 다음 세션에서 누구든 즉시 시작 가능:

1. `docs/refactor/sqm-inline-structure.md` 읽기 (측량 데이터)
2. 이 문서 `sqm-inline-split-plan.md` 읽기 (분할 계획)
3. **S1 patch_*.py 스크립트 작성부터 시작**
4. 위 §3.3 체크리스트 따라 진행
5. S1 통과 후 S2-S4 (모두 LOW 위험)는 같은 패턴으로 진행 가능
6. S5부터는 매 슬라이스마다 Codex 협업 강화

---

## 5. 예상 일정 (단독 작업 가정)

| 슬라이스 | 작업량 | 예상 |
|---|---|---|
| S1 (Tooltip) | 스크립트 + 검증 | 2-3시간 |
| S2-S4 (소형) | 각 1-2시간 | 4-6시간 |
| S5-S8 (중형) | 각 3-5시간 | 12-20시간 |
| S9 (페이지) | 페이지별 점진 | 며칠 |
| S10 (OneStop) | 단일 거대 모달 | 1-2주 |
| S11 (정리) | 잔여 + 최적화 | 며칠 |
| **합계** | | **3-6주 분량** |

---

## 6. 메트릭

| 지표 | 시작 | 목표 |
|---|---|---|
| sqm-inline.js 줄수 | 5,635 | < 500 (boot+dispatch만 남김) |
| 분리 모듈 수 | 6개 (이전 refactor 결과) | 15-20개 |
| 평균 모듈 크기 | n/a | < 300줄 |
| 회귀 통과율 | 현재 통과 | 100% 유지 |
| Edit 도구 사고 | 1건 (2026-05-15) | 0건 |

---

## 7. 측량/검토 출처

- 1차 측량: Claude Opus 4.7 (2026-05-23) — `sqm-inline-structure.md`
- 2차 검토: Codex CLI 0.133.0 (2026-05-23) — section boundaries verified, Tooltip 첫 슬라이스 동의, line 5635 fragility 강조

---

## 변경 이력

| 일자 | 변경 | 작성 |
|---|---|---|
| 2026-05-23 | 초안 작성 (S1-S11 슬라이스 정의, S1 상세 설계) | Ruby |
