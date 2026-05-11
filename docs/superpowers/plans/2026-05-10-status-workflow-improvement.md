# SQM Status Workflow 개선 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `PENDING` 입고 대기 워크플로우 추가 + `OUTBOUND` 제거하고 `SOLD` 하나로 통일

**Architecture:**
- Phase 1 (단일 에이전트): DB 컬럼 추가 → PENDING 상태 → 입고 확정 API → Dashboard 필터
- Phase 2-A (서브에이전트 A): 백엔드 Python 파일 OUTBOUND→SOLD 일괄 변환
- Phase 2-B (서브에이전트 B): 프론트엔드 JS 파일 OUTBOUND→SOLD 일괄 변환
- Phase 2-A와 2-B는 공유 파일 없으므로 병렬 실행 가능

**Tech Stack:** Python 3.11 · FastAPI · SQLite WAL · Vanilla JS

**Rule 5 적용 대상:** 300줄↑ 파일은 Edit 툴 금지 → Python 스크립트로 수정

---

## 최종 STATUS 6개 (확정)

```
PENDING   → 포트 입항, 창고 미반입 (파싱 직후 자동 배정)
AVAILABLE → 창고 반입 확정 (재고로 집계 시작)
RESERVED  → 배정됨
PICKED    → 출고 작업 중 (취소 가능)
SOLD      → 차량 출발 = 거래 종료 (취소 불가, OUTBOUND 흡수)
RETURN    → 반품
```

---

## 파일 수정 목록

### Phase 1
| 파일 | 작업 |
|------|------|
| `backend/api/inbound.py` | DB 컬럼 추가 마이그레이션, LOT 생성 시 status=PENDING, port_date 저장, 새 엔드포인트 2개 추가 |
| `backend/api/dashboard.py` | 재고 집계 쿼리에서 PENDING 제외 (6곳) |

### Phase 2-A (백엔드 Python)
| 파일 | OUTBOUND 건수 | 방법 |
|------|-------------|------|
| `engine_modules/inventory_modular/outbound_mixin.py` | 73 | Python 스크립트 |
| `engine_modules/constants.py` | 19 | Python 스크립트 |
| `backend/api/outbound_api.py` | 12 | Python 스크립트 |
| `backend/api/actions2.py` | 10 | Python 스크립트 |
| `backend/api/allocation_api.py` | 8 | Python 스크립트 |
| `core/barcode_scan_engine.py` | 8 | Python 스크립트 |
| `core/constants.py` | 8 | Python 스크립트 |
| `backend/api/dashboard.py` | 7 | Python 스크립트 |
| `backend/api/queries.py` | 7 | Python 스크립트 |
| `engine_modules/inventory_modular/export_mixin.py` | 5 | Python 스크립트 |
| `engine_modules/inventory_modular/return_mixin.py` | 13 | Python 스크립트 |
| `backend/api/queries2.py` | 4 | Python 스크립트 |
| `backend/api/scan_api.py` | 3 | Python 스크립트 |
| `backend/api/inventory_api.py` | 3 | Python 스크립트 |
| `backend/api/queries3.py` | 2 | Python 스크립트 |
| `backend/api/info.py` | 1 | Edit |
| `engine_modules/preflight.py` | 9 | Python 스크립트 |
| `engine_modules/inventory_modular/query_mixin.py` | 11 | Python 스크립트 |
| `features/parsers/sales_order_engine.py` | 10 | Python 스크립트 |
| `gui_app_modular/tabs/allocation_tab.py` | 20 | Python 스크립트 |
| 기타 gui_app_modular 파일들 | 다수 | Python 스크립트 |

### Phase 2-B (프론트엔드 JS)
| 파일 | OUTBOUND 건수 | 방법 |
|------|-------------|------|
| `frontend/js/sqm-inline.js` | 21 | Python 스크립트 |
| `frontend/js/sqm-allocation.js` | 9 | Python 스크립트 |
| `frontend/js/sqm-tonbag.js` | 9 | Python 스크립트 |
| `frontend/js/sqm-logistics.js` | 6 | Python 스크립트 |
| `frontend/js/sqm-inventory.js` | 3 | Python 스크립트 |
| `frontend/js/sqm-picked.js` | 1 | Edit |

