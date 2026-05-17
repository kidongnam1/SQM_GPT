// =============================================================================
// SQM v8.6.8 - 라우터 회귀 테스트 (P2-3)
// 목적: 사이드바 탭 클릭 후 'Preparing:' 버그 자동 차단
// 실행: npx playwright test tests/sqm_regression.spec.js
// =============================================================================
const { test, expect } = require('@playwright/test');

const APP_URL = process.env.SQM_APP_URL || 'http://127.0.0.1:8765';

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

  test('Available 탭 — 핵심 컬럼과 그룹 전환 버튼 유지', async ({ page }) => {
    await page.locator('[data-page="available"], [data-tab="available"]').first().click();
    await expect(page.locator('#page-container')).toContainText('Con Return');
    await expect(page.locator('#page-container')).toContainText('Free');
    await expect(page.getByText('LOT별', { exact: true })).toBeVisible();
    await expect(page.getByText('컨테이너별', { exact: true })).toBeVisible();
    await expect(page.getByText('입고일별', { exact: true })).toBeVisible();
  });

  test('Picked 탭 — 그룹 모드 전환 중 치명 콘솔 오류 없음', async ({ page }) => {
    const consoleErrors = [];
    page.on('pageerror', (err) => consoleErrors.push(err.message));

    await page.locator('[data-page="picked"], [data-tab="picked"]').first().click();
    await page.getByText('고객사별', { exact: true }).click();
    await page.waitForTimeout(300);
    await page.getByText('입고일별', { exact: true }).click();
    await page.waitForTimeout(300);

    expect(consoleErrors, `Picked 그룹 전환 오류: ${consoleErrors.join(' | ')}`).toHaveLength(0);
  });





  test('실행 중 프런트 자산 버전이 작업본과 일치', async ({ page }) => {
    const scripts = await page.locator('script[src]').evaluateAll((els) => els.map((el) => el.getAttribute('src')));
    expect(scripts).toContain('js/sqm-core.js?v=20260517p22');
    expect(scripts).toContain('js/sqm-inline.js?v=20260517p29');
    expect(scripts).toContain('js/sqm-upload-modals.js?v=20260517a');
    expect(scripts).toContain('js/sqm-aux-modals.js?v=20260517a');
    expect(scripts).toContain('js/sqm-tools-modals.js?v=20260517a');
    expect(scripts).toContain('js/sqm-product-modals.js?v=20260517a');
  });

  test('분리 모듈 — 핵심 전역 함수가 로드됨', async ({ page }) => {
    const exported = await page.evaluate(() => ({
      upload: typeof window.showInboundManualUploadModal,
      uploadPdf: typeof window.showPickingListPdfModal,
      product: typeof window.showProductSummaryModal,
      tools: typeof window.showDocConvertModal,
      aux: typeof window.showAiToolsHubModal,
      info: typeof window.renderInfoModal,
    }));

    expect(exported).toEqual({
      upload: 'function',
      uploadPdf: 'function',
      product: 'function',
      tools: 'function',
      aux: 'function',
      info: 'function',
    });
  });

  test('메뉴 액션 — 분리된 모듈 모달이 실제로 열림', async ({ page }) => {
    const cases = [
      { action: 'onInboundManual', text: '수동 입고' },
      { action: 'onProductLotLookup', text: '품목별 LOT 조회' },
      { action: 'onDocConvert', text: '문서 변환' },
      { action: 'onAiTools', text: 'AI / 선사 도구' },
    ];

    for (const item of cases) {
      await page.evaluate((action) => window.SQM.dispatchAction(action), item.action);
      await expect(page.locator('#sqm-modal')).toBeVisible();
      await expect(page.locator('#sqm-modal-content')).toContainText(item.text);
      await page.evaluate(() => { document.getElementById('sqm-modal').style.display = 'none'; });
    }
  });

  test('Move 탭 — LOT 이동 입력으로 표시', async ({ page }) => {
    await page.locator('[data-page="move"], [data-tab="move"]').first().click();
    await expect(page.locator('#move-lot-no')).toBeVisible();
    await expect(page.locator('#move-lot-no')).toHaveAttribute('placeholder', 'LOT No');
  });
});
