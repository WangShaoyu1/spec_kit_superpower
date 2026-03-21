import { test, expect } from '@playwright/test';

test.describe('Login Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
  });

  test('should display login form', async ({ page }) => {
    await expect(page.getByPlaceholder('用户名')).toBeVisible();
    await expect(page.getByPlaceholder('密码')).toBeVisible();
    // Antd inserts a space between two CJK characters in buttons
    await expect(page.getByRole('button', { name: /登\s*录/ })).toBeVisible();
  });

  test('should show error for empty form submission', async ({ page }) => {
    await page.getByRole('button', { name: /登\s*录/ }).click();
    const errors = page.locator('.ant-form-item-explain-error');
    await expect(errors.first()).toBeVisible();
    await expect(errors).toHaveCount(2);
  });

  test('should show SmartChef branding on login page', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'SmartChef' })).toBeVisible();
    await expect(page.getByText('智能对话管理平台', { exact: true })).toBeVisible();
  });
});
