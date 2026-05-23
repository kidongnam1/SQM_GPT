# 릴리스 폴더 비교 보고서

- 생성 시각: 2026-05-17 20:45:43
- 기준(base): `D:\program\SQM_inventory\SQM_v868_claan`
- 대상(target): `D:\program\SQM_inventory\sqm_v869_clean`

## 요약

| 구분 | 개수 |
|---|---:|
| 전체 비교 파일 | 4643 |
| 동일 | 4571 |
| 수정됨 | 23 |
| base에만 존재 | 20 |
| target에만 존재 | 29 |

## 수정된 파일

### `.gitignore`

- 변경량: `+6 / -1`

### `HOW_TO_RUN.md`

- 변경량: `+16 / -0`

```diff
@@ -57,3 +57,19 @@
+
+## Canonical launcher for V869 clean
+
+From this version onward, use **`run_v869_clean.bat`** as the single canonical launcher.
+
+Why this matters:
+- Older copied folders can still run their own `main_webview.py` and silently serve stale frontend assets.
+- If the browser shows an old script version, first verify that the running app was launched from this folder.
+
+Expected runtime root:
+- `D:\program\SQM_inventory\sqm_v869_clean`
+
+Expected verification points after launch:
+- `GET /api/q3/settings-info` should report a DB path under `sqm_v869_clean`.
+- The page should load `sqm-inline.js?v=20260517p26` and the split modal modules.
+
```

### `backend\api\actions3.py`

- 변경량: `+17 / -0`

```diff
@@ -192,6 +192,23 @@
+
+        # 실제 재고 상태 반영 — 이력만 쌓이고 Return 탭에 보이지 않는 상태를 방지
+        con.execute(
+            "UPDATE inventory SET status='RETURN', updated_at=? WHERE lot_no=?",
+            (ts, lot_no),
+        )
+        if tonbag_uid:
+            con.execute(
+                "UPDATE inventory_tonbag SET status='RETURN', updated_at=? "
+                "WHERE lot_no=? AND (tonbag_uid=? OR CAST(sub_lt AS TEXT)=?)",
+                (ts, lot_no, tonbag_uid, tonbag_uid),
+            )
+        else:
+            con.execute(
+                "UPDATE inventory_tonbag SET status='RETURN', updated_at=? WHERE lot_no=?",
+                (ts, lot_no),
+            )
```

### `backend\api\allocation_api.py`

- 변경량: `+101 / -18`

```diff
@@ -55,6 +55,34 @@
+
+
+def _rows_from_canonical_parser(excel_path: str) -> list[dict]:
+    """정본 AllocationParser 결과를 API 입력 행 구조로 변환."""
+    try:
+        from parsers.allocation_parser import AllocationParser
+    except Exception as exc:
+        logger.warning("[allocation-import] 정본 파서 import 실패: %s", exc)
+        return []
+
+    parsed = AllocationParser().parse(excel_path)
+    if not parsed or not parsed.rows:
+        return []
+
+    rows = []
+    for row in parsed.rows:
+        rows.append({
+            "lot_no": row.lot_no,
+            "sold_to": row.sold_to,
+            "customer": row.sold_to,
+            "sale_ref": row.sale_ref,
+            "qty_mt": row.qty_mt,
+            "outbound_date": row.outbound_date.isoformat() if row.outbound_date else None,
+            "sublot_count": row.sublot_count,
+            "is_sample": row.is_sample,
+            "export_type": row.export_type,
+        })
+    return rows
@@ -177,9 +205,16 @@
-        # Stage 2: Gemini AI 폴백 — alias 매핑 실패 시
+        canonical_rows = []
+        # Stage 2: 정본 AllocationParser 폴백 — Song/Jakarta/Woo 등 기존 강한 파서 우선
-            logger.info("[allocation-import] alias 매핑 실패 → Gemini AI 폴백 시도")
+            canonical_rows = _rows_from_canonical_parser(tmp_path)
+            if canonical_rows:
+                logger.info("[allocation-import] alias 매핑 실패 → 정본 AllocationParser 폴백 성공: %d행", len(canonical_rows))
+
+        # Stage 3: Gemini AI 폴백 — alias + 정본 파서 모두 실패 시
+        if (df is None or df.empty) and not canonical_rows:
+            logger.info("[allocation-import] alias/정본 파서 실패 → Gemini AI 폴백 시도")
@@ -195,26 +230,36 @@
-        if df is None or df.empty:
... (이하 생략, 총 +101/-18 줄)
```

