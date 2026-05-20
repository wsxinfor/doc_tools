import { test, expect } from '@playwright/test'

const BASE = 'http://localhost:5173'

test.describe('登录流程', () => {
  test.beforeEach(async ({ page }) => {
    // Clear storage to start fresh
    await page.goto(`${BASE}/login`)
    await page.evaluate(() => localStorage.clear())
  })

  test('正确账号密码登录成功，跳转文档列表', async ({ page }) => {
    await page.goto(`${BASE}/login`)
    await page.getByTestId('username').fill('admin')
    await page.getByTestId('password').fill('admin123456')
    await page.getByTestId('login-btn').click()
    await expect(page).toHaveURL(/\/documents/, { timeout: 8000 })
  })

  test('错误密码显示错误提示', async ({ page }) => {
    await page.goto(`${BASE}/login`)
    await page.getByTestId('username').fill('admin')
    await page.getByTestId('password').fill('wrongpassword')
    await page.getByTestId('login-btn').click()
    await expect(page.locator('.ant-message-error')).toBeVisible({ timeout: 5000 })
  })

  test('未登录访问 /documents 跳转 /login', async ({ page }) => {
    await page.goto(`${BASE}/documents`)
    await expect(page).toHaveURL(/\/login/)
  })

  test('必填项为空提交显示校验错误', async ({ page }) => {
    await page.goto(`${BASE}/login`)
    await page.getByTestId('login-btn').click()
    await expect(page.locator('.ant-form-item-explain-error').first()).toBeVisible()
  })
})
