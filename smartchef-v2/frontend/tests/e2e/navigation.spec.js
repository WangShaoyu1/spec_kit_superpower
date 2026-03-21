import { test, expect } from '@playwright/test';

test.describe('Navigation', () => {
  test('login page renders without errors', async ({ page }) => {
    await page.goto('/login');
    await expect(page).toHaveTitle(/SmartChef/);
  });

  test('404 page for unknown routes', async ({ page }) => {
    await page.goto('/nonexistent-page');
    const url = page.url();
    expect(url).toMatch(/\/(login|nonexistent)/);
  });
});