### `backend\api\queries.py`

- 변경량: `+2 / -1`

```diff
@@ -418,6 +418,7 @@
+                i.inbound_date,
@@ -445,7 +446,7 @@
-                        "product", "mxbg_pallet", "total_bags", "tb_available",
+                        "product", "mxbg_pallet", "inbound_date", "total_bags", "tb_available",
```

### `frontend\index.html`

- 변경량: `+11 / -5`

```diff
@@ -366,11 +366,11 @@
-  <script src="js/sqm-core.js?v=20260517p21"></script>
+  <script src="js/sqm-core.js?v=20260517p22"></script>
-    <script src="js/sqm-allocation.js?v=20260505a"></script>
-    <script src="js/sqm-picked.js?v=20260517a"></script>
-    <script src="js/sqm-logistics.js?v=20260517a"></script>
+    <script src="js/sqm-allocation.js?v=20260517b"></script>
+    <script src="js/sqm-picked.js?v=20260517b"></script>
+    <script src="js/sqm-logistics.js?v=20260517b"></script>
@@ -379,7 +379,13 @@
-    <script src="js/sqm-inline.js?v=20260517p21"></script>
+    <script src="js/sqm-weight-panel.js?v=20260517b"></script>
+    <script src="js/sqm-settings-templates.js?v=20260517a"></script>
+    <script src="js/sqm-inline.js?v=20260517p29"></script>
+    <script src="js/sqm-upload-modals.js?v=20260517a"></script>
+    <script src="js/sqm-aux-modals.js?v=20260517a"></script>
+    <script src="js/sqm-tools-modals.js?v=20260517a"></script>
+    <script src="js/sqm-product-modals.js?v=20260517a"></script>
```

### `frontend\js\sqm-allocation.js`

- 변경량: `+11 / -79`

```diff
@@ -341,7 +341,7 @@
-        if (res.ok === false) { showToast('warn', res.message || '취소 대상 없음'); }
+        if (res.ok === false) { showToast('warning', res.message || '취소 대상 없음'); }
@@ -352,7 +352,7 @@
-      if (!rows.length) { showToast('warn', 'LOT 현황 데이터 없음'); return; }
+      if (!rows.length) { showToast('warning', 'LOT 현황 데이터 없음'); return; }
@@ -388,84 +388,12 @@
-        if (res.ok === false) { showToast('warn', res.message || '되돌릴 대상 없음'); }
+        if (res.ok === false) { showToast('warning', res.message || '되돌릴 대상 없음'); }
-
-  /* ── 전체 초기화 ── */
-  window.allocResetAll = function() {
-    if (!sqmConfirm('⚠️ 전체 초기화\n\n모든 RESERVED/PICKED/OUTBOUND 배정을 취소하고 AVAILABLE로 원복합니다.\n(SOLD는 보호됩니다)\n\n계속하시겠습니까?')) return;
-    apiPost('/api/allocation/reset-all', {})
-      .then(function(res){
-        showToast('success', '⚠️ ' + (res.message || '전체 초기화 완료'));
-        loadAllocationPage();
-      })
-      .catch(function(e){ showToast('error', '전체 초기화 실패: ' + (e.message||e)); });
-  };
-
-  /* ── SALE REF 일괄 취소 ── */
-  window.allocCancelBySaleRef = function() {
-    var saleRef = prompt('SALE REF 번호를 입력하세요 (예: SC-2026-001)');
-    if (!saleRef || !saleRef.trim()) return;
-    saleRef = saleRef.trim();
-    if (!sqmConfirm('🔖 SALE REF 취소\n\n"' + saleRef + '" 에 해당하는 모든 배정을 취소하고 AVAILABLE로 원복합니다.\n계속하시겠습니까?')) return;
-    apiPost('/api/allocation/cancel-by-sale-ref', { sale_ref: saleRef })
-      .then(function(res){
-        if (res.ok === false) { showToast('warn', res.message || '취소 대상 없음'); }
-        else { showToast('success', '🔖 ' + (res.message || 'SALE REF 취소 완료')); loadAllocationPage(); }
-      })
-      .catch(function(e){ showToast('error', 'SALE REF 취소 실패: ' + (e.message||e)); });
-  };
-
-  /* ── LOT 현황 팝업 ── */
-  window.allocOpenLotOverview = function() {
-    showToast('info', '📦 LOT 현황 로딩...');
-    apiGet('/api/allocation/lot-overview').then(function(res){
-      var rows = (res.data || []);
-      if (!rows.length) { showToast('warn', 'LOT 현황 데이터 없음'); return; }
-      var lines = rows.map(function(r, i){
-        return (i+1) + '. ' + r.lot_no +
... (이하 생략, 총 +11/-79 줄)
```