---

## Phase 1 — PENDING 입고 워크플로우

### Task 1: DB 컬럼 추가 마이그레이션

**Files:**
- Modify: `backend/api/inbound.py:1355-1389` (`_ensure_do_authority_columns` 함수)

- [ ] **Step 1: 기존 마이그레이션 함수 확인**

```bash
grep -n "ensure_do_authority\|port_date\|inbound_type" backend/api/inbound.py
```

Expected: `_ensure_do_authority_columns` 함수가 1355번줄 근처에 있고, `port_date`/`inbound_type` 은 없음

- [ ] **Step 2: `_ensure_do_authority_columns` 에 컬럼 2개 추가**

`backend/api/inbound.py` 의 `_ensure_do_authority_columns` 함수 내, 기존 `if "do_updated_at" not in cols:` 블록 **아래** 에 추가:

```python
    if "port_date" not in cols:
        alter_sql.append("ALTER TABLE inventory ADD COLUMN port_date TEXT DEFAULT ''")
    if "inbound_type" not in cols:
        alter_sql.append("ALTER TABLE inventory ADD COLUMN inbound_type TEXT DEFAULT 'DIRECT'")
```

- [ ] **Step 3: DB에 컬럼이 추가됐는지 확인**

```python
# 임시 검증 (터미널에서 실행)
python -c "
import sqlite3
conn = sqlite3.connect('data/db/sqm_inventory.db')
cols = [r[1] for r in conn.execute('PRAGMA table_info(inventory)').fetchall()]
print('port_date' in cols, 'inbound_type' in cols)
conn.close()
"
```

Expected: `True True`
(마이그레이션 함수는 서버 시작 시 자동 호출되므로, 서버를 한 번 기동하거나 직접 호출해야 함)

---

### Task 2: 파싱 시 status=PENDING, port_date 저장

**Files:**
- Modify: `backend/api/inbound.py` (LOT 생성 common dict 부분, ~1194-1207줄)

- [ ] **Step 1: LOT 생성 위치 확인**

```bash
grep -n "common = {" backend/api/inbound.py
```

Expected: 1195번줄 근처에 `common = {` 블록 확인

- [ ] **Step 2: common dict에 `status`, `port_date` 추가**

`backend/api/inbound.py` 의 `common = {` 블록 (1195줄 근처) 에서
`"arrival_date": getattr(parsed, "arrival_date", None),` 줄 **바로 아래** 에 추가:

```python
                        "status":           "PENDING",
                        "port_date":        datetime.now().strftime("%Y-%m-%d"),
                        "inbound_type":     "DIRECT",
```

> **주의:** `datetime` 은 이미 import 되어 있음 (`from datetime import datetime`). 없으면 상단 import 확인.

- [ ] **Step 3: OneStop 입고 경로도 동일하게 적용**

```bash
grep -n "add_inventory_from_dict\|onestop.*save\|save.*onestop" backend/api/inbound.py
```

OneStop 경로에서도 LOT를 생성하는 곳이 있으면 동일하게 `"status": "PENDING"`, `"port_date"` 추가.

- [ ] **Step 4: py_compile 검사**

```bash
python -m py_compile backend/api/inbound.py && echo OK
```

Expected: `OK`

---

### Task 3: GET /api/inbound/pending 엔드포인트 추가

**Files:**
- Modify: `backend/api/inbound.py` (파일 끝 또는 라우터 정의 마지막 부분)

- [ ] **Step 1: 라우터 변수명 확인**

```bash
grep -n "^router = \|^router=" backend/api/inbound.py | head -3
```

Expected: `router = APIRouter(...)` 형태로 선언된 줄 확인 후 변수명 메모

- [ ] **Step 2: 엔드포인트 추가**

`backend/api/inbound.py` 파일 맨 끝에 추가:

