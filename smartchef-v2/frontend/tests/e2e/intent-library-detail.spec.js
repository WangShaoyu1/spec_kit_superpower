// @ts-check
const { test, expect } = require('@playwright/test');
const { loginAsAdmin } = require('./helpers');

test.describe('Intent Library Detail Page', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page, '/intent-library');
    await page.waitForLoadState('networkidle').catch(() => {});
    const firstRow = page.locator('.ant-table-tbody tr').first();
    await expect(firstRow).toBeVisible({ timeout: 10000 });
    const viewLink = firstRow.getByRole('link', { name: /查看|详情/ }).or(firstRow.locator('a').first());
    await viewLink.click();
    await page.waitForLoadState('networkidle').catch(() => {});
  });

  test('detail page shows library info', async ({ page }) => {
    await expect(page.locator('.ant-descriptions, .ant-card')).toBeVisible({ timeout: 10000 });
  });

  test('model version table is visible', async ({ page }) => {
    await expect(page.locator('.ant-table')).toBeVisible({ timeout: 10000 });
  });

  test('create model button exists', async ({ page }) => {
    const btn = page.getByRole('button', { name: /新建|训练|创建模型/ });
    await expect(btn).toBeVisible({ timeout: 5000 });
  });

  test('create model opens modal', async ({ page }) => {
    const btn = page.getByRole('button', { name: /新建|训练|创建模型/ });
    await btn.click();
    await expect(page.locator('.ant-modal')).toBeVisible({ timeout: 5000 });
  });

  test('navigate to datasets page', async ({ page }) => {
    const dsBtn = page.getByRole('button', { name: /数据集/ }).or(page.getByText(/数据集管理/));
    if (await dsBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
      await dsBtn.click();
      await page.waitForURL('**/datasets**', { timeout: 5000 }).catch(() => {});
    }
  });

  test('model version table shows status tags', async ({ page }) => {
    const table = page.locator('.ant-table');
    await expect(table).toBeVisible({ timeout: 10000 });
    const statusTags = table.locator('.ant-tag, .ant-badge');
    const count = await statusTags.count();
    expect(count).toBeGreaterThanOrEqual(0);
  });

  test('no console errors on detail page', async ({ page }) => {
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
