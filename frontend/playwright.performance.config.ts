import { defineConfig, devices } from 'playwright/test'
import { browserLaunchOptions } from './playwright.browser'

export default defineConfig({
  testDir: './tests/performance',
  workers: 1,
  timeout: 150_000,
  reporter: 'list',
  use: { baseURL: 'http://127.0.0.1:5173', trace: 'retain-on-failure', launchOptions: browserLaunchOptions },
  webServer: {
    command: 'npm run dev -- --host 127.0.0.1',
    url: 'http://127.0.0.1:5173',
    reuseExistingServer: !process.env.CI,
    env: { VITE_API_PROXY_TARGET: process.env.REAL_CITY_API_URL ?? 'http://127.0.0.1:18080' },
  },
  projects: [
    { name: 'desktop', use: { ...devices['Desktop Chrome'] } },
    { name: 'mobile', use: { ...devices['Pixel 7'] } },
  ],
})