```python
# ── PENDING 입고 대기 목록 ─────────────────────────────────────────
@router.get("/pending", summary="📋 입고 대기 목록 (창고 미반입)")
def get_pending_inbound():
    """PENDING 상태 LOT 목록 반환 — 포트 입항 후 창고 미반입 화물."""
    try:
        db = _db()
        rows = db.execute("""
            SELECT lot_no, product, net_weight, port_date, inbound_type,
                   arrival_date, bl_no, vessel, created_at
            FROM inventory
            WHERE status = 'PENDING'
            ORDER BY COALESCE(port_date, created_at) DESC
        """).fetchall()
        db.close()
        return {"success": True, "data": [dict(r) for r in rows], "count": len(rows)}
    except Exception as e:
        logger.error(f"GET /pending error: {e}")
        raise HTTPException(500, str(e))
```

> `_db()` 와 `logger` 가 파일 상단에 이미 정의돼 있는지 확인. 없으면 파일 내 동일 패턴으로 사용 중인 함수명 확인 후 맞춤.

- [ ] **Step 3: py_compile 검사**

```bash
python -m py_compile backend/api/inbound.py && echo OK
```

Expected: `OK`

---

### Task 4: POST /api/inbound/confirm/{lot_no} 엔드포인트 추가

**Files:**
- Modify: `backend/api/inbound.py` (Task 3 추가 바로 아래)

- [ ] **Step 1: 엔드포인트 추가**

Task 3에서 추가한 `get_pending_inbound` 함수 바로 아래에 추가:

```python
# ── PENDING → AVAILABLE 입고 확정 ────────────────────────────────
@router.post("/confirm/{lot_no}", summary="✅ 입고 확정 (PENDING → AVAILABLE)")
def confirm_inbound(lot_no: str, payload: dict = {}):
    """
    PENDING → AVAILABLE 전환. 창고 실물 반입 확정 시 호출.

    payload:
      inbound_date: str  (YYYY-MM-DD, 생략 시 오늘)
      inbound_type: str  'DIRECT'(당일 직반입) | 'BOND'(보세대기 후 반입)
    """
    inbound_date = (payload.get("inbound_date") or "").strip()
    if not inbound_date:
        inbound_date = datetime.now().strftime("%Y-%m-%d")
    inbound_type = payload.get("inbound_type", "DIRECT")
    if inbound_type not in ("DIRECT", "BOND"):
        raise HTTPException(400, "inbound_type 은 'DIRECT' 또는 'BOND' 만 허용")
    try:
        db = _db()
        row = db.execute(
            "SELECT id, status FROM inventory WHERE lot_no=?", (lot_no,)
        ).fetchone()
        if not row:
            db.close()
            raise HTTPException(404, f"{lot_no} 없음")
        if dict(row)["status"] != "PENDING":
            db.close()
            raise HTTPException(
                400, f"{lot_no}: PENDING 상태가 아님 (현재: {dict(row)['status']})"
            )
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        db.execute("""
            UPDATE inventory
            SET status='AVAILABLE', inbound_date=?, inbound_type=?, updated_at=?
            WHERE lot_no=? AND status='PENDING'
        """, (inbound_date, inbound_type, ts, lot_no))
        db.execute("""
            UPDATE inventory_tonbag
            SET status='AVAILABLE', updated_at=?
            WHERE lot_no=? AND status='PENDING'
        """, (ts, lot_no))
        db.commit()
        db.close()
        logger.info(f"[confirm-inbound] {lot_no} → AVAILABLE (type={inbound_type}, date={inbound_date})")
        return {
            "success": True,
            "lot_no": lot_no,
            "inbound_date": inbound_date,
            "inbound_type": inbound_type,
            "message": f"{lot_no} → AVAILABLE 입고 확정 완료",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"POST /confirm/{lot_no} error: {e}")
        raise HTTPException(500, str(e))
```

- [ ] **Step 2: py_compile 검사**

```bash
python -m py_compile backend/api/inbound.py && echo OK
```

