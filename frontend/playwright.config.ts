import { defineConfig, devices } from 'playwright/test'
export default defineConfig({
 testDir: './tests/e2e', testMatch: ['**/real-gameplay.spec.ts', '**/live-world.spec.ts'], fullyParallel: false, workers: 1,
 timeout: 90_000, expect: { timeout: 15_000 }, retries: process.env.CI ? 1 : 0,
 reporter: process.env.CI ? [['github'], ['html', { open: 'never' }]] : 'list',
 use: { baseURL: 'http://127.0.0.1:5173', trace: 'retain-on-failure', screenshot: 'only-on-failure' },
 webServer: { command: 'npm run dev -- --host 127.0.0.1', url: 'http://127.0.0.1:5173', reuseExistingServer: !process.env.CI,
  env: { VITE_API_PROXY_TARGET: process.env.REAL_CITY_API_URL ?? 'http://127.0.0.1:18080' } },
 projects: [{ name: 'desktop', use: { ...devices['Desktop Chrome'] } }, { name: 'mobile', use: { ...devices['Pixel 7'] } }],
})
