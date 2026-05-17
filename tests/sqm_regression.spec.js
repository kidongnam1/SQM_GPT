// =============================================================================
// SQM v8.6.8 - 라우터 회귀 테스트 (P2-3)
// 목적: 사이드바 탭 클릭 후 'Preparing:' 버그 자동 차단
// 실행: npx playwright test tests/sqm_regression.spec.js
// =============================================================================
const { test, expect } = require('@playwright/test');

const APP_URL = 'http://localhost:8000';

const TABS = [
  { name: 'pending',    label: '입고대기' },
  { name: 'available',  label: '재고'    },
  { name: 'allocation', label: '배정'    },
  { name: 'picked',     label: '피킹'    },
  { name: 'return',     label: '반품'    },
  { name: 'move',       label: '이동'    },
];

test.describe('SQM 라우터 회귀 — Preparing: 버그 차단', () => {

  test.beforeEach(async ({ page }) => {
    await page.goto(APP_URL, { waitUntil: 'networkidle' });
  });

  for (const tab of TABS) {
    test(`탭 [${tab.label}] — "Preparing:" 없음`, async ({ page }) => {
      // 사이드바 탭 클릭 (data-page 또는 data-tab 속성으로 찾음)
      const selector = `[data-page="${tab.name}"], [data-tab="${tab.name}"], nav a[href="#${tab.name}"]`;
      const btn = page.locator(selector).first();
      await btn.click();

      // 페이지 로드 대기 (최대 5초)
      await page.waitForTimeout(1000);

      // page-container 내 "Preparing:" 문자열 없어야 함
      const container = page.locator('#page-container');
      const text = await container.innerText().catch(() => '');
      expect(text, `[${tab.label}] 탭에 "Preparing:" 발견 — 라우터 누락 의심`).not.toContain('Preparing:');
      expect(text, `[${tab.label}] 탭이 비어 있음`).not.toBe('');
    });
  }

  test('전체 탭 순회 — 각 탭 HTTP 500 없음', async ({ page }) => {
    const errors = [];
    page.on('response', (res) => {
      if (res.status() >= 500) {
        errors.push(`${res.status()} ${res.url()}`);
      }
    });

    for (const tab of TABS) {
      const selector = `[data-page="${tab.name}"], [data-tab="${tab.name}"], nav a[href="#${tab.name}"]`;
      const btn = page.locator(selector).first();
      if (await btn.count() > 0) {
        await btn.click();
        await page.waitForTimeout(800);
      }
    }

    expect(errors, `HTTP 500 발생: ${errors.join(', ')}`).toHaveLength(0);
  });
});
