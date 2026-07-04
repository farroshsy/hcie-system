import { test, expect } from '@playwright/test'

test('homepage has title', async ({ page }) => {
  await page.goto('/')
  await expect(page).toHaveTitle(/HCIE/)
})

test('navigation works', async ({ page }) => {
  await page.goto('/')
  await page.click('text=Dashboard')
  await expect(page).toHaveURL(/\/dashboard/)
})

test('login page loads', async ({ page }) => {
  await page.goto('/login')
  await expect(page.locator('h1')).toContainText('Login')
})
