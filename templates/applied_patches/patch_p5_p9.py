"""P5 + P9 — JS heartbeat + sqm-core.js IIFE 재진입 가드"""
SRC = r"D:\program\SQM_inventory\SQM_v867_clean\frontend\js\sqm-core.js"

with open(SRC, 'r', encoding='utf-8') as f:
    content = f.read()

if '__SQM_HEARTBEAT_INSTALLED__' in content:
    print("P5 이미 적용됨 — 건너뜀")
    raise SystemExit(0)

HEARTBEAT_CODE = """
  /* ===================================================
     P5: Backend Heartbeat (silent fail 감지)
     =================================================== */
  (function() {
    if (window.__SQM_HEARTBEAT_INSTALLED__) return;
    window.__SQM_HEARTBEAT_INSTALLED__ = true;

    var HEALTH_URL = '/api/health';
    var INTERVAL_MS = 15000;
    var FAIL_COUNT = 0;
    var MAX_FAIL = 2;
    var _banner = null;

    function showOfflineBanner() {
      if (_banner) return;
      _banner = document.createElement('div');
      _banner.id = 'sqm-offline-banner';
      _banner.style.cssText = [
        'position:fixed', 'top:0', 'left:0', 'right:0',
        'background:#c0392b', 'color:#fff',
        'text-align:center', 'padding:8px 16px',
        'font-size:14px', 'z-index:99999',
        'font-family:Malgun Gothic,Segoe UI,sans-serif',
        'box-shadow:0 2px 8px rgba(0,0,0,0.4)'
      ].join(';');
      _banner.textContent = '\\u26a0\\ufe0f \\uc11c\\ubc84 \\uc5f0\\uacb0\\uc774 \\ub04a\\uacbc\\uc2b5\\ub2c8\\ub2e4. \\ud504\\ub85c\\uadf8\\ub7a8\\uc744 \\uc7ac\\uc2dc\\uc791\\ud574 \\uc8fc\\uc138\\uc694.';
      document.body.appendChild(_banner);
    }

    function hideOfflineBanner() {
      if (_banner) { _banner.remove(); _banner = null; }
    }

    function checkHealth() {
      fetch(HEALTH_URL, { method: 'GET', cache: 'no-store' })
        .then(function(r) {
          if (r.ok) { FAIL_COUNT = 0; hideOfflineBanner(); }
          else { FAIL_COUNT++; if (FAIL_COUNT >= MAX_FAIL) showOfflineBanner(); }
        })
        .catch(function() {
          FAIL_COUNT++;
          if (FAIL_COUNT >= MAX_FAIL) showOfflineBanner();
        });
    }

    setTimeout(function() {
      checkHealth();
      setInterval(checkHealth, INTERVAL_MS);
    }, 5000);
  })();

"""

# 파일 마지막 })(); 바로 앞에 삽입
OLD_TAIL = '\n})();'
count = content.count(OLD_TAIL)
assert count == 1, "})(); count=" + str(count)
content = content.replace(OLD_TAIL, HEARTBEAT_CODE + '\n})();', 1)

with open(SRC, 'w', encoding='utf-8', newline='\n') as f:
    raw = content.encode('utf-8').replace(bytes([0x5c, 0x21]), bytes([0x21]))
    f.write(raw.decode('utf-8'))

print("P5+P9 patch applied OK.")
