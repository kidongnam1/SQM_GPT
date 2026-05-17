# -*- coding: utf-8 -*-
"""Fix: sqm-onestop-inbound.js _currentRoute → window.getCurrentRoute()"""
import sys

PATH = r"D:\program\SQM_inventory\SQM_v868_claan\frontend\js\sqm-onestop-inbound.js"

with open(PATH, encoding="utf-8") as f:
    src = f.read()

OLD_COMMENT = "     loadInventoryPage, loadKpi, _currentRoute, API"
NEW_COMMENT = "     loadInventoryPage, loadKpi, getCurrentRoute(via window), API"

OLD_CODE = "          if (_currentRoute === 'inventory' && typeof loadInventoryPage === 'function') loadInventoryPage();"
NEW_CODE = "          if (window.getCurrentRoute && window.getCurrentRoute() === 'inventory' && typeof loadInventoryPage === 'function') loadInventoryPage();"

changed = 0
if OLD_COMMENT in src:
    src = src.replace(OLD_COMMENT, NEW_COMMENT, 1)
    changed += 1
    sys.stdout.buffer.write(b"[OK] comment updated\n")
else:
    sys.stdout.buffer.write(b"[WARN] comment line not found\n")

if OLD_CODE in src:
    src = src.replace(OLD_CODE, NEW_CODE, 1)
    changed += 1
    sys.stdout.buffer.write(b"[OK] line 1278 patched\n")
else:
    sys.stdout.buffer.write(b"[WARN] target code not found\n")

if changed > 0:
    with open(PATH, "w", encoding="utf-8") as f:
        f.write(src)
    sys.stdout.buffer.write(b"[DONE] file saved\n")
else:
    sys.stdout.buffer.write(b"[SKIP] nothing changed\n")
