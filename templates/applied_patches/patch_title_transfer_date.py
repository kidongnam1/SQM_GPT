"""피킹일 -> Title Transfer Date 라벨 변경"""
import subprocess, sys

FILES = [
    r"D:\program\SQM_inventory\SQM_v867_clean\frontend\js\sqm-picked.js",
    r"D:\program\SQM_inventory\SQM_v867_clean\frontend\js\sqm-inline.js",
]

for src in FILES:
    fname = src.split("\\")[-1]
    with open(src, 'r', encoding='utf-8') as f:
        content = f.read()

    before = content.count('피킹일')
    if before == 0:
        print(fname + " - no 피킹일 found, skip")
        continue

    content = content.replace('피킹일', 'Title Transfer Date')

    after = content.count('피킹일')
    print(fname + " - replaced " + str(before - after) + " occurrences")

    with open(src, 'w', encoding='utf-8', newline='\n') as f:
        raw = content.encode('utf-8').replace(bytes([0x5c, 0x21]), bytes([0x21]))
        f.write(raw.decode('utf-8'))

    result = subprocess.run(['node', '--check', src], capture_output=True, text=True)
    if result.returncode != 0:
        print("FAIL: " + fname)
        print(result.stderr)
        sys.exit(1)
    print(fname + " - syntax OK")

print("Done.")
