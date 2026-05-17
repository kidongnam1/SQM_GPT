"""
patch_pending_force.py
backend/api/inbound.py — Excel 업로드 & OneStop 저장 경로에 status='PENDING' 강제 주입

대상 콜사이트:
  1) bulk_import_excel   (~line 342-343)  — Excel 업로드
  2) onestop_inbound_save (~line 1188-1190) — OneStop 편집 저장
  (PDF 경로 line 1316은 이미 패치됨 → 건드리지 않음)
"""
import shutil, sys
from pathlib import Path
from datetime import datetime

TARGET = Path("/sessions/eloquent-amazing-ramanujan/mnt/SQM_v868_claan/backend/api/inbound.py")
ts = datetime.now().strftime("%Y%m%d_%H%M%S")
backup = TARGET.with_name(f"inbound.py.bak_{ts}")
shutil.copy2(TARGET, backup)
print(f"[backup] {backup.name}")

src = TARGET.read_text(encoding="utf-8")
orig = src
changes = 0

# ══════════════════════════════════════════════════════════
# 1) bulk_import_excel — Excel 업로드 경로
#    lot_no 체크 후 continue, 그 다음 try: 직전에 주입
# ══════════════════════════════════════════════════════════
OLD1 = (
    '                continue\n'
    '            try:\n'
    '                result = engine.add_inventory_from_dict(data)\n'
    '                if result.get("success"):\n'
    '                    success_count += 1'
)
NEW1 = (
    '                continue\n'
    '            data["status"] = "PENDING"  # v868: Excel 수동 입고 → PENDING 강제 (053fa7a 정책)\n'
    '            try:\n'
    '                result = engine.add_inventory_from_dict(data)\n'
    '                if result.get("success"):\n'
    '                    success_count += 1'
)
if OLD1 in src:
    src = src.replace(OLD1, NEW1, 1)
    changes += 1
    print("[ok1] bulk_import_excel: data['status']='PENDING' 주입")
else:
    print("[WARN1] bulk_import_excel 앵커 없음 — 확인:")
    idx = src.find('engine.add_inventory_from_dict(data)')
    if idx >= 0:
        print("  →", repr(src[max(0, idx-120):idx+60]))

# ══════════════════════════════════════════════════════════
# 2) onestop_inbound_save — OneStop 편집 저장 경로
#    lot_no 체크 후 continue, 그 다음 try: 직전에 주입
# ══════════════════════════════════════════════════════════
OLD2 = (
    '            continue\n'
    '        try:\n'
    '            result = engine.add_inventory_from_dict(data)\n'
    '            if result.get("success"):\n'
    '                success_count += 1'
)
NEW2 = (
    '            continue\n'
    '        data["status"] = "PENDING"  # v868: OneStop 입고 → PENDING 강제 (053fa7a 정책)\n'
    '        try:\n'
    '            result = engine.add_inventory_from_dict(data)\n'
    '            if result.get("success"):\n'
    '                success_count += 1'
)
if OLD2 in src:
    src = src.replace(OLD2, NEW2, 1)
    changes += 1
    print("[ok2] onestop_inbound_save: data['status']='PENDING' 주입")
else:
    print("[WARN2] onestop_inbound_save 앵커 없음 — 확인:")
    idx = src.find('[onestop-save]')
    if idx >= 0:
        print("  →", repr(src[max(0, idx-300):idx+60]))

print(f"\n[총 변경] {changes}곳")
if changes == 0:
    print("[ERROR] 변경 없음 — 원본 유지")
    sys.exit(1)

TARGET.write_text(src, encoding="utf-8")
print(f"[done] {TARGET.name} 저장")
old_n = orig.count("\n"); new_n = src.count("\n")
print(f"[lines] {old_n} → {new_n} (diff {new_n-old_n:+d})")

# ── 검증: 두 주입 문자열이 실제로 존재하는지 확인 ──
v1 = 'data["status"] = "PENDING"  # v868: Excel 수동 입고' in src
v2 = 'data["status"] = "PENDING"  # v868: OneStop 입고' in src
print(f"[verify] Excel PENDING 주입: {'✅' if v1 else '❌'}")
print(f"[verify] OneStop PENDING 주입: {'✅' if v2 else '❌'}")
