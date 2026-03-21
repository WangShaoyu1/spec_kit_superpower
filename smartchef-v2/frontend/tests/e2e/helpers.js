/**
 * Shared helpers for Playwright E2E tests.
 */

/**
 * Login as admin and navigate to target path.
 * @param {import('@playwright/test').Page} page
 * @param {string} [targetPath='/'] - path to navigate after login
 */
export async function loginAsAdmin(page, targetPath = '/') {
  await page.goto('/login');
  await page.getByPlaceholder('用户名').fill('admin');
  await page.getByPlaceholder('密码').fill('admin123456');
  await page.getByRole('button', { name: /登\s*录/ }).click();
  await page.waitForURL('**/dashboard**', { timeout: 10000 }).catch(() => {});
  if (targetPath !== '/') {
    await page.goto(targetPath);
  }
  await page.waitForLoadState('networkidle', { timeout: 10000 }).catch(() => {});
}
