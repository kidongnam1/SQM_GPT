# -*- coding: utf-8 -*-
"""
patch_sample_row_and_context_menus.py
======================================
Purpose: 3가지 동시 패치
  1) Available 샘플 행 칼럼 정렬 — LOT(SP)를 LOT 헤더 자리로 이동
  2) Picked 우클릭 메뉴에 ↩ PICKED → RESERVED 추가
  3) Outbound 우클릭 메뉴 신규 생성 + ↩ SOLD → PICKED 추가
Why    : 사용자 보고 — 샘플 행 칸 정렬 안 맞음, Picked/Outbound 우클릭 취소 없음
Rule   : CLAUDE.md Rule 5 — Python 스크립트만
Author : Ruby (Senior Software Architect) — 2026-05-16
"""
import sys
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
INV = ROOT / "frontend" / "js" / "sqm-inventory.js"
PICKED = ROOT / "frontend" / "js" / "sqm-picked.js"
LOGISTICS = ROOT / "frontend" / "js" / "sqm-logistics.js"

# ────────────────────────────────────────────────────────────
# 1. sqm-inventory.js: Available 샘플 행 칼럼 정렬
# ────────────────────────────────────────────────────────────
INV_SAMPLE_ANCHOR = """        if (hasSample) {
          sampleRow =
            '<tr style="background:rgba(234,179,8,0.08);border-left:3px solid #eab308">' +
            '<td class="mono-cell" style="color:#eab308;text-align:center;padding:6px 10px">🔬</td>' +
            '<td class="mono-cell cell-left" style="color:#eab308;font-weight:700;padding:6px 10px">' + lotKey + '(SP)</td>' +
            '<td class="mono-cell" style="color:#555">—</td>' +
            '<td class="mono-cell" style="color:#94a3b8">' + escapeHtml(r.sap||'') + '</td>' +
            '<td class="mono-cell" style="color:#94a3b8">' + escapeHtml(r.bl||'') + '</td>' +
            '<td><span class="tag" style="background:rgba(234,179,8,0.2);color:#eab308">' + escapeHtml(r.product||'') + '</span></td>' +
            '<td style="color:#eab308;font-weight:600">SAMPLE</td>' +
            '<td class="mono-cell" style="text-align:right;color:#eab308;font-weight:600">' + fmtN(r.sample_weight_mt||0) + '</td>' +
            '<td class="mono-cell" style="text-align:right;color:#eab308">' + fmtN(r.sample_weight_mt||0) + '</td>' +
            '<td class="mono-cell" style="color:#94a3b8">' + parentContainer + '</td>' +
            '<td class="mono-cell" style="text-align:center;color:#eab308;font-weight:700">' + r.sample_bags + '</td>' +
            '<td class="mono-cell" style="text-align:center;color:#eab308;font-weight:700">' + r.sample_bags + '</td>' +
            '<td class="mono-cell" style="text-align:center;color:#555">0</td>' +
            '<td class="mono-cell" style="text-align:center;color:#555">0</td>' +
            '<td class="mono-cell" style="text-align:center;color:#eab308;font-weight:700">' + r.sample_bags + '</td>' +
            '<td class="mono-cell" style="text-align:center;color:#555">0</td>' +
            '<td class="mono-cell" style="text-align:right;color:#eab308">' + fmtN(r.sample_weight_mt||0) + '</td>' +
            '<td class="mono-cell" style="text-align:right;color:#555">0</td>' +
            '<td class="mono-cell" style="text-align:right;color:#555">0</td>' +
            '<td colspan="8" style="color:#555">—</td>' +
            '</tr>';
        }"""

