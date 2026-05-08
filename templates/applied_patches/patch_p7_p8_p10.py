"""P7/P8/P10 - JS IIFE guard (listener accumulation prevention)"""

FILES = [
    (
        r"D:\program\SQM_inventory\SQM_v867_clean\frontend\js\sqm-inline.js",
        "__SQM_INLINE_INSTALLED__",
        "(function () {\n  'use strict';",
        "(function () {\n  'use strict';\n  if (window.__SQM_INLINE_INSTALLED__) return;\n  window.__SQM_INLINE_INSTALLED__ = true;",
    ),
    (
        r"D:\program\SQM_inventory\SQM_v867_clean\frontend\js\sqm-tonbag.js",
        "__SQM_TONBAG_INSTALLED__",
        "(function () {\n  'use strict';",
        "(function () {\n  'use strict';\n  if (window.__SQM_TONBAG_INSTALLED__) return;\n  window.__SQM_TONBAG_INSTALLED__ = true;",
    ),
    (
        r"D:\program\SQM_inventory\SQM_v867_clean\frontend\js\sqm-onestop-inbound.js",
        "__SQM_ONESTOP_INSTALLED__",
        "(function () {\n  'use strict';",
        "(function () {\n  'use strict';\n  if (window.__SQM_ONESTOP_INSTALLED__) return;\n  window.__SQM_ONESTOP_INSTALLED__ = true;",
    ),
]

import subprocess, sys

for src, guard, old, new in FILES:
    fname = src.split("\\")[-1]
    with open(src, 'r', encoding='utf-8') as f:
        content = f.read()

    if guard in content:
        print(fname + " - already applied, skip")
        continue

    count = content.count(old)
    assert count == 1, fname + ": IIFE pattern count=" + str(count)

    content = content.replace(old, new, 1)

    with open(src, 'w', encoding='utf-8', newline='\n') as f:
        raw = content.encode('utf-8').replace(bytes([0x5c, 0x21]), bytes([0x21]))
        f.write(raw.decode('utf-8'))

    result = subprocess.run(['node', '--check', src], capture_output=True, text=True)
    if result.returncode != 0:
        print("FAIL: " + fname)
        print(result.stderr)
        sys.exit(1)

    print(fname + " - OK")

print("P7+P8+P10 all done.")
