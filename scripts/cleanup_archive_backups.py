# -*- coding: utf-8 -*-
"""
cleanup_archive_backups.py
==========================
Purpose: 백업/손상/임시 파일들을 _archive/ 폴더로 이동 (빌드 오염 방지)
Why    : SQM_v868.spec이 frontend/ 폴더 전체를 EXE에 포함시키므로
         .bak, .bak2, .corrupted, .pre_parity_patch, .BROKEN_BY_EDIT_*, .bak_router_*,
         .bak_status_*, .bak_fmt_* 등이 모두 EXE에 묶일 위험.
         빌드 전 _archive/로 이동하여 격리.
Rule   : 삭제 아닌 이동 (사고 학습 자료 보존)
Author : Ruby (Senior Software Architect) — 2026-05-15
"""
import sys
import shutil
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
ARCHIVE = ROOT / "_archive"

# 이동 대상 패턴 (glob)
PATTERNS = [
    "frontend/js/*.bak",
    "frontend/js/*.bak2",
    "frontend/js/*.bak3",
    "frontend/js/*.bak_*",
    "frontend/js/*.corrupted_*",
    "frontend/js/*.pre_parity_patch",
    "frontend/js/*.BROKEN_BY_EDIT_*",
    "frontend/js/*.bak_presplit",
    "frontend/js/*.bak_router_*",
    "frontend/js/*.bak_fmt_*",
    # 다른 디렉토리도 점검
    "engine_modules/inventory_modular/*.bak_*",
    "backend/api/*.bak*",
]


def main(dry_run: bool = False) -> int:
    print(f"[INFO] root: {ROOT}")
    print(f"[INFO] archive: {ARCHIVE}")
    print(f"[INFO] dry_run: {dry_run}")
    print()

    # _archive/ 폴더 생성
    if not dry_run:
        ARCHIVE.mkdir(exist_ok=True)
        (ARCHIVE / "README.md").write_text(
            "# _archive/\n\n"
            "이 폴더는 백업/손상/임시 파일들을 격리하는 곳입니다.\n"
            "PyInstaller .spec 파일이 frontend/ 폴더 전체를 묶으므로, "
            "백업 파일이 EXE에 포함되지 않도록 별도 폴더로 분리합니다.\n\n"
            "**삭제하지 마세요** — 사고 학습 자료(.corrupted_by_agent3 등)는 향후 디버깅에 유용합니다.\n\n"
            f"- 생성일: 2026-05-15 (Ruby)\n"
            "- 관련: scripts/cleanup_archive_backups.py\n",
            encoding="utf-8",
        )

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    moved_count = 0
    skip_count = 0
    errors = []

    # 패턴별 매칭 + 이동
    seen_files = set()
    for pat in PATTERNS:
        for f in ROOT.glob(pat):
            if not f.is_file():
                continue
            if f in seen_files:
                continue
            seen_files.add(f)

            # 상대 경로 보존
            rel = f.relative_to(ROOT)
            dest = ARCHIVE / rel
            dest.parent.mkdir(parents=True, exist_ok=True)

            if dest.exists():
                # 같은 이름이 이미 archive에 있으면 타임스탬프 추가
                dest = dest.with_suffix(dest.suffix + f".{ts}")

            print(f"  {rel}  →  _archive/{dest.relative_to(ARCHIVE)}")
            if not dry_run:
                try:
                    shutil.move(str(f), str(dest))
                    moved_count += 1
                except Exception as e:
                    errors.append(f"{rel}: {e}")
                    skip_count += 1
            else:
                moved_count += 1

    print()
    print(f"[SUMMARY] moved: {moved_count}, skipped: {skip_count}")
    if errors:
        print("[ERRORS]")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("[OK] cleanup complete.")
    return 0


if __name__ == "__main__":
    dry = "--dry-run" in sys.argv
    sys.exit(main(dry_run=dry))
