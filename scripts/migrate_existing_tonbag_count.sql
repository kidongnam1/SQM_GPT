-- ────────────────────────────────────────────────────────────────────
-- migrate_existing_tonbag_count.sql
-- ────────────────────────────────────────────────────────────────────
-- Purpose: 기존 inventory 행의 tonbag_count = 0 → 실제 톤백 수로 동기화
-- When   : 2026-05-15 — patch_tonbag_count_insert.py 적용 후 1회 실행
-- Why    : 기존 20개 LOT는 tonbag_count=0으로 INSERT되어 정합성 FAIL 발생
--          이 SQL로 inventory_tonbag 실제 카운트 기반 UPDATE → mismatch 해소
-- Run    : sqlite3 data/db/sqm_inventory.db < scripts/migrate_existing_tonbag_count.sql
--          또는 SQM 앱의 SQL 콘솔에서 실행
-- Safety : 백업 먼저 권장 (Windows CMD):
--          copy data\db\sqm_inventory.db data\db\sqm_inventory_pre_tonbag_count_fix.db
-- Author : Ruby (Senior Software Architect)
-- ────────────────────────────────────────────────────────────────────

-- ① 마이그레이션 전 상태 확인
SELECT 'BEFORE — mismatch 카운트:' AS step;
SELECT COUNT(*) AS mismatch_lots
FROM inventory i
LEFT JOIN (
    SELECT inventory_id, COUNT(*) AS actual_cnt
    FROM inventory_tonbag
    GROUP BY inventory_id
) t ON t.inventory_id = i.id
WHERE COALESCE(i.tonbag_count, 0) != COALESCE(t.actual_cnt, 0);

-- ② 실제 톤백 수로 동기화 (모든 LOT 대상)
UPDATE inventory
SET tonbag_count = (
    SELECT COUNT(*)
    FROM inventory_tonbag t
    WHERE t.inventory_id = inventory.id
);

-- ③ 마이그레이션 후 검증
SELECT 'AFTER — mismatch 카운트 (0이어야 정상):' AS step;
SELECT COUNT(*) AS mismatch_lots
FROM inventory i
LEFT JOIN (
    SELECT inventory_id, COUNT(*) AS actual_cnt
    FROM inventory_tonbag
    GROUP BY inventory_id
) t ON t.inventory_id = i.id
WHERE COALESCE(i.tonbag_count, 0) != COALESCE(t.actual_cnt, 0);

-- ④ 샘플 5건 확인
SELECT 'AFTER — 샘플 5건:' AS step;
SELECT i.lot_no, i.mxbg_pallet, i.tonbag_count, COUNT(t.id) AS actual_count
FROM inventory i
LEFT JOIN inventory_tonbag t ON t.inventory_id = i.id
GROUP BY i.id
ORDER BY i.created_at DESC
LIMIT 5;
