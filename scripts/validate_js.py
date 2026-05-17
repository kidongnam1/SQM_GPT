#!/usr/bin/env python3
"""
JS 파일 문법 검사
"""
import subprocess
import os

TARGET_FILES = [
    "frontend/js/sqm-core.js",
    "frontend/js/sqm-inline.js",
    "frontend/js/sqm-allocation.js",
    "frontend/js/sqm-tonbag.js",
    "frontend/js/sqm-logistics.js",
    "frontend/js/sqm-inventory.js",
    "frontend/js/sqm-picked.js",
    "frontend/js/sqm-onestop-inbound.js",
]

print("=" * 60)
print("JS 파일 문법 검사 (node --check)")
print("=" * 60)

all_ok = True
for path in TARGET_FILES:
    if not os.path.exists(path):
        print(f"  SKIP: {path} (file not found)")
        continue

    try:
        result = subprocess.run(
            ["node", "--check", path],
            capture_output=True,
            timeout=10,
            text=True
        )
        if result.returncode == 0:
            print(f"  [OK] {path}")
        else:
            print(f"  [ERR] {path}")
            if result.stderr:
                print(f"    {result.stderr.strip()}")
            all_ok = False
    except subprocess.TimeoutExpired:
        print(f"  [TIMEOUT] {path}")
        all_ok = False
    except Exception as e:
        print(f"  [EXCEPTION] {path} -- {e}")
        all_ok = False

print("=" * 60)
if all_ok:
    print("[OK] All files passed syntax check")
else:
    print("[ERR] Some files have syntax errors")
print("=" * 60)
