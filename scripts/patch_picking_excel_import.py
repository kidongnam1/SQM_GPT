# -*- coding: utf-8 -*-
"""
patch_picking_excel_import.py
-----------------------------
Picking List 엑셀 import 기능 신규 추가.

[A] backend/api/outbound_api.py
    POST /api/outbound/picking-import-excel 엔드포인트 추가.
    Excel → parse_picking_list_excel() → apply_picking_list_to_db() (PDF와 엔진 공유).
[B] frontend/js/sqm-upload-modals.js
    showPickingListExcelModal() 업로드 모달 함수 추가.
[C] frontend/js/sqm-inline.js
    메뉴 레지스트리 + 디스패치에 picking-list-excel 항목 추가.
[D] frontend/js/sqm-tonbag.js
    메뉴 레지스트리 + 디스패처에 picking-list-excel 항목 추가.

Rule 5: outbound_api.py(>1000줄) · 3개 JS(IIFE) → Edit 금지, 본 스크립트로 처리.
"""
import os
import sys
import datetime

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

ROOT = os.path.join(os.path.dirname(__file__), '..')
API = os.path.join(ROOT, 'backend', 'api', 'outbound_api.py')
UPLOAD = os.path.join(ROOT, 'frontend', 'js', 'sqm-upload-modals.js')
INLINE = os.path.join(ROOT, 'frontend', 'js', 'sqm-inline.js')
TONBAG = os.path.join(ROOT, 'frontend', 'js', 'sqm-tonbag.js')

# ════════════════════════════════════════════════════════════════════
# [A] outbound_api.py — picking-import-excel 엔드포인트
# ════════════════════════════════════════════════════════════════════
A_ENDPOINT = '''@router.post("/picking-import-excel", summary="\U0001F4CB Picking List Excel 업로드 (피킹 이력 반영)")
async def picking_import_excel(file: UploadFile = File(...)):
    """
    Picking List Excel(.xlsx/.xls) 파싱 → apply_picking_list_to_db() 호출.
    PDF(picking-list-pdf)와 동일한 picking_engine 을 공유한다.
    """
    if not file.filename:
        raise HTTPException(400, "파일명 없음")
    if not file.filename.lower().endswith((".xlsx", ".xls")):
        raise HTTPException(400, f"Excel 파일만 지원. 받은 파일: {file.filename}")

    try:
        from backend.api import engine, ENGINE_AVAILABLE
    except Exception as e:
        raise HTTPException(500, f"엔진 로드 실패: {e}")
    if not ENGINE_AVAILABLE or engine is None:
        raise HTTPException(500, "엔진 사용 불가")

    try:
        from features.parsers.picking_excel_parser import parse_picking_list_excel
        from features.parsers.picking_engine import apply_picking_list_to_db
    except ImportError as e:
        raise HTTPException(500, f"Picking 엔진 import 실패: {e}")

    tmp_path = None
    try:
        content = await file.read()
        if not content:
            raise HTTPException(400, "빈 파일")
        ext = os.path.splitext(file.filename)[1].lower()
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name
        logger.info(f"[picking-import-excel] 수신: {file.filename} ({len(content)} bytes)")

        doc = parse_picking_list_excel(tmp_path)
        if not doc.get("parse_ok"):
            return {
                "ok": False,
                "data": {
                    "filename": file.filename,
                    "parse_ok": False,
                    "warnings": doc.get("warnings", []),
                    "total_lots": doc.get("total_lots", 0),
                    "items": doc.get("items", [])[:10],
                },
                "error": "Picking List Excel 파싱 실패",
                "detail": {"code": "PARSE_FAILED", "warnings": doc.get("warnings", [])},
                "message": "Picking List Excel 파싱 실패 — 파일 내용을 확인해주세요",
            }

        result = apply_picking_list_to_db(engine, doc, tmp_path)

        if result.get("success"):
            applied = int(result.get("applied", 0) or result.get("picked", 0) or 0)
            logger.info(f"[picking-import-excel] 반영 완료: {applied}건 ({file.filename})")
            return {
                "ok": True,
                "data": {
                    "filename": file.filename,
                    "parse_method": doc.get("parse_method"),
                    "total_lots": doc.get("total_lots", 0),
                    "total_normal_mt": doc.get("total_normal_mt", 0),
                    "total_sample_kg": doc.get("total_sample_kg", 0),
                    "applied": applied,
                    "warnings": doc.get("warnings", []),
                    "details": result.get("details", [])[:30],
                },
                "message": f"Picking List 반영 완료 ({applied}건)",
            }
        return {
            "ok": False,
            "data": {
                "filename": file.filename,
                "total_lots": doc.get("total_lots", 0),
                "errors": result.get("errors", []),
                "warnings": doc.get("warnings", []),
            },
            "error": "Picking List 반영 실패",
            "detail": {"code": "APPLY_FAILED", "errors": result.get("errors", [])},
            "message": "DB 반영 실패 — 상세 errors 확인",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"[picking-import-excel] 에러: {e}")
        raise HTTPException(500, f"Internal error: {e}")
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except Exception:
                pass
'''

