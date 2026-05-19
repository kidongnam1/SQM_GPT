# -*- coding: utf-8 -*-
"""
patch_alloc_template_colmap.py
------------------------------
후속 작업 2건:

[A] template-list 내장 목록 3종 → 6종 보정
    Song/Jakarta/Woo 만 노출되던 것에 Easpring/화주원본/기존 추가
    (정본 AllocationParser 가 실제 지원하는 6종과 일치시킴)

[B] template-upload 에 컬럼 매핑 편집 기능 추가
    - 백엔드: column_map 파라미터 수신 → .json 템플릿에 'column_map' 저장
    - _rows_from_registered_templates: column_map 우선 적용 (비표준 컬럼명 지원)
    - 프론트: [양식 가져오기] 모달 분석 결과에 컬럼 매핑 편집기 UI 추가

대상 (Rule 5):
  - backend/api/allocation_api.py  (>1000줄 → 패치 스크립트)
  - frontend/js/sqm-allocation.js  (IIFE 패턴 → 패치 스크립트)
"""
import os
import sys
import datetime

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

ROOT = os.path.join(os.path.dirname(__file__), '..')
API_PATH = os.path.join(ROOT, 'backend', 'api', 'allocation_api.py')
JS_PATH = os.path.join(ROOT, 'frontend', 'js', 'sqm-allocation.js')

# ════════════════════════════════════════════════════════════════════
# [A] template-list 내장 목록 3 → 6
# ════════════════════════════════════════════════════════════════════
A_OLD = '''            "builtin": True,
            "description": "정본 AllocationParser 내장 지원",
        },
    ]'''

A_NEW = '''            "builtin": True,
            "description": "정본 AllocationParser 내장 지원",
        },
        {
            "id": "builtin_easpring",
            "tab_label": "📄 Easpring 계열",
            "columns": ["LOT", "PRODUCT", "QTY(MT)", "SC RCVD"],
            "sheet": "자동선택",
            "header_row": 0,
            "builtin": True,
            "description": "정본 AllocationParser 내장 지원 (14행 헤더 / SC RCVD)",
        },
        {
            "id": "builtin_shipper",
            "tab_label": "📄 화주원본 계열",
            "columns": ["LOT", "QTY(MT)", "SOLD TO"],
            "sheet": "자동선택",
            "header_row": 0,
            "builtin": True,
            "description": "정본 AllocationParser 내장 지원 (1행 합계 / 2행 헤더)",
        },
        {
            "id": "builtin_legacy",
            "tab_label": "📄 기존 계열",
            "columns": ["LOT", "PRODUCT", "QTY(MT)", "SOLD TO"],
            "sheet": "자동선택",
            "header_row": 0,
            "builtin": True,
            "description": "정본 AllocationParser 내장 지원 (1행 타이틀 / 3행 헤더)",
        },
    ]'''

# ════════════════════════════════════════════════════════════════════
# [B-1] template_upload 시그니처에 column_map 파라미터 추가
# ════════════════════════════════════════════════════════════════════
B1_OLD = '''async def template_upload(
    file: UploadFile = File(...),
    label: str = "",
    action: str = "check"
):'''

B1_NEW = '''async def template_upload(
    file: UploadFile = File(...),
    label: str = "",
    action: str = "check",
    column_map: str = ""
):'''

# ════════════════════════════════════════════════════════════════════
# [B-2] column_map 파싱·검증 → mapping 에 저장
# ════════════════════════════════════════════════════════════════════
B2_OLD = '''        }

        # 저장
        base = _alloc_template_dir()'''

B2_NEW = '''        }

        # 사용자 지정 컬럼 매핑 (비표준 컬럼명 → 표준키) 파싱·검증
        user_col_map = {}
        if column_map:
            try:
                _raw_map = _json.loads(column_map)
                _valid_keys = {'lot_no', 'qty_mt', 'sold_to', 'sale_ref', 'outbound_date'}
                for _k, _v in (_raw_map or {}).items():
                    if _k in _valid_keys and _v and str(_v).strip() in columns:
                        user_col_map[_k] = str(_v).strip()
            except Exception as _exc:
                logger.warning("[template-upload] column_map 파싱 실패: %s", _exc)
        if user_col_map:
            mapping['column_map'] = user_col_map

        # 저장
        base = _alloc_template_dir()'''

# ════════════════════════════════════════════════════════════════════
# [B-3] _rows_from_registered_templates 에서 column_map 우선 적용
# ════════════════════════════════════════════════════════════════════
B3_OLD = '''        col_map = _match_alloc_columns(df.columns)
        if 'lot_no' in col_map and ('sold_to' in col_map or 'qty_mt' in col_map):'''

B3_NEW = '''        col_map = _match_alloc_columns(df.columns)
        # 템플릿에 사용자 지정 매핑(column_map)이 있으면 우선 적용 — 비표준 컬럼명 지원
        _tpl_map = tpl.get('column_map') or {}
        if _tpl_map:
            _df_cols = {str(c).strip().lower(): c for c in df.columns}
            for _mk, _mname in _tpl_map.items():
                _actual = _df_cols.get(str(_mname).strip().lower())
                if _actual is not None:
                    col_map[_mk] = _actual
        if 'lot_no' in col_map and ('sold_to' in col_map or 'qty_mt' in col_map):'''

