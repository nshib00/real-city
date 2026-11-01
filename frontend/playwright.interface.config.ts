import { defineConfig } from 'playwright/test'
import { browserLaunchOptions } from './playwright.browser'

export default defineConfig({
  testDir: './tests/e2e', testMatch: 'ui.spec.ts', workers: 1, retries: 0,
  outputDir: 'interface-results',
  timeout: 60_000, expect: { timeout: 15_000 },
  use: { launchOptions: browserLaunchOptions, baseURL: 'http://127.0.0.1:5173', locale: 'ru-RU', reducedMotion: 'reduce', screenshot: 'only-on-failure' },
  webServer: { command: 'npm run dev -- --host 127.0.0.1 --strictPort', url: 'http://127.0.0.1:5173', reuseExistingServer: false },
  projects: [
    ...[320, 390, 768, 1024, 1440].map((width) => ({ name: `${width}-portrait`, use: { viewport: { width, height: 900 }, hasTouch: width <= 768 } })),
    { name: 'mobile-landscape', use: { viewport: { width: 844, height: 390 }, hasTouch: true } },
  ],
})