A_OLD = "# F016 빠른 출고 (붙여넣기) — 여러 LOT 텍스트 → 일괄 즉시 출고"
A_NEW = (A_ENDPOINT
         + "\n\n# ─────────────────────────────────────────────────────────────\n"
         + A_OLD)

# ════════════════════════════════════════════════════════════════════
# [B] sqm-upload-modals.js — showPickingListExcelModal()
# ════════════════════════════════════════════════════════════════════
B_OLD = "  window.showPickingListPdfModal = showPickingListPdfModal;"
B_MODAL = r'''
  /* Picking List Excel 업로드 (피킹 이력 반영) */
  function showPickingListExcelModal() {
    _showExcelUploadModal({
      title: '📋 Picking List Excel 업로드',
      subtitle: 'Picking List Excel(.xlsx) 을 업로드하면 자동 파싱하여 picking_table 에 반영합니다.',
      endpoint: '/api/outbound/picking-import-excel',
      onSuccess: function(d) {
        var warnHtml = '';
        if (d.warnings && d.warnings.length) {
          warnHtml = '<details style="margin-top:8px"><summary style="cursor:pointer;color:var(--warning)">⚠️ 경고 ' + d.warnings.length + '건</summary><pre style="white-space:pre-wrap;font-size:.8rem;margin-top:8px">' + escapeHtml(d.warnings.join('\n')) + '</pre></details>';
        }
        return '<div style="color:var(--text-muted);font-size:.85rem">파일: ' + escapeHtml(d.filename||'-') +
               ' · 방법: ' + escapeHtml(d.parse_method||'-') +
               ' · LOT ' + (d.total_lots||0) + '개 · 일반 ' + (d.total_normal_mt||0) + ' MT · 샘플 ' + (d.total_sample_kg||0) + ' KG' +
               ' · <strong style="color:var(--accent)">반영 ' + (d.applied||0) + '건</strong>' +
               '</div>' + warnHtml;
      }
    });
  }
  window.showPickingListExcelModal = showPickingListExcelModal;'''
B_NEW = B_OLD + B_MODAL

# ════════════════════════════════════════════════════════════════════
# [C] sqm-inline.js — 메뉴 레지스트리 + 디스패치
# ════════════════════════════════════════════════════════════════════
C1_OLD = "    'onPickingListUpload':  {m:'JS', u:'picking-list-pdf', lbl:'Picking List 업로드 (PDF)'},"
C1_NEW = (C1_OLD
          + "\n    'onPickingListExcelUpload':  {m:'JS', u:'picking-list-excel', lbl:'Picking List 업로드 (Excel)'},")

C2_OLD = "    'picking-list-pdf': function(){ window.showPickingListPdfModal(); },"
C2_NEW = (C2_OLD
          + "\n    'picking-list-excel': function(){ window.showPickingListExcelModal(); },")

# ════════════════════════════════════════════════════════════════════
# [D] sqm-tonbag.js — 메뉴 레지스트리 + 디스패처
# ════════════════════════════════════════════════════════════════════
D1_OLD = C1_OLD
D1_NEW = C1_NEW

D2_OLD = (
    "      if (conf.u === 'picking-list-pdf') {\n"
    "        showPickingListPdfModal();\n"
    "        return;\n"
    "      }"
)
D2_NEW = (
    D2_OLD
    + "\n      if (conf.u === 'picking-list-excel') {\n"
    "        window.showPickingListExcelModal();\n"
    "        return;\n"
    "      }"
)

TARGETS = [
    (API,    'picking-import-excel',     [('[A] picking-import-excel 엔드포인트', A_OLD, A_NEW)]),
    (UPLOAD, 'showPickingListExcelModal', [('[B] showPickingListExcelModal 모달', B_OLD, B_NEW)]),
    (INLINE, "'picking-list-excel'",      [('[C1] 메뉴 레지스트리', C1_OLD, C1_NEW),
                                           ('[C2] 디스패치', C2_OLD, C2_NEW)]),
    (TONBAG, "'picking-list-excel'",      [('[D1] 메뉴 레지스트리', D1_OLD, D1_NEW),
                                           ('[D2] 디스패처', D2_OLD, D2_NEW)]),
]


def apply(path, guard, repls):
    name = os.path.basename(path)
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    orig = content
    if guard in content:
        print('[SKIP] %s — 이미 패치됨 (%s)' % (name, guard))
        return True
    errors = []
    for label, old, _new in repls:
        n = content.count(old)
        if n != 1:
            errors.append('  [%s] 발견 횟수 %d (기대 1)' % (label, n))
    if errors:
        print('[FAIL] %s — 패턴 불일치, 중단:' % name)
        print('\n'.join(errors))
        return False
    for label, old, new in repls:
        content = content.replace(old, new, 1)
        print('  · %s' % label)
    ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    bak = path + '.bak_pickexcel_' + ts
    with open(bak, 'w', encoding='utf-8') as f:
        f.write(orig)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print('[OK] %s 패치 완료 (백업: %s)' % (name, os.path.basename(bak)))
    return True


def main():
    print('=== Picking List 엑셀 import 기능 추가 ===')
    ok = True
    for path, guard, repls in TARGETS:
        print('-- %s --' % os.path.basename(path))
        ok &= apply(path, guard, repls)
    print('=== %s ===' % ('완료' if ok else '실패 — 위 로그 확인'))
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
