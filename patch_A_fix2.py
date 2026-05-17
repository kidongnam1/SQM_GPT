# -*- coding: utf-8 -*-
"""patch_A_fix2.py — showPendingActionMenu innerHTML 방식을 DOM 방식으로 교체"""
from pathlib import Path

f = Path('frontend/js/sqm-inventory.js')
lines = f.read_text(encoding='utf-8').splitlines(keepends=True)

# line 693-698 (0-indexed: 692-697) 교체
# menu.innerHTML 방식 → DOM createElement 방식으로 (따옴표 문제 완전 회피)
NEW_BLOCK = """\
    var item1 = document.createElement('div');
    item1.style.cssText = 'padding:8px 16px;cursor:pointer;font-size:13px;color:var(--text)';
    item1.dataset.lot = lotNo;
    item1.onmouseenter = function() { this.style.background = '#334155'; };
    item1.onmouseleave = function() { this.style.background = ''; };
    item1.onclick = function() {
      window.showPendingConfirmModal(this.dataset.lot);
      var m = document.getElementById('pending-ctx-menu'); if (m) m.remove();
    };
    item1.textContent = '\\u2705 AVAILABLE \\uc785\\uace0 \\ud655\\uc815';
    var item2 = document.createElement('div');
    item2.style.cssText = 'padding:8px 16px;cursor:pointer;font-size:13px;color:var(--text-muted)';
    item2.dataset.lot = lotNo;
    item2.onmouseenter = function() { this.style.background = '#334155'; };
    item2.onmouseleave = function() { this.style.background = ''; };
    item2.onclick = function() {
      window.invShowLotHistory(this.dataset.lot);
      var m = document.getElementById('pending-ctx-menu'); if (m) m.remove();
    };
    item2.textContent = '\\ud83d\\udcca LOT \\uc774\\ub825 \\ubcf4\\uae30';
    menu.appendChild(item1);
    menu.appendChild(item2);
"""

# 찾을 범위: line 693~698 (1-indexed), 즉 index 692~697
start_marker = "    menu.innerHTML = '<div style=\"padding:8px 16px;cursor:pointer;font-size:13px;color:var(--text)\"'"
end_marker = "    document.body.appendChild(menu);"

new_lines = []
skip = False
replaced = False
for line in lines:
    if not replaced and line.rstrip('\n\r') == start_marker.rstrip():
        # 시작 마커 발견 → 새 블록 삽입 후 end_marker까지 skip
        new_lines.append(NEW_BLOCK)
        skip = True
        continue
    if skip:
        if line.strip().startswith('document.body.appendChild(menu)'):
            skip = False
            replaced = True
            new_lines.append(line)
        continue
    new_lines.append(line)

if replaced:
    f.write_text(''.join(new_lines), encoding='utf-8')
    print("DOM 방식으로 교체 완료")
else:
    print("마커를 찾지 못함 — 파일 그대로 유지")
    print("첫 번째 줄 후보:")
    for i, l in enumerate(lines[690:700], 691):
        print(f"  {i}: {repr(l[:80])}")
