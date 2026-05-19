const fs = require('fs');
const path = require('path');
const { test, expect } = require('@playwright/test');

test('Pending 버튼 markup은 inline onclick에 JSON.stringify를 직접 주입하지 않는다', () => {
  const sourcePath = path.join(__dirname, '..', 'frontend', 'js', 'sqm-inventory.js');
  const source = fs.readFileSync(sourcePath, 'utf8');

  expect(source).not.toContain("onclick=\"window.showPendingActionMenu(event,' + JSON.stringify");
  expect(source).not.toContain("onclick=\"window.pendingEditInboundDate(this,' + lotJson");
  expect(source).toContain("onclick=\"window.showPendingActionMenu(event,\\'' + lotSafe + '\\')\"");
});