Expected: `OK`

---

### Task 5: Dashboard — PENDING 재고 집계 제외

**Files:**
- Modify: `backend/api/dashboard.py` (64줄, 73줄, 147줄, 209줄, 243줄, 274줄)

- [ ] **Step 1: PENDING 제외가 필요한 줄 확인**

```bash
grep -n "NOT IN\|status IN\|status =" backend/api/dashboard.py | grep -v "#"
```

- [ ] **Step 2: 재고 집계 쿼리 6곳에 'PENDING' 추가**

아래 6개 패턴을 찾아 `PENDING` 추가:

| 위치 | Before | After |
|------|--------|-------|
| 64줄 | `NOT IN ('SOLD', 'RETURNED', 'OUTBOUND')` | `NOT IN ('SOLD', 'RETURNED', 'OUTBOUND', 'PENDING')` |
| 73줄 | `NOT IN ('SOLD', 'RETURNED', 'OUTBOUND')` | `NOT IN ('SOLD', 'RETURNED', 'OUTBOUND', 'PENDING')` |
| 243줄 | `status IN ('AVAILABLE', 'RESERVED', 'PICKED', 'RETURN')` | 변경 없음 (이미 PENDING 미포함) |
| 274줄 | `status IN ('AVAILABLE', 'RESERVED', 'PICKED', 'RETURN')` | 변경 없음 (이미 PENDING 미포함) |

> `dashboard.py` 는 200줄 미만이므로 Edit 툴 사용 가능.

- [ ] **Step 3: py_compile 검사**

```bash
python -m py_compile backend/api/dashboard.py && echo OK
```

Expected: `OK`

---

### Task 6: Phase 1 검증 및 커밋

- [ ] **Step 1: 전체 py_compile 검사**

```bash
python -m py_compile backend/api/inbound.py backend/api/dashboard.py && echo ALL_OK
```

- [ ] **Step 2: API 동작 확인 (서버 기동 후)**

```bash
# 서버 기동
python -m uvicorn backend.main:app --port 8765 --reload

# 다른 터미널에서
curl http://localhost:8765/api/inbound/pending
# Expected: {"success": true, "data": [], "count": 0}

curl -X POST http://localhost:8765/api/inbound/confirm/NONEXISTENT
# Expected: 404 error
```

- [ ] **Step 3: 커밋 (Windows CMD에서)**

```cmd
git add backend/api/inbound.py backend/api/dashboard.py
git commit -m "feat: PENDING 입고 워크플로우 추가 (port_date/inbound_type 컬럼, /pending /confirm API)"
```

---

## Phase 2-A — OUTBOUND → SOLD 백엔드 Python (서브에이전트 A)

> **서브에이전트 A 전용.** Phase 1 완료 후 실행. JS 파일(Phase 2-B)과 충돌 없음.

### Task 7: 변환 스크립트 생성 및 실행

**Files:**
- Create: `scripts/migrate_outbound_to_sold.py`
- Modify: 위 파일 목록의 Python 파일 전체

- [ ] **Step 1: 변환 스크립트 작성**

`scripts/migrate_outbound_to_sold.py` 생성:

