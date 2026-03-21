import { test, expect } from '@playwright/test';

test.describe('Layout & Accessibility', () => {
  test('login page has correct font loaded', async ({ page }) => {
    await page.goto('/login');
    const fontFamily = await page.evaluate(() => {
      return window.getComputedStyle(document.body).fontFamily;
    });
    expect(fontFamily).toContain('DM Sans');
  });

  test('login page has no console errors', async ({ page }) => {
    const errors = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') errors.push(msg.text());
    });
    await page.goto('/login');
    await page.waitForTimeout(2000);
    const realErrors = errors.filter((e) => !e.includes('favicon'));
    expect(realErrors).toHaveLength(0);
  });
});