# ════════════════════════════════════════════════════════════════════
# [B-4] 프론트 — 컬럼 매핑 편집기 helper 삽입
# ════════════════════════════════════════════════════════════════════
F1_OLD = "    function showAnalysisResult(res) {"

F1_HELPER = """    // ── 컬럼 매핑 편집기 (비표준 컬럼명 → 표준키) ───────────
    var _MAP_FIELDS = [
      ['lot_no',        'LOT 번호',  /lot/i,                                       true],
      ['qty_mt',        '수량 (MT)', /qty|quantity|balance|weight|수량/i,           true],
      ['sold_to',       '고객사',    /sold|customer|buyer|consignee|고객|거래처/i,  false],
      ['sale_ref',      'Sale Ref',  /sale.?ref|sc.?no|contract|참조/i,             false],
      ['outbound_date', '출고일',    /outbound|ship|delivery|출고|선적/i,           false]
    ];
    function _buildMapEditor(columns) {
      var rows = _MAP_FIELDS.map(function(f){
        var key = f[0], lbl = f[1], rx = f[2], req = f[3];
        var guess = '';
        columns.some(function(c){ if (rx.test(String(c))) { guess = c; return true; } return false; });
        var opts = '<option value="">(자동 감지)</option>' + columns.map(function(c){
          var sel = (c === guess) ? ' selected' : '';
          return '<option value="' + escapeHtml(String(c)) + '"' + sel + '>' + escapeHtml(String(c)) + '</option>';
        }).join('');
        return '<div style="display:flex;align-items:center;gap:8px;margin-bottom:5px">' +
          '<label style="width:104px;font-size:.82rem;color:var(--text-muted)">' + lbl +
            (req ? ' <span style="color:var(--danger)">*</span>' : '') + '</label>' +
          '<select id="atpl-map-' + key + '" style="flex:1;padding:4px 6px;border:1px solid var(--border);' +
            'border-radius:5px;background:var(--bg);color:var(--text-primary);font-size:.83rem">' + opts + '</select>' +
        '</div>';
      }).join('');
      return '<div style="background:var(--bg-hover);border:1px solid var(--border);border-radius:6px;padding:10px 12px;margin-bottom:10px">' +
        '<div style="font-size:.83rem;font-weight:600;color:var(--text-muted);margin-bottom:8px">🔗 컬럼 매핑 — 표준 항목에 엑셀 컬럼 연결</div>' +
        rows +
        '<div style="font-size:.76rem;color:var(--text-muted);margin-top:4px">(자동 감지)로 두면 import 시 별칭 규칙으로 매칭합니다. 비표준 컬럼명은 직접 지정하세요.</div>' +
      '</div>';
    }
"""

F1_NEW = F1_HELPER + "\n" + F1_OLD

# [B-5] 분석 결과에 매핑 편집기 출력
F2_OLD = "      if (!res.duplicate) {"
F2_NEW = "      preview += _buildMapEditor(res.columns || []);\n\n      if (!res.duplicate) {"

# [B-6] 저장 시 column_map 수집·전송
F3_OLD = "      fd.append('action', action);"
F3_NEW = """      fd.append('action', action);
      var _cmap = {};
      ['lot_no','qty_mt','sold_to','sale_ref','outbound_date'].forEach(function(k){
        var _el = document.getElementById('atpl-map-' + k);
        if (_el && _el.value) _cmap[k] = _el.value;
      });
      if (Object.keys(_cmap).length) fd.append('column_map', JSON.stringify(_cmap));"""

API_REPLS = [
    ('[A] 내장 목록 3 → 6종', A_OLD, A_NEW),
    ('[B-1] column_map 파라미터', B1_OLD, B1_NEW),
    ('[B-2] column_map 파싱·저장', B2_OLD, B2_NEW),
    ('[B-3] column_map 우선 적용', B3_OLD, B3_NEW),
]
JS_REPLS = [
    ('[B-4] 매핑 편집기 helper', F1_OLD, F1_NEW),
    ('[B-5] 분석결과에 편집기 출력', F2_OLD, F2_NEW),
    ('[B-6] 저장 시 column_map 전송', F3_OLD, F3_NEW),
]


def apply(path, repls, guard_token):
    name = os.path.basename(path)
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    orig = content

    if guard_token in content:
        print('[SKIP] %s — 이미 패치됨 (%s 존재)' % (name, guard_token))
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
    bak = path + '.bak_colmap_' + ts
    with open(bak, 'w', encoding='utf-8') as f:
        f.write(orig)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print('[OK] %s 패치 완료  (백업: %s)' % (name, os.path.basename(bak)))
    return True


def main():
    print('=== Allocation 템플릿: 내장목록 보정 + 컬럼매핑 편집 ===')
    ok = True
    print('-- backend/api/allocation_api.py --')
    ok &= apply(API_PATH, API_REPLS, 'builtin_easpring')
    print('-- frontend/js/sqm-allocation.js --')
    ok &= apply(JS_PATH, JS_REPLS, '_buildMapEditor')
    print('=== %s ===' % ('완료' if ok else '실패 — 위 로그 확인'))
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