### `frontend\js\sqm-core.js`

- 변경량: `+2 / -2`

```diff
@@ -164,7 +164,7 @@
-  var API = 'http://127.0.0.1:8765';
+  var API = window.SQM_API_BASE || (window.location && window.location.origin) || 'http://127.0.0.1:8765';
@@ -602,7 +602,7 @@
-        else { showToast('warn', '이 탭은 Ctrl+Delete 지원 없음'); }
+        else { showToast('warning', '이 탭은 Ctrl+Delete 지원 없음'); }
```

### `frontend\js\sqm-inline.js`

- 변경량: `+158 / -2178`

```diff
@@ -141,7 +141,7 @@
-  var API = 'http://127.0.0.1:8765';
+  var API = window.SQM_API_BASE || (window.location && window.location.origin) || 'http://127.0.0.1:8765';
@@ -339,6 +339,8 @@
+  window.dbgLog = dbgLog;
+
@@ -348,6 +350,7 @@
+  window.extractRows = extractRows;
@@ -765,6 +768,8 @@
+  // sqm-core.js가 이미 getCurrentRoute 권위를 가진다. 없을 때만 레거시 폴백을 둔다.
+  if (typeof window.getCurrentRoute !== 'function') window.getCurrentRoute = function(){ return _currentRoute; };
@@ -797,8 +802,10 @@
-    // P2-1 (2026-05-17): 라우터 단일화 — sqm-core.js가 단일 권위 라우터
-    // 이 함수는 IIFE 내부 호출을 window.renderPage(sqm-core)로 포워딩만 함
+    // P2-1/P2-2 (2026-05-17): sqm-core.js가 권위 라우터지만,
+    // inline 내부의 레거시 비동기 guard들도 아직 _currentRoute를 읽는다.
+    // 포워딩 전에 로컬 미러를 동기화해 기존 guard가 false-negative로 렌더를 막지 않게 한다.
+    _currentRoute = route;
@@ -833,7 +840,7 @@
-      _updateWeightBadge();
+      if (window._updateWeightBadge) window._updateWeightBadge();
@@ -1005,7 +1012,7 @@
-    if (!win) { showToast('warn', '\uD31D\uC5C5 \uCC28\uB2E8\uB428 \u2014 \uBE0C\uB77C\uC6B0\uC800 \uC124\uC815 \uD655\uC778'); return; }
+    if (!win) { showToast('warning', '\uD31D\uC5C5 \uCC28\uB2E8\uB428 \u2014 \uBE0C\uB77C\uC6B0\uC800 \uC124\uC815 \uD655\uC778'); return; }
@@ -1688,7 +1695,7 @@
-    if (typeof showAllocationUploadModal === 'function') { showAllocationUploadModal(); }
+    if (typeof window.showAllocationUploadModal === 'function') { window.showAllocationUploadModal(); }
@@ -1773,7 +1780,7 @@
-        if (res.ok === false) { showToast('warn', res.message || '취소 대상 없음'); }
+        if (res.ok === false) { showToast('warning', res.message || '취소 대상 없음'); }
@@ -1784,7 +1791,7 @@
-      if (!rows.length) { showToast('warn', 'LOT 현황 데이터 없음'); return; }
+      if (!rows.length) { showToast('warning', 'LOT 현황 데이터 없음'); return; }
@@ -1816,80 +1823,12 @@
-        if (res.ok === false) { showToast('warn', res.message || '되돌릴 대상 없음'); }
+        if (res.ok === false) { showToast('warning', res.message || '되돌릴 대상 없음'); }
-
-  /* ── 전체 초기화 ── */
-  window.allocResetAll = function() {
-    if (!sqmConfirm('⚠️ 전체 초기화\n\n모든 RESERVED/PICKED/OUTBOUND 배정을 취소하고 AVAILABLE로 원복합니다.\n(SOLD는 보호됩니다)\n\n계속하시겠습니까?')) return;
-    apiPost('/api/allocation/reset-all', {})
-      .then(function(res){
-        showToast('success', '⚠️ ' + (res.message || '전체 초기화 완료'));
-        loadAllocationPage();
-      })
-      .catch(function(e){ showToast('error', '전체 초기화 실패: ' + (e.message||e)); });
-  };
-
-  /* ── SALE REF 일괄 취소 ── */
-  window.allocCancelBySaleRef = function() {
-    var saleRef = prompt('SALE REF 번호를 입력하세요 (예: SC-2026-001)');
... (이하 생략, 총 +158/-2178 줄)
```

