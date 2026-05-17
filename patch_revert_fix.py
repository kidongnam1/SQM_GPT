# -*- coding: utf-8 -*-
"""patch_revert_fix.py — desc.createTextNode 의 리터럴 개행 제거"""
from pathlib import Path

f = Path('frontend/js/sqm-inventory.js')
lines = f.read_text(encoding='utf-8').splitlines(keepends=True)

# 문제 줄: line 308-310 (0-indexed: 307-309) — 개행 포함된 createTextNode 호출
# 찾아서 단일 줄로 교체
out = []
i = 0
while i < len(lines):
    # 개행 포함된 잘못된 블록 시작 감지
    if "desc.appendChild(document.createTextNode('" in lines[i] and lines[i].rstrip('\n').endswith("('"):
        # 다음 줄들을 end of string 까지 합침
        combined = lines[i].rstrip('\n')
        i += 1
        while i < len(lines) and "'));" not in lines[i] and "'));" not in combined:
            combined += ' ' + lines[i].strip().rstrip('\n')
            i += 1
        if i < len(lines):
            combined += ' ' + lines[i].strip()
            i += 1
        # 단순 설명 텍스트로 교체
        fixed = "    desc.appendChild(document.createTextNode(' \u2192 PENDING \ubcf5\uad6c. inbound_date \ucd08\uae30\ud654 / RESERVED\u00b7PICKED\u00b7SOLD \ud1a4\ubc31 \uc5c6\uc5b4\uc57c \ud569\ub2c8\ub2e4.'));\n"
        out.append(fixed)
        continue
    out.append(lines[i])
    i += 1

f.write_text(''.join(out), encoding='utf-8')
print("fix \uc644\ub8cc")
