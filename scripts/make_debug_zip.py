# -*- coding: utf-8 -*-
"""
SQM v869 디버깅용 압축 스크립트
- 프로그램 실행/디버깅에 실제로 필요한 소스 파일만 추려서 zip 생성
- 안드로이드폰 등에서 코드 열람/검토용
출력: ../SQM_v869_debug_<YYYYMMDD>.zip
"""
import os
import sys
import zipfile
import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ── 포함할 최상위 단일 파일 ────────────────────────────────
INCLUDE_FILES = [
    "main_webview.py",
    "config.py", "config_logging.py", "config_sql.py",
    "version.py", "theme_aware.py",
    "requirements.txt", "requirements_webview.txt",
    "run.bat", "run_v869_clean.bat", "실행.bat",
    "SQM_v868.spec", "build_v868.bat",
    "pytest.ini", "settings.ini.template",
    "CLAUDE.md", "HOW_TO_RUN.md",
]

# ── 포함할 디렉터리 (재귀) ─────────────────────────────────
INCLUDE_DIRS = [
    "core", "engine_modules", "features", "parsers",
    "backend", "utils", "gui_app_modular",
    "frontend", "resources", "tools", "fixes",
    "tests", "docs",
]

# ── 현재 DB 파일만 별도 포함 (디버깅 시 데이터 확인용) ─────
INCLUDE_EXTRA = [
    os.path.join("data", "db", "sqm_inventory.db"),
]

# ── 제외할 디렉터리 이름 ───────────────────────────────────
EXCLUDE_DIRS = {
    "__pycache__", "_archive", ".git", ".bkit", ".claude",
    ".cursor", ".locks", ".pytest_cache", "node_modules",
    "test-results", ".ipynb_checkpoints",
}

# 이름이 정확히 일치하면 제외할 파일 (테스트 리포트 등)
EXCLUDE_FILE_NAMES = {
    "workflow_test_report.html",
}

def is_excluded_file(name: str) -> bool:
    low = name.lower()
    if low in EXCLUDE_FILE_NAMES:
        return True
    if low.endswith((".pyc", ".pyo", ".log",
                      "-shm", "-wal", ".db-shm", ".db-wal")):
        return True
    if ".bak" in low or ".broken" in low:
        return True
    if low in ("thumbs.db", ".ds_store"):
        return True
    return False

def main():
    stamp = datetime.date.today().strftime("%Y%m%d")
    out_path = os.path.join(os.path.dirname(ROOT),
                            f"SQM_v869_debug_{stamp}.zip")

    count = 0
    total_bytes = 0
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zf:
        # 단일 파일
        for rel in INCLUDE_FILES + INCLUDE_EXTRA:
            src = os.path.join(ROOT, rel)
            if os.path.isfile(src):
                zf.write(src, rel)
                count += 1
                total_bytes += os.path.getsize(src)

        # 디렉터리 재귀
        for d in INCLUDE_DIRS:
            base = os.path.join(ROOT, d)
            if not os.path.isdir(base):
                continue
            for cur, dirs, files in os.walk(base):
                dirs[:] = [x for x in dirs if x not in EXCLUDE_DIRS]
                for fn in files:
                    if is_excluded_file(fn):
                        continue
                    src = os.path.join(cur, fn)
                    rel = os.path.relpath(src, ROOT)
                    zf.write(src, rel)
                    count += 1
                    total_bytes += os.path.getsize(src)

    zsize = os.path.getsize(out_path)
    print(f"[OK] {out_path}")
    print(f"  files   : {count}")
    print(f"  raw     : {total_bytes/1024/1024:.1f} MB")
    print(f"  zipped  : {zsize/1024/1024:.1f} MB")

if __name__ == "__main__":
    main()