# 일반 행 매핑 (28칼럼):
# 1:체크박스 2:# 3:LOT 4:+ 5:SAP 6:BL 7:Product 8:Status 9:↩ 10:Balance 11:NET
# 12:Container 13:MXBG 14:Available 15:Reserved 16:Packed 17:Total 18:Remain
# 19:AV 20:VR 21:AR 22:Invoice 23:Ship 24:Arrival 25:WH 26:Customs 27:Inbound(MT) 28:Location
INV_SAMPLE_PATCH = """        if (hasSample) {
          // v868 fix (2026-05-16): 샘플 행을 일반 행과 동일한 28칼럼 매핑으로 정렬
          // LOT(SP)를 LOT 헤더(3번 칼럼)로 이동, 나머지 칼럼도 1칸씩 정렬
          sampleRow =
            '<tr style="background:rgba(234,179,8,0.08);border-left:3px solid #eab308">' +
            // 1:체크박스 자리 - 🔬
            '<td style="text-align:center;padding:6px 10px;color:#eab308">🔬</td>' +
            // 2:# 자리 - SP
            '<td class="mono-cell" style="color:#eab308;text-align:center">SP</td>' +
            // 3:LOT 자리 - LOT(SP) ← 핵심: LOT 헤더로 이동
            '<td class="mono-cell cell-left" style="color:#eab308;font-weight:700;padding:6px 10px">' + lotKey + '(SP)</td>' +
            // 4:+ 자리 - 빈 (—)
            '<td style="text-align:center;color:#555">—</td>' +
            // 5:SAP
            '<td class="mono-cell" style="color:#94a3b8">' + escapeHtml(r.sap||'') + '</td>' +
            // 6:BL
            '<td class="mono-cell" style="color:#94a3b8">' + escapeHtml(r.bl||'') + '</td>' +
            // 7:Product
            '<td><span class="tag" style="background:rgba(234,179,8,0.2);color:#eab308">' + escapeHtml(r.product||'') + '</span></td>' +
            // 8:Status
            '<td style="color:#eab308;font-weight:600">SAMPLE</td>' +
            // 9:↩ 자리 - 빈
            '<td style="text-align:center;color:#555">—</td>' +
            // 10:Balance(MT)
            '<td class="mono-cell" style="text-align:right;color:#eab308;font-weight:600">' + fmtN(r.sample_weight_mt||0) + '</td>' +
            // 11:NET(MT)
            '<td class="mono-cell" style="text-align:right;color:#eab308">' + fmtN(r.sample_weight_mt||0) + '</td>' +
            // 12:Container
            '<td class="mono-cell" style="color:#94a3b8">' + parentContainer + '</td>' +
            // 13:MXBG 자리 - 빈
            '<td class="mono-cell" style="text-align:center;color:#555">—</td>' +
            // 14:Available bags
            '<td class="mono-cell" style="text-align:center;color:#eab308;font-weight:700">' + r.sample_bags + '</td>' +
            // 15:Reserved
            '<td class="mono-cell" style="text-align:center;color:#555">0</td>' +
            // 16:Packed
            '<td class="mono-cell" style="text-align:center;color:#555">0</td>' +
            // 17:Total Bags
            '<td class="mono-cell" style="text-align:center;color:#eab308;font-weight:700">' + r.sample_bags + '</td>' +
            // 18:Remain
            '<td class="mono-cell" style="text-align:center;color:#555">0</td>' +
            // 19:AV
            '<td class="mono-cell" style="text-align:right;color:#eab308">' + fmtN(r.sample_weight_mt||0) + '</td>' +
            // 20:VR
            '<td class="mono-cell" style="text-align:right;color:#555">0</td>' +
            // 21:AR
            '<td class="mono-cell" style="text-align:right;color:#555">0</td>' +
            // 22-28: Invoice/Ship/Arrival/WH/Customs/Inbound/Location (7칼럼) - colspan
            '<td colspan="7" style="color:#555;text-align:center">—</td>' +
            '</tr>';
        }"""

# ────────────────────────────────────────────────────────────
# 2. sqm-picked.js: 우클릭 메뉴에 ↩ PICKED → RESERVED 추가
# ────────────────────────────────────────────────────────────
PICKED_MENU_ANCHOR = """  window.showPickedActionMenu = function(btn) {
    var lot = btn.dataset.lot || '';
    window._openContextMenu(btn, [
      { icon:'📋', label:'LOT 상세 보기',  kbd:'Enter',  fn:function(){ if(window.showLotDetail) window.showLotDetail(lot); } },
      { icon:'📄', label:'LOT 번호 복사',  kbd:'Ctrl+C', fn:function(){ navigator.clipboard&&navigator.clipboard.writeText(lot); showToast('info','LOT 복사: '+lot); } },
      '-',
      { icon:'▶',  label:'피킹 상세 열기', kbd:'Space',  color:'#f59e0b', fn:function(){ window.togglePickedDetail(lot); } },
    ]);
  };"""

