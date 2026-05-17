# -*- coding: utf-8 -*-
"""
patch_renderinfomodal_fmt.py
============================
Purpose: sqm-inline.js renderInfoModal에서 객체/배열을 [object Object]로 표시하는 버그 수정
         정합성 검증, 일일 보고서, 월간 보고서 모달 등 모든 KV 테이블 표시 개선
Why    : String({...}) → "[object Object]", String([{...}]) → "[object Object],[object Object],..."
         원인: line 6430-6432의 escapeHtml(String(kv[1])) 처리
Rule   : CLAUDE.md Rule 5 (강화) — 7516줄 IIFE 파일은 Python 스크립트만 사용
Author : Ruby (Senior Software Architect) — 2026-05-15
"""
import sys
import shutil
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
TARGET = ROOT / "frontend" / "js" / "sqm-inline.js"

# fallback 분기 (Array/Object의 일반 KV 테이블 렌더링) — 객체 값을 JSON 처리
ANCHOR_KV = """      } else {
        html='<table class="data-table"><tbody>'+Object.entries(d).map(function(kv){
          return '<tr><td style="font-weight:600;width:40%">'+escapeHtml(kv[0])+'</td><td>'+escapeHtml(String(kv[1]))+'</td></tr>';
        }).join('')+'</tbody></table>';
      }"""

PATCH_KV = """      } else {
        // v868 fix (2026-05-15): 객체/배열을 [object Object]로 표시하던 버그 수정
        // issues(배열), stats(객체) 등 중첩 데이터를 보기 좋게 포맷
        var _fmtVal = function(v) {
          if (v === null || v === undefined) return '-';
          if (Array.isArray(v)) {
            if (v.length === 0) return '(빈 배열)';
            // 배열 안이 객체면 nested table, 원시값이면 콤마 join
            if (typeof v[0] === 'object' && v[0] !== null) {
              var keys = Object.keys(v[0]);
              var head = '<thead><tr>'+keys.map(function(k){return '<th style="font-size:.8rem;padding:4px 8px">'+escapeHtml(k)+'</th>';}).join('')+'</tr></thead>';
              var body = '<tbody>'+v.map(function(row){
                return '<tr>'+keys.map(function(k){
                  var cell = row[k];
                  return '<td style="font-size:.8rem;padding:4px 8px">'+escapeHtml(cell === null || cell === undefined ? '-' : (typeof cell === 'object' ? JSON.stringify(cell) : String(cell)))+'</td>';
                }).join('')+'</tr>';
              }).join('')+'</tbody>';
              return '<table class="data-table" style="margin:0;font-size:.85rem">'+head+body+'</table>';
            }
            return v.map(function(x){return String(x);}).join(', ');
          }
          if (typeof v === 'object') {
            return '<table class="data-table" style="margin:0;font-size:.85rem"><tbody>'+Object.entries(v).map(function(kv2){
              return '<tr><td style="font-weight:600;padding:3px 8px">'+escapeHtml(kv2[0])+'</td><td style="padding:3px 8px">'+escapeHtml(String(kv2[1]))+'</td></tr>';
            }).join('')+'</tbody></table>';
          }
          return escapeHtml(String(v));
        };
        html='<table class="data-table"><tbody>'+Object.entries(d).map(function(kv){
          return '<tr><td style="font-weight:600;width:40%;vertical-align:top">'+escapeHtml(kv[0])+'</td><td>'+_fmtVal(kv[1])+'</td></tr>';
        }).join('')+'</tbody></table>';
      }"""


def main() -> int:
    if not TARGET.exists():
        print(f"[ERROR] target not found: {TARGET}", file=sys.stderr)
        return 1

    raw = TARGET.read_bytes()
    text = raw.decode("utf-8")
    line_count_before = text.count("\n")
    print(f"[INFO] file: {TARGET.name}")
    print(f"[INFO] lines before: {line_count_before}")

    # 멱등성
    if "_fmtVal = function(v)" in text:
        print("[SKIP] already patched.")
        return 0

    count = text.count(ANCHOR_KV)
    if count == 0:
        print("[ERROR] anchor not found.", file=sys.stderr)
        return 2
    if count > 1:
        print(f"[ERROR] anchor matched {count} times.", file=sys.stderr)
        return 3

    # 백업
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = TARGET.with_suffix(f".js.bak_fmt_{ts}")
    shutil.copy2(TARGET, backup)
    print(f"[INFO] backup: {backup.name}")

    # 패치
    new_text = text.replace(ANCHOR_KV, PATCH_KV, 1)

    # IIFE 닫힘 보존 검증 (Rule 5 강화 — 사고 재발 방지)
    if not new_text.rstrip().endswith("})();"):
        print("[ERROR] IIFE closing `})();` lost after patch. abort.", file=sys.stderr)
        return 4

    TARGET.write_bytes(new_text.encode("utf-8"))
    line_count_after = new_text.count("\n")
    delta = line_count_after - line_count_before
    print(f"[INFO] lines after : {line_count_after} (delta=+{delta})")
    print("[OK] patch applied.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
