const { test, expect } = require('@playwright/test');
test('2+2=4', async () => {
  expect(2 + 2).toBe(4);
});
