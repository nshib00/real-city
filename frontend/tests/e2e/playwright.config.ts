import { defineConfig } from 'playwright/test'

export default defineConfig({
  testDir: '.',
  testMatch: ['ui.spec.ts', 'pixi-canvas.spec.ts'],
  timeout: 45_000,
  expect: { timeout: 15_000 },
  workers: process.env.CI ? 2 : undefined,
  retries: process.env.CI ? 1 : 0,
  use: {
    baseURL: 'http://127.0.0.1:5173',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    launchOptions: { args: ['--enable-webgl', '--use-gl=angle', '--use-angle=swiftshader'] },
  },
  webServer: {
    command: 'npm run dev -- --host 127.0.0.1 --strictPort',
    cwd: '../..',
    url: 'http://127.0.0.1:5173',
    reuseExistingServer: !process.env.CI,
    timeout: 60_000,
  },
})
