"""patch_seq_tonbag.py — sqm-tonbag.js 순번(#) 첫 컬럼 추가"""
import shutil, sys
from pathlib import Path
from datetime import datetime

TARGET = Path("/sessions/eloquent-amazing-ramanujan/mnt/SQM_v868_claan/frontend/js/sqm-tonbag.js")
ts = datetime.now().strftime("%Y%m%d_%H%M%S")
backup = TARGET.with_name(f"sqm-tonbag.js.bak_{ts}")
shutil.copy2(TARGET, backup)
print(f"[backup] {backup.name}")

src = TARGET.read_text(encoding="utf-8")
orig = src
changes = 0

# ── 1) loadTonbagPage 헤더 ─────────────────────────────────────────────
OLD1 = "'<thead><tr><th>Tonbag ID</th><th>LOT</th><th>Product</th><th>Status</th><th>Weight(MT)</th><th>Location</th><th>Container</th><th></th></tr></thead>'"
NEW1 = "'<thead><tr><th style=\"color:var(--text-muted);text-align:center;width:32px\">#</th><th>Tonbag ID</th><th>LOT</th><th>Product</th><th>Status</th><th>Weight(MT)</th><th>Location</th><th>Container</th><th></th></tr></thead>'"
if OLD1 in src:
    src = src.replace(OLD1, NEW1, 1); changes += 1
    print("[ok1] tonbag 헤더 # 추가")
else:
    print("[WARN1] tonbag 헤더 앵커 없음")

# ── 2) rows.map 인덱스화 ────────────────────────────────────────────────
OLD2 = "      if (tbody) tbody.innerHTML=rows.map(function(r){"
NEW2 = "      if (tbody) tbody.innerHTML=rows.map(function(r, _i){"
if OLD2 in src:
    src = src.replace(OLD2, NEW2, 1); changes += 1
    print("[ok2] rows.map 인덱스화")
else:
    print("[WARN2] rows.map 앵커 없음")

# ── 3) 행 — Tonbag ID td 앞 순번 td 삽입 ──────────────────────────────
OLD3 = "        return '<tr>' +\n          '<td class=\"mono-cell\">'+escapeHtml(r.sub_lt||r.tonbag_id||'-')+'</td>' +"
NEW3 = "        return '<tr>' +\n          '<td class=\"mono-cell\" style=\"color:var(--text-muted);text-align:center\">'+(_i+1)+'</td>' +\n          '<td class=\"mono-cell\">'+escapeHtml(r.sub_lt||r.tonbag_id||'-')+'</td>' +"
if OLD3 in src:
    src = src.replace(OLD3, NEW3, 1); changes += 1
    print("[ok3] tonbag 행 순번 td 추가")
else:
    print("[WARN3] tonbag 행 앵커 없음 — 확인:")
    idx = src.find("tonbag_id")
    if idx >= 0: print("  →", repr(src[max(0,idx-60):idx+80]))

print(f"\n[총 변경] {changes}곳")
TARGET.write_text(src, encoding="utf-8")
print(f"[done] {TARGET.name} 저장")
old_n = orig.count("\n"); new_n = src.count("\n")
print(f"[lines] {old_n} → {new_n} (diff {new_n-old_n:+d})")
tail = src[-200:]
if "})();" in tail or "}());" in tail:
    print("[ok] IIFE 닫힘 확인 ✅")
else:
    print("[WARN] IIFE 닫힘 미확인")
