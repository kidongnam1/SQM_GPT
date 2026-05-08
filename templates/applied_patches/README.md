# Applied Patches — v8.6.7

> **자산화 일자:** 2026-05-08
> **출처:** SQM v8.6.7 LAYER 2/3 작업
> **목적:** 다음 v868 마이그레이션 시 패턴 재사용

---

## 패치 목록

| 파일 | 적용 시점 | 내용 |
|---|---|---|
| `patch_p4.py` | 2026-05-07 (90be151) | P4 — Win32 Mutex 단일 인스턴스 락 |
| `patch_p5_p9.py` | 2026-05-07 (90be151) | P5 + P9 — sqm-core.js Heartbeat + 가드 |
| `patch_p7_p8_p10.py` | 2026-05-07 (90be151) | P7+P8+P10 — sqm-inline/tonbag/onestop 가드 |
| `patch_title_transfer_date.py` | 2026-05-07 (c83aac0) | 라벨 변경 (피킹일 → Title Transfer Date) |

## 공통 특징

각 패치는 **멱등성(idempotency) 가드**를 내장합니다:
```python
if '_MUTEX_NAME' in content:
    print("이미 적용됨 — 건너뜀")
    raise SystemExit(0)
```

→ 여러 번 실행해도 안전. 이미 적용된 경우 자동 skip.

## 사용 방법 (재실행 필요 시)

```powershell
cd D:\program\SQM_inventory\SQM_v867_clean
python templates\applied_patches\patch_p4.py
python templates\applied_patches\patch_p5_p9.py
python templates\applied_patches\patch_p7_p8_p10.py
python templates\applied_patches\patch_title_transfer_date.py
```

## v868 마이그레이션 시 활용

새 버전(v8.6.8 등)으로 업그레이드할 때:
1. v867 코드를 새 폴더에 복사
2. 이 폴더의 4개 패치 다시 실행
3. 멱등성 가드 덕분에 안전 (이미 적용 시 skip)
4. node --check + py_compile 전수검사

---

**Ruby (Senior Software Architect Mode) — 패치 자산화 — 2026-05-08**
