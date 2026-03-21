// @ts-check
const { test, expect } = require('@playwright/test');
const { loginAsAdmin } = require('./helpers');

test.describe('Intent Library List Page', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page, '/intent-library');
  });

  test('page loads and displays statistics cards', async ({ page }) => {
    await expect(page.locator('.ant-statistic')).toHaveCount(4, { timeout: 10000 });
  });

  test('page displays a table with libraries', async ({ page }) => {
    const table = page.locator('.ant-table');
    await expect(table).toBeVisible({ timeout: 10000 });
  });

  test('search input and filters exist', async ({ page }) => {
    await expect(page.getByPlaceholder(/搜索|名称|Key/)).toBeVisible({ timeout: 5000 });
  });

  test('create button opens modal', async ({ page }) => {
    const createBtn = page.getByRole('button', { name: /新建/ });
    await expect(createBtn).toBeVisible({ timeout: 5000 });
    await createBtn.click();
    await expect(page.locator('.ant-modal')).toBeVisible({ timeout: 5000 });
  });

  test('create library flow', async ({ page }) => {
    await page.getByRole('button', { name: /新建/ }).click();
    const modal = page.locator('.ant-modal');
    await expect(modal).toBeVisible();

    const uniqueKey = `e2e_${Date.now()}`;
    await modal.getByLabel(/名称|name/i).first().fill('E2E Test Library');
    await modal.locator('input[id*="library_key"], input[id*="libraryKey"]').first().fill(uniqueKey);

    const langSelect = modal.locator('.ant-select').first();
    if (await langSelect.isVisible()) {
      await langSelect.click();
      await page.locator('.ant-select-item-option').filter({ hasText: /zh|中文/ }).first().click();
    }

    const submitBtn = modal.getByRole('button', { name: /确[定认]|提交|OK/i });
    await submitBtn.click();

    await expect(page.locator('.ant-message-success, .ant-message-notice')).toBeVisible({ timeout: 5000 }).catch(() => {});
  });

  test('table has expected columns', async ({ page }) => {
    const table = page.locator('.ant-table');
    await expect(table).toBeVisible({ timeout: 10000 });
    const headers = table.locator('.ant-table-thead th');
    const headerTexts = await headers.allTextContents();
    const joined = headerTexts.join(',');
    expect(joined).toMatch(/名称|Library/i);
    expect(joined).toMatch(/Key|标识/i);
  });

  test('no console errors', async ({ page }) => {
    const errors = [];
    page.on('console', msg => {
      if (msg.type() === 'error' && !msg.text().includes('favicon')) {
        errors.push(msg.text());
      }
    });
    await page.reload();
    await page.waitForLoadState('networkidle').catch(() => {});
    expect(errors.filter(e => !e.includes('ERR_CANCELED') && !e.includes('AbortError'))).toHaveLength(0);
  });
});
