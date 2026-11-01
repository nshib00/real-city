import { defineConfig } from 'playwright/test'
import { browserLaunchOptions } from './playwright.browser'

export default defineConfig({
  testDir: './tests/e2e/design',
  outputDir: 'design-results',
  fullyParallel: false,
  workers: 1,
  retries: 0,
  timeout: 45_000,
  use: {
    launchOptions: browserLaunchOptions,
    baseURL: 'http://127.0.0.1:5173', locale: 'ru-RU', timezoneId: 'UTC',
    colorScheme: 'dark', reducedMotion: 'reduce', deviceScaleFactor: 1,
    trace: 'retain-on-failure',
  },
  webServer: {
    command: 'npm run dev -- --host 127.0.0.1 --strictPort',
    url: 'http://127.0.0.1:5173/design.html', reuseExistingServer: false,
  },
  projects: [
    { name: '1440x900', use: { viewport: { width: 1440, height: 900 } } },
    { name: '1024x768', use: { viewport: { width: 1024, height: 768 } } },
    { name: '390x844', use: { viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true } },
    { name: '320x700', use: { viewport: { width: 320, height: 700 }, isMobile: true, hasTouch: true } },
  ],
})
