# -*- coding: utf-8 -*-
"""
patch_alloc_template_wiring.py
------------------------------
[양식 가져오기]로 등록한 .json 템플릿을 실제 Allocation import 에 연결한다.

문제: template-upload 가 resources/templates/allocation/*.json 을 저장하지만,
      bulk-import-excel 은 그 파일을 한 번도 읽지 않음 → 등록 양식이 죽은 데이터.

수정:
  1. _rows_from_registered_templates() 신규 함수 추가
     - 등록된 각 .json 템플릿의 sheet/header_row 를 적용해 Excel 파싱 시도
     - 컬럼 시그니처가 충분히 일치하면 표준 키 매핑 수행
  2. bulk_import_allocation() 에 Stage 2.5(등록 템플릿 폴백) 단계 삽입
     - 순서: ①alias → ②정본 AllocationParser → ②.5 등록 템플릿 → ③Gemini AI
  3. _mapping_source 에 '등록템플릿(...)' 출처 반영

Rule 5 ①: allocation_api.py 1122줄(>1000) → Edit 금지, 본 스크립트로 처리.
"""
import os
import sys
import datetime

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

PATH = os.path.join(os.path.dirname(__file__), '..', 'backend', 'api', 'allocation_api.py')

# ── 신규 함수 ─────────────────────────────────────────────────────────
NEW_FUNC = '''def _rows_from_registered_templates(excel_path: str):
    """등록된 .json 템플릿(resources/templates/allocation/*.json)으로 파싱 시도.

    각 템플릿의 sheet / header_row 를 적용해 Excel 을 읽고, 컬럼 시그니처가
    충분히 일치하면 표준 키 매핑(_match_alloc_columns)을 수행한다.
    [양식 가져오기]로 등록한 외부 양식을 실제 import 에 연결하는 단계.
    반환: (df, header_0based, col_map, template_id) 또는 (None, None, None, None)
    """
    import json as __json
    try:
        import pandas as pd
    except ImportError:
        return None, None, None, None
    try:
        base = _alloc_template_dir()
    except Exception as exc:
        logger.debug("[allocation-import] 템플릿 디렉터리 접근 실패: %s", exc)
        return None, None, None, None

    for jf in sorted(base.glob('*.json')):
        try:
            tpl = __json.loads(jf.read_text(encoding='utf-8'))
        except Exception:
            continue
        header_row = tpl.get('header_row')          # 1-based
        if not isinstance(header_row, int) or header_row < 1:
            continue
        sheet = tpl.get('sheet')
        tpl_cols = {str(c).strip().lower()
                    for c in (tpl.get('columns') or []) if str(c).strip()}
        try:
            read_kw = {'header': header_row - 1}
            if sheet and sheet not in ('자동선택', ''):
                read_kw['sheet_name'] = sheet
            df = pd.read_excel(excel_path, **read_kw)
        except Exception as exc:
            logger.debug("[allocation-import] 템플릿 %s 적용 실패: %s", jf.stem, exc)
            continue
        if df is None or df.empty:
            continue
        # 시그니처 검증 — 업로드 파일 컬럼이 템플릿 columns 와 충분히 겹쳐야 함
        file_cols = {str(c).strip().lower() for c in df.columns if str(c).strip()}
        if tpl_cols:
            overlap = len(file_cols & tpl_cols)
            if overlap < max(2, len(tpl_cols) // 2):
                continue                            # 이 템플릿 양식 아님
        col_map = _match_alloc_columns(df.columns)
        if 'lot_no' in col_map and ('sold_to' in col_map or 'qty_mt' in col_map):
            logger.info(
                "[allocation-import] 등록 템플릿 매칭: %s (header=%d행)",
                tpl.get('id', jf.stem), header_row,
            )
            return df, header_row - 1, col_map, tpl.get('id', jf.stem)
    return None, None, None, None
'''

# ── 치환 1: 신규 함수 삽입 (bulk-import-excel 데코레이터 직전) ──────────
OLD1 = '@router.post("/bulk-import-excel", summary="📍 Allocation 입력 — Excel 업로드 (F014)")'
NEW1 = NEW_FUNC + '\n\n' + OLD1

# ── 치환 2: Stage 2.5(등록 템플릿 폴백) 단계 삽입 ──────────────────────
OLD2 = (
    "        # Stage 3: Gemini AI 폴백 — alias + 정본 파서 모두 실패 시\n"
    "        if (df is None or df.empty) and not canonical_rows:\n"
    "            logger.info(\"[allocation-import] alias/정본 파서 실패 → Gemini AI 폴백 시도\")"
)
NEW2 = (
    "        # Stage 2.5: 등록된 .json 템플릿 폴백 — [양식 가져오기]로 등록한 외부 양식 적용\n"
    "        tpl_used = None\n"
    "        if (df is None or df.empty) and not canonical_rows:\n"
    "            _t_df, _t_header, _t_map, _t_id = _rows_from_registered_templates(tmp_path)\n"
    "            if _t_df is not None:\n"
    "                df = _t_df\n"
    "                header_used = _t_header\n"
    "                col_map_override = _t_map\n"
    "                tpl_used = _t_id\n"
    "                logger.info(\"[allocation-import] alias/정본 파서 실패 → 등록 템플릿 폴백 성공: id=%s\", _t_id)\n"
    "\n"
    "        # Stage 3: Gemini AI 폴백 — alias + 정본 파서 + 등록 템플릿 모두 실패 시\n"
    "        if (df is None or df.empty) and not canonical_rows:\n"
    "            logger.info(\"[allocation-import] alias/정본/템플릿 실패 → Gemini AI 폴백 시도\")"
)

# ── 치환 3: _mapping_source 에 등록 템플릿 출처 반영 ──────────────────
OLD3 = '        _mapping_source = "정본파서" if canonical_rows else ("AI폴백" if col_map_override else "alias")'
NEW3 = (
    "        _mapping_source = (\n"
    "            \"정본파서\" if canonical_rows\n"
    "            else (\"등록템플릿(\" + str(tpl_used) + \")\") if tpl_used\n"
    "            else (\"AI폴백\" if col_map_override else \"alias\")\n"
    "        )"
)

REPLS = [('신규 함수 _rows_from_registered_templates', OLD1, NEW1),
         ('Stage 2.5 등록 템플릿 폴백 단계', OLD2, NEW2),
         ('_mapping_source 출처 반영', OLD3, NEW3)]


def main():
    print('=== Allocation 등록 템플릿 → import 연결 패치 ===')
    with open(PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    orig = content

    # 사전 검증
    errors = []
    for label, old, _new in REPLS:
        n = content.count(old)
        if n != 1:
            errors.append('  [%s] 발견 횟수 %d (기대 1)' % (label, n))
    # 이미 패치됐는지 확인
    if '_rows_from_registered_templates' in content and content.count('def _rows_from_registered_templates') >= 1:
        errors.append('  이미 패치된 것으로 보임 (_rows_from_registered_templates 존재)')
    if errors:
        print('[FAIL] 패턴 불일치 — 중단:')
        print('\n'.join(errors))
        sys.exit(1)

    for label, old, new in REPLS:
        content = content.replace(old, new, 1)
        print('  · %s' % label)

    ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    bak = PATH + '.bak_tplwiring_' + ts
    with open(bak, 'w', encoding='utf-8') as f:
        f.write(orig)
    with open(PATH, 'w', encoding='utf-8') as f:
        f.write(content)
    print('[OK] allocation_api.py 패치 완료  (백업: %s)' % os.path.basename(bak))


if __name__ == '__main__':
    main()
