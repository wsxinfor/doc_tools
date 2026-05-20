import { test, expect } from '@playwright/test'

const BASE = 'http://localhost:5173'

async function loginAsAdmin(page: import('@playwright/test').Page) {
  await page.goto(`${BASE}/login`)
  await page.getByTestId('username').fill('admin')
  await page.getByTestId('password').fill('admin123456')
  await page.getByTestId('login-btn').click()
  await expect(page).toHaveURL(/\/documents/, { timeout: 8000 })
}

test.describe('模板管理', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page)
  })

  test('创建模板，列表出现', async ({ page }) => {
    await page.goto(`${BASE}/templates`)
    await page.getByTestId('new-template-btn').click()
    await expect(page).toHaveURL(/\/templates\/new/)
    const name = `E2E模板_${Date.now()}`
    await page.getByTestId('template-name-input').fill(name)
    await page.getByTestId('save-template-btn').click()
    await expect(page).toHaveURL(/\/templates$/, { timeout: 5000 })
    await expect(page.getByText(name)).toBeVisible()
  })

  test('模板名称为空时显示校验错误', async ({ page }) => {
    await page.goto(`${BASE}/templates/new`)
    await page.getByTestId('save-template-btn').click()
    await expect(page.locator('.ant-form-item-explain-error').first()).toBeVisible()
  })
})
