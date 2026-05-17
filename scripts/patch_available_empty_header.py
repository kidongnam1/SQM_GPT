# -*- coding: utf-8 -*-
"""
patch_available_empty_header.py
================================
Purpose: Available 빈 데이터(0건)일 때도 헤더 표시
Why    : 사용자 보고 — 데이터 0건일 때 모드 토글/Excel/새로고침 모두 안 보임
Fix    : if (!rows.length) {...; return;} 분기에서 헤더 먼저 출력 후 빈 메시지
Rule   : CLAUDE.md Rule 5 — Python 스크립트만
Author : Ruby (Senior Software Architect) — 2026-05-17
"""
import sys
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
TARGET = ROOT / "frontend" / "js" / "sqm-inventory.js"

ANCHOR = """      var rows = Array.isArray(res) ? res : (res.data || res.rows || res.items || []);
      if (!rows.length) {
        c.innerHTML = '<div class="empty" style="padding:60px;text-align:center;color:var(--text-muted,#888)">✅ Available 재고 없음 (전량 배분 또는 피킹 완료)</div>';
        return;
      }"""

PATCH = """      var rows = Array.isArray(res) ? res : (res.data || res.rows || res.items || []);
      // v868 fix (2026-05-17): 데이터 0건일 때도 헤더(모드 토글/Excel/새로고침) 표시
      if (!rows.length) {
        var availModeEmpty = window._availViewMode || 'lot';
        var _availBtnEmpty = function(val, label, cur) {
          var act = val === cur
            ? 'background:var(--accent,#3b82f6);color:#fff;border-color:var(--accent,#3b82f6);'
            : 'background:var(--surface,#1e293b);color:var(--text-muted);border-color:var(--border,#334155);';
          return '<button class="btn" style="font-size:12px;padding:4px 10px;' + act + '" '
            + 'onclick="window._availViewMode=\\'' + val + '\\';window.loadAvailablePage()">' + label + '</button>';
        };
        c.innerHTML =
          '<section style="padding:12px 16px">'
          + '<div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;flex-wrap:wrap">'
          + '<h2 style="margin:0;font-size:16px;color:#22c55e">✅ Available 재고 — 판매 가능 물량</h2>'
          + '<span style="font-size:12px;color:var(--text-muted)">0 LOT</span>'
          + '<div style="display:flex;gap:4px;margin-left:8px">'
          + _availBtnEmpty('lot', 'LOT별', availModeEmpty)
          + _availBtnEmpty('container', '컨테이너별', availModeEmpty)
          + _availBtnEmpty('date', '입고일별', availModeEmpty)
          + '</div>'
          + '<button class="btn btn-secondary" style="font-size:12px" onclick="window.exportAvailableExcel()" title="현재 화면 Available 데이터를 Excel로 내보냅니다">📊 Excel 내보내기</button>'
          + '<button class="btn btn-ghost" style="font-size:12px" onclick="window.loadAvailablePage()">🔄 새로고침</button>'
          + '</div>'
          + '<div class="empty" style="padding:60px;text-align:center;color:var(--text-muted,#888)">✅ Available 재고 없음 (전량 배분 또는 피킹 완료)</div>'
          + '</section>';
        return;
      }"""


def main() -> int:
    text = TARGET.read_text(encoding="utf-8")

    if "v868 fix (2026-05-17): 데이터 0건일 때도 헤더" in text:
        print("[SKIP] already patched.")
        return 0
    if ANCHOR not in text:
        print("[ERROR] anchor not found")
        return 2
    if text.count(ANCHOR) > 1:
        print(f"[ERROR] matched {text.count(ANCHOR)} times")
        return 3

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = TARGET.with_suffix(f".js.bak_empty_header_{ts}")
    shutil.copy2(TARGET, backup)
    print(f"[INFO] backup: {backup.name}")

    new_text = text.replace(ANCHOR, PATCH, 1)
    if not new_text.rstrip().endswith("})();"):
        print("[ERROR] IIFE closing lost")
        return 4

    TARGET.write_bytes(new_text.encode("utf-8"))
    r = subprocess.run(["node", "--check", str(TARGET)], capture_output=True, text=True)
    if r.returncode != 0:
        print(f"[FAIL] {r.stderr}")
        return 5
    print("[OK] Available 빈 데이터 헤더 표시 완료")
    return 0


if __name__ == "__main__":
    sys.exit(main())
