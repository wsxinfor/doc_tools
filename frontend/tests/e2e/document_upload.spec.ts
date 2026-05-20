import { test, expect } from '@playwright/test'
import path from 'path'

const BASE = 'http://localhost:5173'

async function loginAsAdmin(page: import('@playwright/test').Page) {
  await page.goto(`${BASE}/login`)
  await page.getByTestId('username').fill('admin')
  await page.getByTestId('password').fill('admin123456')
  await page.getByTestId('login-btn').click()
  await expect(page).toHaveURL(/\/documents/, { timeout: 8000 })
}

test.describe('文档上传', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page)
  })

  test('上传 .docx 成功，列表出现新记录', async ({ page }) => {
    const filePath = path.resolve(__dirname, '../../backend/tests/fixtures/sample.docx')
    const fileInput = page.locator('input[type="file"]').first()
    await fileInput.setInputFiles(filePath)
    await expect(page.locator('.ant-message-success')).toBeVisible({ timeout: 10000 })
    await expect(page.locator('[data-testid="documents-table"] .ant-table-row').first()).toBeVisible()
  })

  test('非法格式被客户端拦截', async ({ page }) => {
    const fileInput = page.locator('input[type="file"]').first()
    await fileInput.setInputFiles({
      name: 'test.pdf',
      mimeType: 'application/pdf',
      buffer: Buffer.from('fake pdf content'),
    })
    await expect(page.locator('.ant-message-error')).toBeVisible({ timeout: 3000 })
    await expect(page.locator('.ant-message-error')).toContainText('仅支持')
  })
})
