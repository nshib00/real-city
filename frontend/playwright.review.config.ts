import { defineConfig } from 'playwright/test'
import { browserLaunchOptions } from './playwright.browser'

export default defineConfig({
  testDir: './tests/e2e', testMatch: ['browser-review.spec.ts', 'world-review.spec.ts'], workers: 1,
  timeout: 90_000, outputDir: 'review-results',
  expect: { timeout: 15_000 },
  use: { actionTimeout: 15_000, launchOptions: browserLaunchOptions, baseURL: 'http://127.0.0.1:5174', locale: 'ru-RU',
    reducedMotion: 'reduce', trace: 'retain-on-failure', screenshot: 'only-on-failure' },
  webServer: { command: 'npm run dev -- --host 127.0.0.1 --port 5174 --strictPort', url: 'http://127.0.0.1:5174', reuseExistingServer: false },
  projects: [
    ...[320, 390, 768, 1024, 1440].map(width => ({ name: `${width}-dpr1`, use: { viewport: { width, height: 900 }, hasTouch: width <= 768 } })),
    { name: 'landscape', use: { viewport: { width: 844, height: 390 }, hasTouch: true } },
    ...[390, 1440].map(width => ({ name: `${width}-dpr2`, use: { viewport: { width, height: 900 }, deviceScaleFactor: 2, hasTouch: width === 390 } })),
  ],
})