PICKED_MENU_PATCH = """  window.showPickedActionMenu = function(btn) {
    var lot = btn.dataset.lot || '';
    window._openContextMenu(btn, [
      { icon:'📋', label:'LOT 상세 보기',  kbd:'Enter',  fn:function(){ if(window.showLotDetail) window.showLotDetail(lot); } },
      { icon:'📄', label:'LOT 번호 복사',  kbd:'Ctrl+C', fn:function(){ navigator.clipboard&&navigator.clipboard.writeText(lot); showToast('info','LOT 복사: '+lot); } },
      '-',
      { icon:'▶',  label:'피킹 상세 열기', kbd:'Space',  color:'#f59e0b', fn:function(){ window.togglePickedDetail(lot); } },
      // v868 fix (2026-05-16): 취소 기능 추가 — PICKED → RESERVED 되돌리기
      '-',
      { icon:'↩',  label:'PICKED → RESERVED 되돌리기', color:'#ef4444', fn:function(){
          if (!confirm('↩ ' + lot + '\\nPICKED → RESERVED로 되돌리시겠습니까?')) return;
          if (window.allocRevertStep) {
            window.allocRevertStep('PICKED');
          } else {
            alert('되돌리기 함수를 찾을 수 없습니다 (allocRevertStep)');
          }
      } },
    ]);
  };"""

# ────────────────────────────────────────────────────────────
# 3. sqm-logistics.js: Outbound 행에 ⋯ 버튼 추가 + 우클릭 메뉴 신규 생성
# ────────────────────────────────────────────────────────────
LOGISTICS_ROW_ANCHOR = """        return '<tr class="outbound-summary-row" data-lot="'+lot+'" style="cursor:pointer" onclick="window.toggleOutboundDetail(\\'\'+lot+\'\\')">' +
          '<td style="width:24px;text-align:center"><span class="outbound-expand-icon">▶</span></td>' +
          '<td class="mono-cell" style="color:var(--text-muted)">'+(i+1)+'</td>' +
          '<td class="mono-cell" style="color:var(--accent);font-weight:600">'+lot+'</td>' +
          '<td class="mono-cell">'+escapeHtml(r.sales_order_no||'-')+'</td>' +
          '<td>'+escapeHtml(r.customer||'-')+'</td>' +
          '<td class="mono-cell" style="text-align:right">'+(r.tonbag_count||0)+'</td>' +
          '<td class="mono-cell" style="text-align:right">'+(r.total_kg!=null?fmtN(r.total_kg):'-')+'</td>' +
          '<td class="mono-cell">'+escapeHtml(r.sold_date||'-')+'</td>' +
          '</tr>';"""

LOGISTICS_ROW_PATCH = """        return '<tr class="outbound-summary-row" data-lot="'+lot+'" style="cursor:pointer" onclick="window.toggleOutboundDetail(\\'\'+lot+\'\\')">' +
          '<td style="width:24px;text-align:center"><span class="outbound-expand-icon">▶</span></td>' +
          '<td class="mono-cell" style="color:var(--text-muted)">'+(i+1)+'</td>' +
          '<td class="mono-cell" style="color:var(--accent);font-weight:600">'+lot+'</td>' +
          // v868 fix (2026-05-16): 우클릭 메뉴 버튼 추가
          '<td style="text-align:center;padding:3px 4px;width:32px"><button class="btn btn-ghost btn-xs" data-lot="'+lot+'" onclick="event.stopPropagation();window.showOutboundActionMenu(this)" style="font-size:15px;padding:0 4px;letter-spacing:1px" title="추가기능">⋯</button></td>' +
          '<td class="mono-cell">'+escapeHtml(r.sales_order_no||'-')+'</td>' +
          '<td>'+escapeHtml(r.customer||'-')+'</td>' +
          '<td class="mono-cell" style="text-align:right">'+(r.tonbag_count||0)+'</td>' +
          '<td class="mono-cell" style="text-align:right">'+(r.total_kg!=null?fmtN(r.total_kg):'-')+'</td>' +
          '<td class="mono-cell">'+escapeHtml(r.sold_date||'-')+'</td>' +
          '</tr>';"""

# 헤더 컬럼도 추가
LOGISTICS_HEAD_ANCHOR = """      '  <thead><tr><th></th><th>#</th><th>LOT No</th><th>판매주문No</th><th>고객사</th><th>톤백수</th><th>중량(kg)</th><th>출고일</th></tr></thead>',"""

LOGISTICS_HEAD_PATCH = """      '  <thead><tr><th></th><th>#</th><th>LOT No</th><th style="width:32px">⋯</th><th>판매주문No</th><th>고객사</th><th>톤백수</th><th>중량(kg)</th><th>출고일</th></tr></thead>',"""