### `frontend\js\sqm-inventory.js`

- 변경량: `+1 / -2`

```diff
@@ -524,7 +524,6 @@
-      var lotJson = JSON.stringify(r.lot_no || '');
@@ -668,7 +667,7 @@
-        html += '<div class="empty" style="padding:60px;text-align:center;color:var(--text-muted);font-size:3em;font-weight:600;line-height:1.4">⏳ 입고 대기 중인 화물 
+        html += '<div class="empty" style="padding:60px;text-align:center;color:var(--text-muted)">⏳ 입고 대기 중인 화물 없음</div></section>';
```

### `frontend\js\sqm-logistics.js`

- 변경량: `+13 / -7`

```diff
@@ -461,7 +461,10 @@
-              window.allocRevertStep('SOLD');
+              apiPost('/api/allocation/revert-step', { from_status: 'SOLD', lot_nos: [lot] }).then(function(){
+                showToast('success', lot + ' SOLD → PICKED 복구 완료');
+                renderPage('sold');
+              });
@@ -470,7 +473,10 @@
-        if (window.allocRevertStep) window.allocRevertStep('SOLD');
+        apiPost('/api/allocation/revert-step', { from_status: 'SOLD', lot_nos: [lot] }).then(function(){
+          showToast('success', lot + ' SOLD → PICKED 복구 완료');
+          renderPage('sold');
+        });
@@ -634,7 +640,7 @@
-      '<input id="move-barcode" class="input" placeholder="Tonbag barcode" style="width:200px">',
+      '<input id="move-lot-no" class="input" placeholder="LOT No" style="width:200px">',
@@ -672,11 +678,11 @@
-    var barcode = (document.getElementById('move-barcode')||{}).value||'';
+    var lotNo = (document.getElementById('move-lot-no')||{}).value||'';
-    if (!barcode||!dest) { showToast('warning','Enter barcode and destination'); return; }
-    apiPost('/api/action/inventory-move',{barcode:barcode,destination:dest})
-      .then(function(){ showToast('success',barcode+' moved to '+dest); renderPage('move'); })
+    if (!lotNo||!dest) { showToast('warning','Enter LOT No and destination'); return; }
+    apiPost('/api/action2/inventory-move',{lot_no:lotNo,destination:dest})
+      .then(function(){ showToast('success',lotNo+' moved to '+dest); renderPage('move'); })
```

### `frontend\js\sqm-onestop-inbound.js`

- 변경량: `+2 / -2`

```diff
@@ -1170,7 +1170,7 @@
-          showToast('warn',
+          showToast('warning',
@@ -1394,7 +1394,7 @@
-      showToast('warn', '파싱된 데이터가 없습니다. ▶ 파싱 시작을 먼저 실행하세요');
+      showToast('warning', '파싱된 데이터가 없습니다. ▶ 파싱 시작을 먼저 실행하세요');
```

### `frontend\js\sqm-picked.js`

- 변경량: `+2 / -2`

```diff
@@ -32,7 +32,7 @@
-    if (!tbl) { if (window.showToast) showToast('warn', '내보낼 테이블이 없습니다'); return; }
+    if (!tbl) { if (window.showToast) showToast('warning', '내보낼 테이블이 없습니다'); return; }
@@ -117,7 +117,7 @@
-    rows.forEach(function(r) {
+    rows.forEach(function(r, _i) {
```

### `frontend\js\sqm-tonbag.js`

- 변경량: `+4 / -4`

