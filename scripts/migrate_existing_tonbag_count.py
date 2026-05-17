# -*- coding: utf-8 -*-
"""
migrate_existing_tonbag_count.py
================================
Purpose: 기존 inventory 행의 tonbag_count = 0 → 실제 톤백 수로 동기화
When   : 2026-05-15 — patch_tonbag_count_insert.py 적용 후 1회 실행
Why    : 기존 20개 LOT는 tonbag_count=0으로 INSERT되어 정합성 FAIL 발생
         이 스크립트로 inventory_tonbag 실제 카운트 기반 UPDATE → mismatch 해소

사용법 (Windows CMD):
    cd /d D:\\program\\SQM_inventory\\SQM_v868_claan
    python scripts\\migrate_existing_tonbag_count.py

또는 dry-run (실제 변경 없이 미리보기):
    python scripts\\migrate_existing_tonbag_count.py --dry-run

Safety : 실행 전 자동 백업 (data/db/sqm_inventory_pre_migrate_{timestamp}.db)
Author : Ruby (Senior Software Architect) — 2026-05-15
"""
import sqlite3
import sys
import shutil
import os
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "db" / "sqm_inventory.db"


def find_db() -> Path:
    """DB 파일 위치 확인 (운영 DB 우선)"""
    if DB_PATH.exists():
        return DB_PATH
    # fallback: 최근 백업
    backup_dir = ROOT / "backup"
    if backup_dir.exists():
        backups = sorted(backup_dir.glob("sqm_backup_*.db"),
                        key=lambda p: p.stat().st_mtime, reverse=True)
        if backups:
            print(f"[WARN] 운영 DB 없음. 최근 백업 사용: {backups[0]}", file=sys.stderr)
            return backups[0]
    raise FileNotFoundError(f"DB 파일 없음: {DB_PATH}")


def main(dry_run: bool = False) -> int:
    try:
        db_path = find_db()
    except FileNotFoundError as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return 1

    print(f"[INFO] DB: {db_path}")
    print(f"[INFO] dry_run: {dry_run}")
    print()

    # ── ① 안전 백업 (실제 실행 시에만)
    if not dry_run:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup = db_path.parent / f"sqm_inventory_pre_migrate_{ts}.db"
        # WAL 모드면 -wal/-shm도 함께 백업할 수 있지만, 메인 파일만으로 충분
        shutil.copy2(db_path, backup)
        print(f"[INFO] backup: {backup.name}")

    conn = sqlite3.connect(str(db_path), timeout=10)
    conn.row_factory = sqlite3.Row

    # ── ② 마이그레이션 전 상태 확인
    print()
    print("=== BEFORE — mismatch 카운트 ===")
    before = conn.execute("""
        SELECT COUNT(*) AS cnt
        FROM inventory i
        LEFT JOIN (
            SELECT inventory_id, COUNT(*) AS actual_cnt
            FROM inventory_tonbag
            GROUP BY inventory_id
        ) t ON t.inventory_id = i.id
        WHERE COALESCE(i.tonbag_count, 0) != COALESCE(t.actual_cnt, 0)
    """).fetchone()
    print(f"  mismatch LOT 수: {before['cnt']}")

    if before['cnt'] == 0:
        print()
        print("[OK] 이미 모든 LOT의 tonbag_count가 정상입니다. 마이그레이션 불필요.")
        conn.close()
        return 0

    # ── ③ 영향받을 LOT 미리보기 (최대 10건)
    print()
    print("=== 마이그레이션 대상 (최대 10건) ===")
    sample = conn.execute("""
        SELECT i.lot_no,
               COALESCE(i.tonbag_count, 0) AS before_cnt,
               COUNT(t.id) AS after_cnt,
               i.mxbg_pallet,
               i.status
        FROM inventory i
        LEFT JOIN inventory_tonbag t ON t.inventory_id = i.id
        WHERE COALESCE(i.tonbag_count, 0) != (
            SELECT COUNT(*) FROM inventory_tonbag t2 WHERE t2.inventory_id = i.id
        )
        GROUP BY i.id
        LIMIT 10
    """).fetchall()
    print(f"  {'LOT':<14s} {'before':>7s} → {'after':>7s} (mxbg_pallet={'?':<3s} status)")
    for r in sample:
        print(f"  {r['lot_no']:<14s} {r['before_cnt']:>7d} → {r['after_cnt']:>7d} "
              f"(mxbg={r['mxbg_pallet']:<3d} {r['status']})")

    # ── ④ 실제 UPDATE 실행
    print()
    if dry_run:
        print("[DRY-RUN] 실제 UPDATE 미실행. 옵션 없이 다시 실행하면 적용됩니다.")
        conn.close()
        return 0

    print("=== UPDATE 실행 중... ===")
    cur = conn.execute("""
        UPDATE inventory
        SET tonbag_count = (
            SELECT COUNT(*)
            FROM inventory_tonbag t
            WHERE t.inventory_id = inventory.id
        )
    """)
    updated_rows = cur.rowcount
    conn.commit()
    print(f"  ✅ {updated_rows} LOT 업데이트 완료")

    # ── ⑤ 마이그레이션 후 검증
    print()
    print("=== AFTER — mismatch 카운트 (0이어야 정상) ===")
    after = conn.execute("""
        SELECT COUNT(*) AS cnt
        FROM inventory i
        LEFT JOIN (
            SELECT inventory_id, COUNT(*) AS actual_cnt
            FROM inventory_tonbag
            GROUP BY inventory_id
        ) t ON t.inventory_id = i.id
        WHERE COALESCE(i.tonbag_count, 0) != COALESCE(t.actual_cnt, 0)
    """).fetchone()
    print(f"  mismatch LOT 수: {after['cnt']}")

    conn.close()

    if after['cnt'] == 0:
        print()
        print("🎉 마이그레이션 성공 — 정합성 검사가 이제 PASS 되어야 합니다.")
        print("    앱 재시작 후 '정합성' 메뉴 클릭하여 확인하세요.")
        return 0
    else:
        print()
        print(f"⚠️ 마이그레이션 후에도 {after['cnt']}건 mismatch 잔존.")
        print("    추가 진단 필요 — 백업 파일로 복구 가능.")
        return 2


if __name__ == "__main__":
    dry = "--dry-run" in sys.argv
    sys.exit(main(dry_run=dry))