```python
"""
OUTBOUND → SOLD 상태 통합 마이그레이션 스크립트
실행: python scripts/migrate_outbound_to_sold.py
"""
import re
import os

# 수정 대상 Python 파일 (상대 경로)
TARGET_FILES = [
    "engine_modules/inventory_modular/outbound_mixin.py",
    "engine_modules/inventory_modular/return_mixin.py",
    "engine_modules/inventory_modular/query_mixin.py",
    "engine_modules/inventory_modular/export_mixin.py",
    "engine_modules/constants.py",
    "engine_modules/preflight.py",
    "engine_modules/audit_helper.py",
    "engine_modules/return_reinbound_engine.py",
    "core/barcode_scan_engine.py",
    "core/constants.py",
    "features/parsers/sales_order_engine.py",
    "features/parsers/picking_list_parser.py",
    "features/parsers/return_inbound_engine.py",
    "backend/api/outbound_api.py",
    "backend/api/actions2.py",
    "backend/api/allocation_api.py",
    "backend/api/dashboard.py",
    "backend/api/queries.py",
    "backend/api/queries2.py",
    "backend/api/queries3.py",
    "backend/api/scan_api.py",
    "backend/api/inventory_api.py",
    "backend/api/info.py",
    "backend/api/actions.py",
    "backend/api/actions3.py",
    "backend/api/__init__.py",
    "gui_app_modular/tabs/allocation_tab.py",
    "gui_app_modular/tabs/dashboard_data_mixin.py",
    "gui_app_modular/tabs/inventory_tab.py",
    "gui_app_modular/tabs/scan_tab.py",
    "gui_app_modular/tabs/outbound_scheduled_tab.py",
    "gui_app_modular/tabs/sold_tab.py",
    "gui_app_modular/handlers/outbound_handlers.py",
    "gui_app_modular/handlers/status_import_handlers.py",
    "gui_app_modular/dialogs/lot_status_dialog.py",
    "gui_app_modular/dialogs/onestop_outbound.py",
    "gui_app_modular/mixins/advanced_features_mixin.py",
    "gui_app_modular/mixins/custom_menubar.py",
    "gui_app_modular/mixins/menu_mixin.py",
    "gui_app_modular/mixins/toolbar_mixin.py",
    "parsers/allocation_parser.py",
    "parsers/document_models.py",
    "config.py",
    "version.py",
]

def replace_outbound_status(text: str) -> str:
    """
    STATUS 값으로 쓰인 OUTBOUND 만 SOLD 로 교체.
    URL 경로(/outbound/), 함수명(outbound_handlers), 상수명(QUICK_OUTBOUND_MAX_TONBAGS) 은 유지.
    """
    # 1. SQL SET status='OUTBOUND' → SET status='SOLD'
    text = re.sub(r"(SET\s+status\s*=\s*)'OUTBOUND'", r"\1'SOLD'", text)
    text = re.sub(r'(SET\s+status\s*=\s*)"OUTBOUND"', r'\1"SOLD"', text)

    # 2. Python 대입 status='OUTBOUND' / status="OUTBOUND"
    text = re.sub(r"(status\s*=\s*)'OUTBOUND'", r"\1'SOLD'", text)
    text = re.sub(r'(status\s*=\s*)"OUTBOUND"', r'\1"SOLD"', text)

    # 3. SQL IN 절에서 중복 제거: ('SOLD', 'OUTBOUND') → ('SOLD')
    text = re.sub(r"'SOLD',\s*'OUTBOUND'", "'SOLD'", text)
    text = re.sub(r"'OUTBOUND',\s*'SOLD'", "'SOLD'", text)
    # IN 절 끝에 붙은 경우: IN ('SOLD', 'OUTBOUND', 'CONFIRMED') → IN ('SOLD', 'CONFIRMED')
    text = re.sub(r",\s*'OUTBOUND'(\s*[,\)])", r"\1", text)
    text = re.sub(r"'OUTBOUND',\s*", "", text)

    # 4. Python set/list 에서 중복 제거
    text = re.sub(r'"SOLD",\s*"OUTBOUND"', '"SOLD"', text)
    text = re.sub(r'"OUTBOUND",\s*"SOLD"', '"SOLD"', text)
    text = re.sub(r',\s*"OUTBOUND"(\s*[,}\]])', r'\1', text)
    text = re.sub(r'"OUTBOUND",\s*', '', text)

    # 5. == / != / in 비교
    text = re.sub(r"(==\s*)'OUTBOUND'", r"\1'SOLD'", text)
    text = re.sub(r'(==\s*)"OUTBOUND"', r'\1"SOLD"', text)
    text = re.sub(r"(!=\s*)'OUTBOUND'", r"\1'SOLD'", text)
    text = re.sub(r'(!=\s*)"OUTBOUND"', r'\1"SOLD"', text)

    # 6. event_type OUTBOUND_SOLD → SOLD
    text = text.replace("OUTBOUND_SOLD", "SOLD")
    text = text.replace('"OUTBOUND_SOLD"', '"SOLD"')
    text = text.replace("'OUTBOUND_SOLD'", "'SOLD'")

    return text

def process_file(path: str) -> bool:
    if not os.path.exists(path):
        print(f"  SKIP (없음): {path}")
        return False
    with open(path, encoding="utf-8") as f:
        original = f.read()
    updated = replace_outbound_status(original)
    if original == updated:
        print(f"  NO CHANGE: {path}")
        return False
    with open(path, "w", encoding="utf-8") as f:
        f.write(updated)
    changed = sum(1 for a, b in zip(original.splitlines(), updated.splitlines()) if a != b)
    print(f"  UPDATED ({changed}줄 변경): {path}")
    return True

if __name__ == "__main__":
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(root)
    print(f"작업 디렉토리: {root}\n")
    total_changed = 0
    for rel_path in TARGET_FILES:
        if process_file(rel_path):
            total_changed += 1
    print(f"\n완료: {total_changed}/{len(TARGET_FILES)} 파일 수정됨")
```