```diff
@@ -725,7 +725,7 @@
-    if (!lot || !act) { showToast('warn', 'LOT NO 와 실제(kg) 값 필요'); return; }
+    if (!lot || !act) { showToast('warning', 'LOT NO 와 실제(kg) 값 필요'); return; }
@@ -1017,7 +1017,7 @@
-      showToast('warn', '선택된 톤백이 없습니다');
+      showToast('warning', '선택된 톤백이 없습니다');
@@ -1120,7 +1120,7 @@
-    if (!uid || !act) { showToast('warn', '톤백 ID와 실제(kg) 필요'); return; }
+    if (!uid || !act) { showToast('warning', '톤백 ID와 실제(kg) 필요'); return; }
@@ -1239,7 +1239,7 @@
-    else if (hasWarn) showToast('warn', '⚠️ 일부 편차 — 검토 후 진행');
+    else if (hasWarn) showToast('warning', '⚠️ 일부 편차 — 검토 후 진행');
```

### `logs\sqm_inventory.log`

- 변경량: `+9710 / -2345`

### `package-lock.json`

- 변경량: `+15 / -16`

```diff
@@ -5,24 +5,23 @@
-        "@playwright/test": "^1.44.0",
-        "playwright": "^1.44.0"
+        "@playwright/test": "^1.60.0"
-      "version": "1.44.0",
-      "resolved": "https://registry.npmjs.org/@playwright/test/-/test-1.44.0.tgz",
-      "integrity": "sha512-rNX5lbNidamSUorBhB4XZ9SQTjAqfe5M+p37Z8ic0jPFBMo5iCtQz1kRWkEMg+rYOKSlVycpQmpqjSFq7LXOfg==",
+      "version": "1.60.0",
+      "resolved": "https://registry.npmjs.org/@playwright/test/-/test-1.60.0.tgz",
+      "integrity": "sha512-O71yZIbAh/PxDMNGns37GHBIfrVkEVyn+AXyIa5dOTfb4/xNvRWV+Vv/NMbNCtODB/pO7vLlF2OTmMVLhmr7Ag==",
-        "playwright": "1.44.0"
+        "playwright": "1.60.0"
-        "node": ">=16"
+        "node": ">=18"
@@ -41,35 +40,35 @@
-      "version": "1.44.0",
-      "resolved": "https://registry.npmjs.org/playwright/-/playwright-1.44.0.tgz",
-      "integrity": "sha512-F9b3GUCLQ3Nffrfb6dunPOkE5Mh68tR7zN32L4jCk4FjQamgesGay7/dAAe1WaMEGV04DkdJfcJzjoCKygUaRQ==",
+      "version": "1.60.0",
+      "resolved": "https://registry.npmjs.org/playwright/-/playwright-1.60.0.tgz",
+      "integrity": "sha512-hheHdokM8cdqCb0lcE3s+zT4t4W+vvjpGxsZlDnikarzx8tSzMebh3UiFtgqwFwnTnjYQcsyMF8ei2mCO/tpeA==",
-        "playwright-core": "1.44.0"
+        "playwright-core": "1.60.0"
-        "node": ">=16"
+        "node": ">=18"
-      "version": "1.44.0",
-      "resolved": "https://registry.npmjs.org/playwright-core/-/playwright-core-1.44.0.tgz",
-      "integrity": "sha512-ZTbkNpFfYcGWohvTTl+xewITm7EOuqIqex0c7dNZ+aXsbrLj0qI8XlGKfPpipjm0Wny/4Lt4CJsWJk1stVS5qQ==",
+      "version": "1.60.0",
+      "resolved": "https://registry.npmjs.org/playwright-core/-/playwright-core-1.60.0.tgz",
+      "integrity": "sha512-9bW6zvX/m0lEbgTKJ6YppOKx8H3VOPBMOCFh2irXFOT4BbHgrx5hPjwJYLT40Lu+4qtD36qKc/Hn56StUW57IA==",
-        "node": ">=16"
+        "node": ">=18"
```

### `package.json`

- 변경량: `+1 / -2`

```diff
@@ -1,6 +1,5 @@
-    "@playwright/test": "^1.44.0",
-    "playwright": "^1.44.0"
+    "@playwright/test": "^1.60.0"
```

### `run.bat`

- 변경량: `+1 / -19`

### `scripts\test_all_menus_playwright.py`

- 변경량: `+112 / -218`

