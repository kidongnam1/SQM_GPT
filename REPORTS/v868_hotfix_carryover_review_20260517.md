# v868 → v869 hotfix carryover review

- 작성일: 2026-05-17
- 목적: `SQM_v868_claan`에서 이미 수정됐지만 `sqm_v869_clean`으로 넘어오며 누락되거나 되돌아간 hotfix를 점검

## 결론

`sqm_v869_clean`은 전체적으로 최신 기준본이지만, 아래 두 항목은 `v868`에서 이미 해결됐던 수정이 누락된 **회귀(regression)** 로 판단한다.

1. `frontend/js/sqm-inventory.js`
   - Pending `⊙ / ⋯` 버튼의 inline `onclick` 인자 직렬화 방식이 다시 깨질 수 있는 형태로 돌아감
2. `tests/sqm_regression.spec.js`
   - 실제 DOM은 `data-route`를 쓰는데, 테스트 일부가 `data-page` / `data-tab` 구버전 셀렉터로 되돌아감

## 이번에 즉시 반영한 항목

| 항목 | 반영 내용 | 근거 |
|---|---|---|
| Pending 버튼 회귀 | `lotJson` inline 주입 제거, 작은따옴표 인자 방식 복구 | `v868/scripts/patch_fix_pending_btn.py` |
| 라우터 회귀 테스트 셀렉터 | `data-route` 기준으로 통일 | `v868/tests/sqm_regression.spec.js`, 현재 `frontend/index.html` |

## 참고한 v868 파일별 판단

| 파일 | 판단 | 이유 |
|---|---|---|
| `scripts/patch_fix_pending_btn.py` | **즉시 반영 가치 높음** | 실제 사용자 기능을 깨뜨릴 수 있는 회귀를 설명하고 있음 |
| `scripts/patch_pending_empty.py` | 선택 반영 | 기능보다 UI 표현 차이. 현재 v869의 단순화가 의도일 수도 있음 |
| `scripts/fix_template_duplicates.py` | 정책만 참고 | 선사별 중복 템플릿 정리라는 생각은 좋지만, 특정 ID 하드코딩이 강함 |
| `scripts/compare_v868_v869.py` | **범용화 후 반영 완료** | `scripts/compare_release_folders.py`로 재작성해 임의 릴리스 폴더 비교에 재사용 가능 |

## 추가로 볼 만한 후보

### 1. 템플릿 중복 방지 정책

`fix_template_duplicates.py`의 코드를 그대로 이식하기보다는, 아래처럼 일반화하는 편이 더 낫다.

- `carrier_id + bag_weight_kg` 조합 기준 중복 활성 템플릿 감지
- 중복 발견 시 UI 경고 또는 API 검증
- 수동 정리보다 서버 정책으로 승격

### 2. 전수 메뉴 검사

`v868`의 `scripts/test_all_menus_playwright.py`는 넓은 회귀 탐지에 장점이 있다.  
현재 `v869`의 빠른 smoke test를 대체하지 말고, 별도 **exhaustive UI sweep** 으로 부활시키는 것이 좋다.

- 반영 완료: `scripts/test_all_menu_actions_playwright.py`
- 역할 분리:
  - `scripts/test_all_menus_playwright.py` = 빠른 smoke
  - `scripts/test_all_menu_actions_playwright.py` = 넓은 전수 검사

## 권장 운영 방식

1. `v869_clean`을 계속 기준본으로 사용
2. 단, `v868` 전용 patch 스크립트는 “이전 수정 기록”으로 보관
3. 큰 구조 변경 뒤에는 단순 최신성 비교가 아니라, **과거 hotfix 생존 여부**를 별도로 점검
4. 릴리스 비교가 필요할 때는 `scripts/compare_release_folders.py`를 표준 도구로 사용
5. 구조 변경 뒤에는 smoke와 exhaustive sweep을 함께 사용