- [ ] **Step 2: 스크립트 실행 (dry-run 먼저 확인)**

```bash
# 실행 전 git status 확인
git status

# 스크립트 실행
python scripts/migrate_outbound_to_sold.py
```

Expected: 다수 파일에 `UPDATED` 출력

- [ ] **Step 3: 변환 결과 확인 — OUTBOUND가 남아 있는지 점검**

```bash
python -c "
import subprocess, re
result = subprocess.run(
    ['python', '-c',
     '''
import os, re
for root, dirs, files in os.walk('.'):
    dirs[:] = [d for d in dirs if d not in ['.git','__pycache__','.bkit','scripts']]
    for f in files:
        if f.endswith('.py'):
            path = os.path.join(root, f)
            text = open(path, encoding='utf-8', errors='ignore').read()
            hits = [(i+1, l.strip()) for i,l in enumerate(text.splitlines())
                    if re.search(r\"['\\\"]OUTBOUND['\\\"]|status.*OUTBOUND\", l)]
            if hits:
                print(path)
                for ln, line in hits[:3]:
                    print(f'  {ln}: {line}')
     '''],
    capture_output=True, text=True
)
print(result.stdout[:3000] if result.stdout else 'No remaining OUTBOUND status references')
"
```

Expected: 남은 OUTBOUND 상태 참조가 없거나 최소화

- [ ] **Step 4: 전체 py_compile 검사**

```bash
python -c "
import os, py_compile, sys
errors = []
for root, dirs, files in os.walk('.'):
    dirs[:] = [d for d in dirs if d not in ['.git','__pycache__','.bkit']]
    for f in files:
        if f.endswith('.py'):
            path = os.path.join(root, f)
            try:
                py_compile.compile(path, doraise=True)
            except py_compile.PyCompileError as e:
                errors.append(str(e))
if errors:
    print('ERRORS:')
    for e in errors: print(e)
    sys.exit(1)
else:
    print('ALL OK')
"
```

Expected: `ALL OK`

- [ ] **Step 5: 수동 확인 — 주요 파일 핵심 부분 점검**

```bash
# outbound_api.py: 출고 확정이 SOLD 로 바뀌었는지
grep -n "status='SOLD'\|status=\"SOLD\"" backend/api/outbound_api.py | head -10

# scan_api.py: OUTBOUND 참조 제거 확인
grep -n "OUTBOUND" backend/api/scan_api.py

# dashboard.py: IN 절 확인
grep -n "OUTBOUND" backend/api/dashboard.py
```

- [ ] **Step 6: 커밋 (Windows CMD에서)**

```cmd
git add -u
git commit -m "refactor: OUTBOUND status → SOLD 통합 (백엔드 Python)"
```

---

## Phase 2-B — OUTBOUND → SOLD 프론트엔드 JS (서브에이전트 B)