# Outbound 우클릭 메뉴 함수 추가 — toggleOutboundDetail 직전에 삽입
LOGISTICS_MENU_ANCHOR = """  var _outboundExpandedLot = null;
  window.toggleOutboundDetail = function(lotNo) {"""

LOGISTICS_MENU_PATCH = """  // v868 fix (2026-05-16): Outbound 우클릭 메뉴 신규 — 취소 기능 (SOLD → PICKED)
  window.showOutboundActionMenu = function(btn) {
    var lot = btn.dataset.lot || '';
    if (window._openContextMenu) {
      window._openContextMenu(btn, [
        { icon:'📋', label:'LOT 상세 보기', fn:function(){ if(window.showLotDetail) window.showLotDetail(lot); } },
        { icon:'📄', label:'LOT 번호 복사', fn:function(){ navigator.clipboard && navigator.clipboard.writeText(lot); showToast('info','LOT 복사: '+lot); } },
        '-',
        { icon:'↩', label:'SOLD → PICKED 되돌리기', color:'#ef4444', fn:function(){
            if (!confirm('↩ ' + lot + '\\nSOLD → PICKED로 되돌리시겠습니까?')) return;
            if (window.allocRevertStep) {
              window.allocRevertStep('SOLD');
            } else {
              alert('되돌리기 함수를 찾을 수 없습니다');
            }
        } },
      ]);
    } else {
      // _openContextMenu 미정의 시 fallback — confirm 직접 사용
      if (confirm('↩ ' + lot + '\\nSOLD → PICKED로 되돌리시겠습니까?')) {
        if (window.allocRevertStep) window.allocRevertStep('SOLD');
      }
    }
  };

  var _outboundExpandedLot = null;
  window.toggleOutboundDetail = function(lotNo) {"""


def apply_patch(file_path: Path, anchor: str, patch: str, label: str) -> bool:
    text = file_path.read_text(encoding="utf-8")
    if patch in text:
        print(f"  [SKIP] {label} — already patched.")
        return True
    if anchor not in text:
        print(f"  [ERROR] {label} — anchor not found.")
        return False
    if text.count(anchor) > 1:
        print(f"  [ERROR] {label} — anchor matched {text.count(anchor)} times.")
        return False
    new_text = text.replace(anchor, patch, 1)
    file_path.write_text(new_text, encoding="utf-8")
    print(f"  [OK] {label} applied.")
    return True


def main() -> int:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    for f in (INV, PICKED, LOGISTICS):
        shutil.copy2(f, f.with_suffix(f".js.bak_sample_menus_{ts}"))
    print(f"[INFO] 3 backups created with suffix .bak_sample_menus_{ts}")
    print()

    print("=== sqm-inventory.js: 샘플 행 칼럼 정렬 ===")
    ok = apply_patch(INV, INV_SAMPLE_ANCHOR, INV_SAMPLE_PATCH, "(S) 샘플 행 28칼럼 매핑")

    print()
    print("=== sqm-picked.js: 우클릭 메뉴에 취소 추가 ===")
    ok &= apply_patch(PICKED, PICKED_MENU_ANCHOR, PICKED_MENU_PATCH, "(P) Picked 우클릭 취소")

    print()
    print("=== sqm-logistics.js: Outbound 우클릭 메뉴 신규 ===")
    ok &= apply_patch(LOGISTICS, LOGISTICS_HEAD_ANCHOR, LOGISTICS_HEAD_PATCH, "(O-H) Outbound 헤더 컬럼")
    ok &= apply_patch(LOGISTICS, LOGISTICS_ROW_ANCHOR, LOGISTICS_ROW_PATCH, "(O-R) Outbound 행에 ⋯ 버튼")
    ok &= apply_patch(LOGISTICS, LOGISTICS_MENU_ANCHOR, LOGISTICS_MENU_PATCH, "(O-M) Outbound 우클릭 메뉴 신규")

    if not ok:
        return 2

    # syntax 검증
    print()
    for f in (INV, PICKED, LOGISTICS):
        r = subprocess.run(["node", "--check", str(f)], capture_output=True, text=True)
        if r.returncode != 0:
            print(f"[FAIL] {f.name}: {r.stderr}")
            return 3
        print(f"[OK] {f.name} syntax OK")

    print()
    print("🎉 3가지 패치 완료")
    return 0


if __name__ == "__main__":
    sys.exit(main())
