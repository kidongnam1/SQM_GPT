"""P4 — 단일 인스턴스 락 (Win32 CreateMutexW)"""
SRC = r"D:\program\SQM_inventory\SQM_v867_clean\main_webview.py"

with open(SRC, 'r', encoding='utf-8') as f:
    content = f.read()

# 이미 적용됐는지 확인
if '_MUTEX_NAME' in content:
    print("P4 이미 적용됨 — 건너뜀")
    raise SystemExit(0)

# 1) 최상단 import 블록에 ctypes 추가 (import json 다음)
# ctypes는 내부에서 로컬 import로 쓰이므로, 상단에 전역 import 추가
content = content.replace(
    'import json\n',
    'import json\nimport ctypes as _ctypes\n',
    1
)

# 2) mutex 함수 추가 (log = logging.getLogger(__name__) 바로 앞)
MUTEX_CODE = '''\n# ─────────────────────────────────────────────────────────────
# [P4] 단일 인스턴스 락 — exe 이중 실행 방지
# ─────────────────────────────────────────────────────────────
_MUTEX_NAME = "SQM_Inventory_SingleInstance_v867"

def _acquire_single_instance_lock():
    mutex = _ctypes.windll.kernel32.CreateMutexW(None, True, _MUTEX_NAME)
    last_err = _ctypes.windll.kernel32.GetLastError()
    if last_err == 183:  # ERROR_ALREADY_EXISTS
        _ctypes.windll.kernel32.CloseHandle(mutex)
        return False
    return True

'''
content = content.replace(
    'log = logging.getLogger(__name__)\n',
    MUTEX_CODE + 'log = logging.getLogger(__name__)\n',
    1
)

# 3) main() 첫 줄에 락 체크 삽입
OLD_MAIN = 'def main():\n'
NEW_MAIN = ('def main():\n'
            '    if not _acquire_single_instance_lock():\n'
            '        sys.exit(0)  # 두 번째 인스턴스 조용히 종료\n')
assert content.count(OLD_MAIN) == 1, f"def main(): 가 {content.count(OLD_MAIN)}개"
content = content.replace(OLD_MAIN, NEW_MAIN, 1)

with open(SRC, 'w', encoding='utf-8', newline='\n') as f:
    raw = content.encode('utf-8').replace(bytes([0x5c, 0x21]), bytes([0x21]))
    f.write(raw.decode('utf-8'))

print("P4 patch applied OK.")
