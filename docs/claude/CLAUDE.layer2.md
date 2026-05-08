# CLAUDE.layer2.md — LAYER 2 작업 상세 가이드

> **로드 시점:** P4 / P5 / P7~P10 작업 진행 시
> **작성:** 2026-05-08 — Ruby (Senior Software Architect Mode)

---

## 🎯 LAYER 2 목적

LAYER 1 (어제 완료, P1/P2/P3/P11) → 부팅 15.7초 → 0.3초 단축
LAYER 2 → **운영 안정성** 강화

| 작업 | 목적 | 위험도 | 시간 |
|---|---|:---:|:---:|
| P4 Mutex | 이중 실행 방지 | 🟢 LOW | ✅ 완료 |
| P5 Heartbeat | 백엔드 silent fail 감지 | 🟢 LOW | 10분 |
| P7 sqm-inline.js 가드 | listener 누적 방지 | 🟡 MED | 8분 |
| P8 sqm-tonbag.js 가드 | listener 누적 방지 | 🟡 MED | 8분 |
| P9 sqm-core.js 가드 | listener 누적 방지 | 🟡 MED | P5와 통합 |
| P10 sqm-onestop-inbound.js 가드 | listener 누적 방지 | 🟢 LOW | 5분 |

**합계: 약 31분 (P4 제외)**

---

## ✅ P4 — 단일 인스턴스 락 (구현 완료)

**파일:** `main_webview.py` 라인 67-78
**상태:** 어제 LAYER 1 시점에 함께 적용됨

```python
_MUTEX_NAME = "SQM_Inventory_SingleInstance_v867"

def _acquire_single_instance_lock():
    mutex = _ctypes.windll.kernel32.CreateMutexW(None, True, _MUTEX_NAME)
    last_err = _ctypes.windll.kernel32.GetLastError()
    if last_err == 183:  # ERROR_ALREADY_EXISTS
        _ctypes.windll.kernel32.CloseHandle(mutex)
        return False
    return True

def main():
    if not _acquire_single_instance_lock():
        sys.exit(0)  # 두 번째 인스턴스 조용히 종료
```

**검증:**
```powershell
Start-Process python -ArgumentList "main_webview.py"
Start-Sleep 8
Start-Process python -ArgumentList "main_webview.py"  # 즉시 종료되어야
Get-Process python | Format-Table Id, ProcessName, StartTime
# Python 프로세스 1개만 살아있어야 함
```

---

## 🔧 P5 — JS Heartbeat (다음 작업)

**파일:** `frontend/js/sqm-core.js` 하단에 IIFE 추가
**목적:** FastAPI 백엔드 silent fail 시 15초 안에 빨간 배너 표시

**핵심 코드 패턴:**
```javascript
(function() {
  if (window.__SQM_HEARTBEAT_INSTALLED__) return;
  window.__SQM_HEARTBEAT_INSTALLED__ = true;

  var HEALTH_URL = '/api/health';
  var INTERVAL_MS = 15000;
  var FAIL_COUNT = 0, MAX_FAIL = 2;
  var _banner = null;

  function showOfflineBanner() { /* 빨간 배너 DOM 삽입 */ }
  function hideOfflineBanner() { /* DOM 제거 */ }
  function checkHealth() {
    fetch(HEALTH_URL, {method:'GET',cache:'no-store'})
      .then(r => { if (r.ok) { FAIL_COUNT=0; hideOfflineBanner(); }
                   else { FAIL_COUNT++; if (FAIL_COUNT>=MAX_FAIL) showOfflineBanner(); }})
      .catch(() => { FAIL_COUNT++; if (FAIL_COUNT>=MAX_FAIL) showOfflineBanner(); });
  }

  setTimeout(() => { checkHealth(); setInterval(checkHealth, INTERVAL_MS); }, 5000);
})();
```

**전제 조건:** ✅ `/api/health` 엔드포인트 200 OK 작동 중

---

## 🔧 P7~P10 — JS 가드 (대기)

각 파일 IIFE 진입부에 idempotency guard 추가:

| 우선순위 | 파일 | 가드 변수 | listener 수 |
|:---:|---|---|:---:|
| P7 | `sqm-inline.js` | `__SQM_INLINE_INSTALLED__` | 119개 |
| P8 | `sqm-tonbag.js` | `__SQM_TONBAG_INSTALLED__` | 93개 |
| P9 | `sqm-core.js` | `__SQM_CORE_INSTALLED__` | 21개 (P5 통합) |
| P10 | `sqm-onestop-inbound.js` | `__SQM_ONESTOP_INSTALLED__` | 16개 |

**패턴:**
```javascript
(function() {
  if (window.__SQM_INLINE_INSTALLED__) return;
  window.__SQM_INLINE_INSTALLED__ = true;
  // ... 나머지 코드
})();
```

---

## 🛡 6-Pass 검증 SOP

각 패치마다:
1. **1차** 구현 + 자가 검증
2. **2차** 독립 재감사 (별도 sub-agent)
3. **3차** 전수검사 (py_compile + node --check)
4. **4차** 스트레스 테스트
5. **5차** 통합 검증
6. **6차** 배포 직전 점검

보고서: `REPORT_{1차~6차}_YYYY-MM-DD.md`

---

## 🚨 롤백 명령

```powershell
cd D:\program\SQM_inventory\SQM_v867_clean
git reset --hard pre-p4-20260508          # 발견 ①② 직후
git reset --hard pre-layer2-20260508      # LAYER 1 직후
```
