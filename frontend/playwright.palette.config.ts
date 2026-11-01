import { defineConfig } from 'playwright/test'
import { browserLaunchOptions } from './playwright.browser'

export default defineConfig({
  testDir: './tests/e2e', testMatch: 'palette.spec.ts', workers: 1, timeout: 90_000,
  outputDir: '../output/playwright/palette',
  use: { actionTimeout: 15_000, baseURL: 'http://127.0.0.1:5176', launchOptions: browserLaunchOptions, locale: 'ru-RU', reducedMotion: 'reduce' },
  webServer: { command: 'npm run dev -- --host 127.0.0.1 --port 5176 --strictPort', url: 'http://127.0.0.1:5176', reuseExistingServer: false },
  projects: [{ name: 'desktop', use: { viewport: { width: 1440, height: 900 } } }, { name: 'mobile', use: { viewport: { width: 390, height: 844 }, hasTouch: true } }],
})