> **서브에이전트 B 전용.** Phase 1 완료 후 실행. Python 파일(Phase 2-A)과 충돌 없음.

### Task 8: JS 파일 변환 스크립트 생성 및 실행

**Files:**
- Create: `scripts/migrate_outbound_to_sold_js.py`
- Modify: `frontend/js/sqm-inline.js`, `sqm-allocation.js`, `sqm-tonbag.js`, `sqm-logistics.js`, `sqm-inventory.js`, `sqm-picked.js`

- [ ] **Step 1: JS 변환 스크립트 작성**

`scripts/migrate_outbound_to_sold_js.py` 생성:

```python
"""
JS 파일 OUTBOUND → SOLD 상태 통합 마이그레이션
실행: python scripts/migrate_outbound_to_sold_js.py
"""
import re, os

TARGET_FILES = [
    "frontend/js/sqm-inline.js",
    "frontend/js/sqm-allocation.js",
    "frontend/js/sqm-tonbag.js",
    "frontend/js/sqm-logistics.js",
    "frontend/js/sqm-inventory.js",
    "frontend/js/sqm-picked.js",
]

def replace_outbound_js(text: str) -> str:
    # 1. 문자열 비교/대입: 'OUTBOUND' / "OUTBOUND"
    text = re.sub(r"=== 'OUTBOUND'", "=== 'SOLD'", text)
    text = re.sub(r'=== "OUTBOUND"', '=== "SOLD"', text)
    text = re.sub(r"!== 'OUTBOUND'", "!== 'SOLD'", text)
    text = re.sub(r'!== "OUTBOUND"', '!== "SOLD"', text)
    text = re.sub(r"= 'OUTBOUND'", "= 'SOLD'", text)
    text = re.sub(r'= "OUTBOUND"', '= "SOLD"', text)

    # 2. 배열/includes 내 중복 제거
    text = re.sub(r"'SOLD',\s*'OUTBOUND'", "'SOLD'", text)
    text = re.sub(r"'OUTBOUND',\s*'SOLD'", "'SOLD'", text)
    text = re.sub(r'"SOLD",\s*"OUTBOUND"', '"SOLD"', text)
    text = re.sub(r'"OUTBOUND",\s*"SOLD"', '"SOLD"', text)
    text = re.sub(r",\s*'OUTBOUND'(\s*[,\]\)])", r"\1", text)
    text = re.sub(r"'OUTBOUND',\s*", "", text)
    text = re.sub(r',\s*"OUTBOUND"(\s*[,\]\)])', r'\1', text)
    text = re.sub(r'"OUTBOUND",\s*', '', text)

    # 3. includes('OUTBOUND') 패턴
    text = re.sub(r"includes\('OUTBOUND'\)", "includes('SOLD')", text)
    text = re.sub(r'includes\("OUTBOUND"\)', 'includes("SOLD")', text)

    # 4. CSS 클래스나 label 문자열 (label: 'outbound' → 'sold')
    text = re.sub(r"label:\s*'출고완료'", "label: '판매완료'", text)
    text = re.sub(r'label:\s*"출고완료"', 'label: "판매완료"', text)

    # 5. OUTBOUND_SOLD 이벤트명
    text = text.replace("OUTBOUND_SOLD", "SOLD")

    return text

def process_file(path: str) -> bool:
    if not os.path.exists(path):
        print(f"  SKIP (없음): {path}")
        return False
    with open(path, encoding="utf-8") as f:
        original = f.read()
    updated = replace_outbound_js(original)
    if original == updated:
        print(f"  NO CHANGE: {path}")
        return False
    with open(path, "w", encoding="utf-8") as f:
        f.write(updated)
    changed = sum(1 for a, b in zip(original.splitlines(), updated.splitlines()) if a != b)
    print(f"  UPDATED ({changed}줄 변경): {path}")
    return True

if __name__ == "__main__":
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(root)
    print(f"작업 디렉토리: {root}\n")
    total = sum(1 for p in TARGET_FILES if process_file(p))
    print(f"\n완료: {total}/{len(TARGET_FILES)} 파일 수정됨")
```

