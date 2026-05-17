# -*- coding: utf-8 -*-
"""
patch_emphasize_inbound_date.py
================================
Purpose: 입고 확정 모달의 날짜 입력 라벨 강조 — 사용자가 더 쉽게 인지
Why    : 사용자 "팬딩에서 어베러블로 넘어올 때 날짜 정하는 메뉴 필요"
         → 이미 있음. 다만 라벨이 작아 못 봄. 강조 필요.
Rule   : CLAUDE.md Rule 5 — Python 스크립트만
Author : Ruby (Senior Software Architect) — 2026-05-16
"""
import sys
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
TARGET = ROOT / "frontend" / "js" / "sqm-inventory.js"

# 단일 LOT 확정 모달 — 라벨 강조
ANCHOR = """    var label = document.createElement('label');
    label.style.cssText = 'font-size:13px;color:var(--text-muted);display:block;margin-bottom:6px';
    label.textContent = '\\u4d8a\\uace0 \\ud655\\uc815\\uc77c (YYYY-MM-DD)';"""

# 위의 hex가 정확치 않음 — 실제 매칭은 다음 패턴
ANCHOR_REAL = "label.textContent = '\\uc785\\uace0 \\ud655\\uc815\\uc77c (YYYY-MM-DD)';"

# 라벨 강조 — 색상 + 폰트 + 아이콘
ANCHOR_FULL = """    var label = document.createElement('label');
    label.style.cssText = 'font-size:13px;color:var(--text-muted);display:block;margin-bottom:6px';
    label.textContent = '\\uc785\\uace0 \\ud655\\uc815\\uc77c (YYYY-MM-DD)';"""

PATCH_FULL = """    var label = document.createElement('label');
    // v868 fix (2026-05-16): 입고 확정일 강조 — 사용자가 명확히 인지
    label.style.cssText = 'font-size:14px;font-weight:600;color:#22c55e;display:block;margin-bottom:8px;padding:6px 8px;background:rgba(34,197,94,0.08);border-left:3px solid #22c55e;border-radius:4px';
    label.innerHTML = '\\ud83d\\udcc5 <strong>\\uc785\\uace0 \\ud655\\uc815\\uc77c</strong> \\u2014 \\uc774 \\ub0a0\\uc9dc\\ub85c \\ucc3d\\uace0 \\ubc18\\uc785 \\ucc98\\ub9ac\\ub429\\ub2c8\\ub2e4 (YYYY-MM-DD)';"""


def main() -> int:
    text = TARGET.read_text(encoding="utf-8")

    if "v868 fix (2026-05-16): 입고 확정일 강조" in text:
        print("[SKIP] already patched.")
        return 0
    if ANCHOR_FULL not in text:
        print("[ERROR] anchor not found", file=sys.stderr)
        return 2
    if text.count(ANCHOR_FULL) > 1:
        print(f"[ERROR] anchor matched {text.count(ANCHOR_FULL)} times", file=sys.stderr)
        return 3

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = TARGET.with_suffix(f".js.bak_emphasize_date_{ts}")
    shutil.copy2(TARGET, backup)
    print(f"[INFO] backup: {backup.name}")

    new_text = text.replace(ANCHOR_FULL, PATCH_FULL, 1)
    if not new_text.rstrip().endswith("})();"):
        print("[ERROR] IIFE closing lost")
        return 4

    TARGET.write_bytes(new_text.encode("utf-8"))

    r = subprocess.run(["node", "--check", str(TARGET)], capture_output=True, text=True)
    if r.returncode != 0:
        print(f"[FAIL] syntax: {r.stderr}")
        return 5

    print("[OK] 입고 확정일 라벨 강조 완료")
    return 0


if __name__ == "__main__":
    sys.exit(main())
