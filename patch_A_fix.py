# -*- coding: utf-8 -*-
"""patch_A_fix.py — onmouseenter 따옴표 수정"""
from pathlib import Path

f = Path('frontend/js/sqm-inventory.js')
src = f.read_text(encoding='utf-8')

# onmouseenter/onclick 줄 수정 — CSS 변수 대신 #334155 직접 사용하고 이스케이프 정정
OLD = (
    "    menu.innerHTML = '<div style=\"padding:8px 16px;cursor:pointer;font-size:13px;color:var(--text)\"'\n"
    "      + ' onmouseenter=\"this.style.background='var(--border,#334155)'\" onmouseleave=\"this.style.background=''\"'\n"
    "      + ' onclick=\"window.showPendingConfirmModal('' + escapeHtml(lotNo) + '');document.getElementById('pending-ctx-menu').remove()\">\u2705 AVAILABLE \uc785\uace0 \ud655\uc815</div>'\n"
    "      + '<div style=\"padding:8px 16px;cursor:pointer;font-size:13px;color:var(--text-muted)\"'\n"
    "      + ' onmouseenter=\"this.style.background='var(--border,#334155)'\" onmouseleave=\"this.style.background=''\"'\n"
    "      + ' onclick=\"window.invShowLotHistory('' + escapeHtml(lotNo) + '');document.getElementById('pending-ctx-menu').remove()\">\ud83d\udcca LOT \uc774\ub825 \ubcf4\uae30</div>';"
)
NEW = (
    "    menu.innerHTML = '<div style=\"padding:8px 16px;cursor:pointer;font-size:13px;color:var(--text)\"'\n"
    "      + ' onmouseenter=\"this.style.background=\\'#334155\\'\" onmouseleave=\"this.style.background=\\'\\'\""
    "      + '\"'\n"
    "      + ' onclick=\"window.showPendingConfirmModal(\\''+escapeHtml(lotNo)+'\\');document.getElementById(\\'pending-ctx-menu\\').remove()\">\u2705 AVAILABLE \uc785\uace0 \ud655\uc815</div>'\n"
    "      + '<div style=\"padding:8px 16px;cursor:pointer;font-size:13px;color:var(--text-muted)\"'\n"
    "      + ' onmouseenter=\"this.style.background=\\'#334155\\'\" onmouseleave=\"this.style.background=\\'\\'\""
    "      + '\"'\n"
    "      + ' onclick=\"window.invShowLotHistory(\\''+escapeHtml(lotNo)+'\\');document.getElementById(\\'pending-ctx-menu\\').remove()\">\ud83d\udcca LOT \uc774\ub825 \ubcf4\uae30</div>';"
)

if OLD in src:
    src = src.replace(OLD, NEW, 1)
    f.write_text(src, encoding='utf-8')
    print("수정 완료")
else:
    print("대상 못 찾음 — 수동 수정 필요")
    # 대안: 해당 줄만 직접 재작성
    lines = src.splitlines(keepends=True)
    out = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if "onmouseenter=\"this.style.background='var(--border" in line:
            # onmouseenter 줄 → 단순 hover 이벤트로 교체
            line = line.replace(
                "onmouseenter=\"this.style.background='var(--border,#334155)'\" onmouseleave=\"this.style.background=''\"",
                "onmouseenter=\"this.style.background='#334155'\" onmouseleave=\"this.style.background=''\""
            )
        if "onclick=\"window.showPendingConfirmModal('' +" in line:
            line = line.replace(
                "onclick=\"window.showPendingConfirmModal('' + escapeHtml(lotNo) + '');document.getElementById('pending-ctx-menu').remove()\"",
                "onclick=\"window.showPendingConfirmModal('\"+ escapeHtml(lotNo) +\"');document.getElementById('pending-ctx-menu').remove()\""
            )
        if "onclick=\"window.invShowLotHistory('' +" in line:
            line = line.replace(
                "onclick=\"window.invShowLotHistory('' + escapeHtml(lotNo) + '');document.getElementById('pending-ctx-menu').remove()\"",
                "onclick=\"window.invShowLotHistory('\"+ escapeHtml(lotNo) +\"');document.getElementById('pending-ctx-menu').remove()\""
            )
        out.append(line)
        i += 1
    result = ''.join(out)
    f.write_text(result, encoding='utf-8')
    print("대안 수정 완료")
