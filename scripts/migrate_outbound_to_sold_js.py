"""
JS 파일 OUTBOUND → SOLD 상태 통합 스크립트
실행: python scripts/migrate_outbound_to_sold_js.py

변환 규칙:
1. 상태 비교: === 'OUTBOUND' → === 'SOLD', !== 'OUTBOUND' → !== 'SOLD'
2. 상태 할당: = 'OUTBOUND' → = 'SOLD'
3. 배열 요소: ['SOLD','OUTBOUND'] → ['SOLD'] (중복 제거)
4. includes(): .includes('OUTBOUND') → .includes('SOLD')
5. switch/case: case 'OUTBOUND': → case 'SOLD':
6. 이벤트: 'OUTBOUND_SOLD' → 'SOLD'
7. 색상 맵: 'OUTBOUND':'...' → 'SOLD':'...'
8. 필터: ['OUTBOUND'] → ['SOLD']

변환하지 않음:
- 컬럼명: OUTBOUND DATE (유지)
- 주석/텍스트: "PICKED → OUTBOUND" (유지)
- URL/경로: (유지)
"""
import re
import os

TARGET_FILES = [
    "frontend/js/sqm-inline.js",
    "frontend/js/sqm-allocation.js",
    "frontend/js/sqm-tonbag.js",
    "frontend/js/sqm-logistics.js",
    "frontend/js/sqm-inventory.js",
    "frontend/js/sqm-picked.js",
]

def replace_outbound_js(text: str) -> str:
    """OUTBOUND 상태값을 SOLD로 변환"""

    # 1. 동등 비교 (===, !==)
    text = re.sub(r"=== 'OUTBOUND'", "=== 'SOLD'", text)
    text = re.sub(r'=== "OUTBOUND"', '=== "SOLD"', text)
    text = re.sub(r"!== 'OUTBOUND'", "!== 'SOLD'", text)
    text = re.sub(r'!== "OUTBOUND"', '!== "SOLD"', text)

    # 2. 상태 할당 (= 'OUTBOUND')
    text = re.sub(r"= 'OUTBOUND'(?=[,;\s\)])", "= 'SOLD'", text)
    text = re.sub(r'= "OUTBOUND"(?=[,;\s\)])', '= "SOLD"', text)

    # 3. 배열 내 OUTBOUND 제거 (['SOLD','OUTBOUND'] → ['SOLD'])
    text = re.sub(r"'SOLD',\s*'OUTBOUND'", "'SOLD'", text)
    text = re.sub(r"'OUTBOUND',\s*'SOLD'", "'SOLD'", text)
    text = re.sub(r'"SOLD",\s*"OUTBOUND"', '"SOLD"', text)
    text = re.sub(r'"OUTBOUND",\s*"SOLD"', '"SOLD"', text)

    # OUTBOUND만 있을 때 제거
    text = re.sub(r",\s*'OUTBOUND'(?=\s*[\],)])", "", text)
    text = re.sub(r',\s*"OUTBOUND"(?=\s*[\],)])', '', text)
    text = re.sub(r"\['OUTBOUND'\]", "['SOLD']", text)
    text = re.sub(r'\["OUTBOUND"\]', '["SOLD"]', text)

    # 4. includes() 메서드
    text = re.sub(r"\.includes\('OUTBOUND'\)", ".includes('SOLD')", text)
    text = re.sub(r'\.includes\("OUTBOUND"\)', '.includes("SOLD")', text)

    # 5. switch/case
    text = re.sub(r"case 'OUTBOUND':", "case 'SOLD':", text)
    text = re.sub(r'case "OUTBOUND":', 'case "SOLD":', text)

    # 6. 색상 맵 정의 ('OUTBOUND':'#...')
    text = re.sub(r"'OUTBOUND':", "'SOLD':", text)
    text = re.sub(r'"OUTBOUND":', '"SOLD":', text)

    # 7. 필터 배열 (단순 OUTBOUND만 있을 때) - FILTERS 배열 등
    # ['ALL','INBOUND','ALLOCATED','PICKED','OUTBOUND',...] → 'SOLD'로 변경
    text = re.sub(r"'OUTBOUND'(?=,)", "'SOLD'", text)

    # 8. 이벤트명 'OUTBOUND_SOLD' → 'SOLD'
    text = text.replace("'OUTBOUND_SOLD'", "'SOLD'")
    text = text.replace('"OUTBOUND_SOLD"', '"SOLD"')

    return text

def process_file(path: str) -> tuple[bool, int]:
    """파일 처리 및 변경 라인 수 반환"""
    if not os.path.exists(path):
        print(f"  SKIP: {path} (file not found)")
        return False, 0

    try:
        with open(path, encoding='utf-8') as f:
            original = f.read()
    except Exception as e:
        print(f"  ERROR reading {path}: {e}")
        return False, 0

    updated = replace_outbound_js(original)

    if original == updated:
        print(f"  NO CHANGE: {path}")
        return False, 0

    try:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(updated)
    except Exception as e:
        print(f"  ERROR writing {path}: {e}")
        return False, 0

    # 변경된 라인 수 계산
    orig_lines = original.splitlines()
    upd_lines = updated.splitlines()
    changed = sum(1 for a, b in zip(orig_lines, upd_lines) if a != b)
    changed += abs(len(orig_lines) - len(upd_lines))

    print(f"  ✓ UPDATED ({changed} lines): {path}")
    return True, changed

if __name__ == "__main__":
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(root)

    print("=" * 60)
    print("JS 파일 OUTBOUND → SOLD 마이그레이션")
    print("=" * 60)

    total_files = 0
    total_lines = 0

    for path in TARGET_FILES:
        success, lines = process_file(path)
        if success:
            total_files += 1
            total_lines += lines

    print("=" * 60)
    print(f"완료: {total_files}개 파일 수정, {total_lines} 라인 변경됨")
    print("=" * 60)