- [ ] **Step 2: 스크립트 실행**

```bash
python scripts/migrate_outbound_to_sold_js.py
```

- [ ] **Step 3: 남은 OUTBOUND 확인**

```bash
python -c "
import os, re
for f in ['frontend/js/sqm-inline.js','frontend/js/sqm-allocation.js',
          'frontend/js/sqm-tonbag.js','frontend/js/sqm-logistics.js',
          'frontend/js/sqm-inventory.js','frontend/js/sqm-picked.js']:
    if not os.path.exists(f): continue
    text = open(f, encoding='utf-8').read()
    hits = [(i+1, l.strip()) for i,l in enumerate(text.splitlines())
            if 'OUTBOUND' in l and not l.strip().startswith('//')]
    if hits:
        print(f'{f}:')
        for ln, line in hits[:5]:
            print(f'  {ln}: {line}')
"
```

Expected: 출력 없음 (또는 URL 경로처럼 status 값이 아닌 것만)

- [ ] **Step 4: node --check 검사**

```bash
for f in frontend/js/sqm-inline.js frontend/js/sqm-allocation.js frontend/js/sqm-tonbag.js frontend/js/sqm-logistics.js frontend/js/sqm-inventory.js; do
  node --check $f && echo "OK: $f"
done
```

Expected: 모든 파일 `OK`

- [ ] **Step 5: 커밋 (Windows CMD에서)**

```cmd
git add frontend/js/sqm-inline.js frontend/js/sqm-allocation.js frontend/js/sqm-tonbag.js frontend/js/sqm-logistics.js frontend/js/sqm-inventory.js frontend/js/sqm-picked.js scripts/migrate_outbound_to_sold_js.py
git commit -m "refactor: OUTBOUND status → SOLD 통합 (프론트엔드 JS)"
```

---

## 최종 검증

- [ ] **py_compile 전수검사**

```bash
python -c "
import os, py_compile, sys
errors = []
for root, dirs, files in os.walk('.'):
    dirs[:] = [d for d in dirs if d not in ['.git','__pycache__','.bkit']]
    for f in files:
        if f.endswith('.py'):
            p = os.path.join(root, f)
            try: py_compile.compile(p, doraise=True)
            except py_compile.PyCompileError as e: errors.append(str(e))
if errors:
    for e in errors: print(e)
    sys.exit(1)
print('ALL OK')
"
```

- [ ] **OUTBOUND 잔존 확인**

```bash
python -c "
import os, re, subprocess
result = []
for root, dirs, files in os.walk('.'):
    dirs[:] = [d for d in dirs if d not in ['.git','__pycache__','.bkit','scripts','docs']]
    for f in files:
        if f.endswith(('.py','.js')):
            path = os.path.join(root, f)
            text = open(path, encoding='utf-8', errors='ignore').read()
            hits = [l.strip() for l in text.splitlines()
                    if re.search(r\"['\\\"]OUTBOUND['\\\"]|status.*OUTBOUND\", l)]
            if hits:
                result.append(f'{path}: {len(hits)}건')
if result:
    print('잔존:')
    for r in result: print(' ', r)
else:
    print('CLEAN — OUTBOUND 상태 참조 없음')
"
```

Expected: `CLEAN — OUTBOUND 상태 참조 없음`

---

## 실행 전략 요약

```
Phase 1 (이 세션, 단일 실행)
  Task 1 → Task 2 → Task 3 → Task 4 → Task 5 → Task 6
  커밋: feat: PENDING 입고 워크플로우

Phase 2 (별도 세션, 병렬 서브에이전트)
  Agent A: Task 7  →  커밋: refactor: OUTBOUND→SOLD 백엔드
  Agent B: Task 8  →  커밋: refactor: OUTBOUND→SOLD 프론트엔드
  두 에이전트 동시 실행 가능 (공유 파일 없음)

최종 검증 (Phase 2 완료 후)
  py_compile 전수검사 + OUTBOUND 잔존 확인
```