```diff
@@ -1,259 +1,153 @@
-v864.3 전체 메뉴/사이드바/툴바 1:1 클릭 검증 -Playwright
-==========================================================
-모든 data-action 버튼을 클릭하고:
-1. 에러 토스트가 뜨지 않는지
-2. 모달이 열리거나 탭이 전환되는지
-3. 빈 화면(blank)이 아닌지
-확인합니다.
+SQM 핵심 UI smoke suite
+======================
-사용:
-    # 서버가 이미 실행 중이어야 합니다 (python -m uvicorn backend.api:app --port 8765)
-    python scripts/test_all_menus_playwright.py
-    python scripts/test_all_menus_playwright.py --headless
+기존 스크립트는 모든 메뉴 액션을 광범위하게 클릭해 오래 걸리고
+부작용 가능성도 컸다. 이 버전은 릴리스 전 빠르게 돌릴 수 있는
+핵심 화면 smoke 검증만 수행한다.
+import argparse
-import argparse
-
-# 클릭하면 안 되는 위험한 액션 (DB 변경/종료)
-SKIP_ACTIONS = {
-    'onExit',           # 앱 종료
-    'onTestDbReset',    # DB 초기화
-}
-
-# POST 액션 중 실행하면 DB가 변경되는 것들 -클릭만 하고 confirm 안 함
-CONFIRM_REQUIRED = {
-    'onOnBackup',       # 백업 생성
-    'onRestore',        # 복원
-    'onOptimizeDb',     # DB 최적화
-    'onCleanupLogs',    # 로그 정리
-    'onInboundCancel',  # 입고 취소
-    'onApplyApproved',  # 예약 반영
-}
+ROUTES = [
+    "pending",
+    "available",
+    "allocation",
+    "picked",
+    "return",
... (이하 생략, 총 +112/-218 줄)
```

### `sqm_debug.log`

- 변경량: `+13 / -38`

### `test-results\.last-run.json`

- 변경량: `+10 / -2`

```diff
@@ -1,4 +1,12 @@
-  "status": "passed",
-  "failedTests": []
+  "status": "failed",
+  "failedTests": [
+    "7c8078cb3a371d931d40-168226b1c1636d6cc1e0",
+    "7c8078cb3a371d931d40-cfb335f96ec6c4bfd419",
+    "7c8078cb3a371d931d40-3d2e27914c66fcd358d0",
+    "7c8078cb3a371d931d40-d95c4ae6f074f5b8abb2",
+    "7c8078cb3a371d931d40-1fb0c9442092cb9ab972",
+    "7c8078cb3a371d931d40-15ba6bf2a1c5fc03d850",
+    "7c8078cb3a371d931d40-679faff691b3ff82abce"
+  ]
```

### `tests\sqm_regression.spec.js`

- 변경량: `+94 / -2`

```diff
@@ -5,7 +5,7 @@
-const APP_URL = 'http://127.0.0.1:8765';
+const APP_URL = process.env.SQM_APP_URL || 'http://127.0.0.1:8765';
@@ -24,7 +24,7 @@
-      // 사이드바 탭 클릭 (data-route 속성)
+      // 현재 사이드바 구현의 정식 라우트 속성
@@ -59,4 +59,96 @@
+
+  test('Available 탭 — 핵심 컬럼과 그룹 전환 버튼 유지', async ({ page }) => {
+    await page.locator('[data-route="available"]').first().click();
+    await expect(page.locator('#page-container')).toContainText('Con Return');
+    await expect(page.locator('#page-container')).toContainText('Free');
+    await expect(page.getByText('LOT별', { exact: true })).toBeVisible();
+    await expect(page.getByText('컨테이너별', { exact: true })).toBeVisible();
+    await expect(page.getByText('입고일별', { exact: true })).toBeVisible();
+  });
+
+  test('Pending 탭 — 추가기능 버튼 onclick이 깨지지 않음', async ({ page }) => {
+    await page.locator('[data-route="pending"]').first().click();
+    const buttons = page.locator('button[title="추가기능"]');
+
+    if (await buttons.count() === 0) {
+      test.skip(true, '입고대기 LOT가 없어 버튼 렌더링 검증을 건너뜀');
+    }
+
+    const onclick = await buttons.first().getAttribute('onclick');
+    expect(onclick).toContain('showPendingActionMenu(event,');
+    expect(onclick).not.toContain('JSON.stringify');
+    expect(onclick).not.toContain('""');
+  });
+
+  test('Picked 탭 — 그룹 모드 전환 중 치명 콘솔 오류 없음', async ({ page }) => {
+    const consoleErrors = [];
+    page.on('pageerror', (err) => consoleErrors.push(err.message));
+
+    await page.locator('[data-route="picked"]').first().click();
+    await page.getByText('고객사별', { exact: true }).click();
+    await page.waitForTimeout(300);
+    await page.getByText('입고일별', { exact: true }).click();
+    await page.waitForTimeout(300);
+
+    expect(consoleErrors, `Picked 그룹 전환 오류: ${consoleErrors.join(' | ')}`).toHaveLength(0);
+  });
... (이하 생략, 총 +94/-2 줄)
```

