# -*- coding: utf-8 -*-
"""
patch_version_869.py
====================
Replace all v8.6.6 / v8.6.8 occurrences with v8.6.9
across frontend JS and HTML files.

Does NOT touch: v864, v864.2, v864.3 (legacy GUI version numbering)
"""

import re, shutil, pathlib, datetime

ROOT   = pathlib.Path(__file__).parent.parent / 'frontend'
STAMP  = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
EXTS   = {'.js', '.html', '.css'}
SKIP   = {'node_modules', '.bak', '.bak_'}

# Patterns to replace (avoid touching v864.x)
PAT = re.compile(r'v8\.6\.[68]')
NEW = 'v8.6.9'

changed = []
skipped = []

def should_skip(path):
    for s in SKIP:
        if s in path.name:
            return True
    return False

files = []
for ext in EXTS:
    files += ROOT.rglob('*' + ext)
files = sorted(files)

for path in files:
    if should_skip(path):
        continue
    try:
        txt = path.read_text(encoding='utf-8', errors='replace')
    except Exception as e:
        skipped.append(str(path.name) + ' [read error: ' + str(e) + ']')
        continue

    if not PAT.search(txt):
        continue

    hits = PAT.findall(txt)
    new_txt = PAT.sub(NEW, txt)

    # Backup
    bak = path.with_suffix(path.suffix + '.bak_ver869_' + STAMP)
    shutil.copy2(path, bak)

    path.write_text(new_txt, encoding='utf-8')
    changed.append(path.name + '  (' + str(len(hits)) + ' replacements)')

print('=== patch_version_869.py ===')
print('Target: v8.6.6 / v8.6.8  ->  v8.6.9')
print()

if changed:
    print('Changed files (' + str(len(changed)) + '):')
    for c in changed:
        print('  OK  ' + c)
else:
    print('No files needed changing.')

if skipped:
    print()
    print('Skipped:')
    for s in skipped:
        print('  -- ' + s)

print()
print('DONE.')