### `실행.bat`

- 변경량: `+1 / -19`

## base에만 있는 파일

- `SQM_v868_vs_v869_비교표.pdf` (30,134 bytes)
- `SQM_v868_변경내역_v869공유용.pdf` (30,383 bytes)
- `bin` (0 bytes)
- `cd` (0 bytes)
- `dir` (0 bytes)
- `echo` (0 bytes)
- `list.txt` (0 bytes)
- `node` (0 bytes)
- `npm` (0 bytes)
- `out.txt` (0 bytes)
- `rmdir` (0 bytes)
- `scripts\compare_v868_v869.py` (6,137 bytes)
- `scripts\fix_template_duplicates.py` (4,396 bytes)
- `scripts\patch_fix_pending_btn.py` (3,700 bytes)
- `scripts\patch_pending_empty.py` (1,214 bytes)
- `test_out.txt` (123 bytes)
- `type` (0 bytes)
- `~$M_PATCH_FINAL_REPORT_2026-05-06.md` (162 bytes)
- `~$M_UI_Schema_Plan.docx` (162 bytes)
- `지정된` (0 bytes)

## target에만 있는 파일

- `REPORTS\folder_diff_v868_claan_vs_v869_clean_20260517.md` (9,959 bytes)
- `REPORTS\folder_diff_v868_claan_vs_v869_clean_regenerated_20260517.md` (25,284 bytes)
- `REPORTS\phase5_verify_20260517_162614.json` (8,992 bytes)
- `REPORTS\phase5_verify_20260517_162614.md` (2,089 bytes)
- `REPORTS\phase5_verify_20260517_163042.json` (8,992 bytes)
- `REPORTS\phase5_verify_20260517_163042.md` (2,089 bytes)
- `REPORTS\phase5_verify_20260517_193756.json` (8,992 bytes)
- `REPORTS\phase5_verify_20260517_193756.md` (2,089 bytes)
- `REPORTS\playwright_ui_smoke.json` (1,564 bytes)
- `REPORTS\v868_hotfix_carryover_review_20260517.md` (2,794 bytes)
- `frontend\js\sqm-aux-modals.js` (20,919 bytes)
- `frontend\js\sqm-product-modals.js` (15,652 bytes)
- `frontend\js\sqm-settings-templates.js` (35,072 bytes)
- `frontend\js\sqm-tools-modals.js` (11,446 bytes)
- `frontend\js\sqm-upload-modals.js` (26,487 bytes)
- `frontend\js\sqm-weight-panel.js` (6,826 bytes)
- `run_v869_clean.bat` (712 bytes)
- `scripts\compare_release_folders.py` (5,967 bytes)
- `test-results\sqm_regression-SQM-라우터-회귀--013fa-단-전체-탭-순회-—-각-탭-HTTP-500-없음\error-context.md` (4,238 bytes)
- `test-results\sqm_regression-SQM-라우터-회귀--1185d-g-버그-차단-탭-재고-—-Preparing-없음\error-context.md` (4,238 bytes)
- `test-results\sqm_regression-SQM-라우터-회귀--20de2-g-버그-차단-탭-이동-—-Preparing-없음\error-context.md` (4,229 bytes)
- `test-results\sqm_regression-SQM-라우터-회귀--45d3d-g-버그-차단-탭-피킹-—-Preparing-없음\error-context.md` (4,229 bytes)
- `test-results\sqm_regression-SQM-라우터-회귀--5ec24-g-버그-차단-탭-반품-—-Preparing-없음\error-context.md` (4,229 bytes)
- `test-results\sqm_regression-SQM-라우터-회귀--bdb58-버그-차단-탭-입고대기-—-Preparing-없음\error-context.md` (4,235 bytes)
- `test-results\sqm_regression-SQM-라우터-회귀--dc371-g-버그-차단-탭-배정-—-Preparing-없음\error-context.md` (4,229 bytes)
- `tests\test_status_transition_contract.py` (1,120 bytes)
- `tests\test_v869_stability_regressions.py` (5,918 bytes)
- `v869_uvicorn_8766.err.log` (105,099 bytes)
- `v869_uvicorn_8766.out.log` (56,651 bytes)
