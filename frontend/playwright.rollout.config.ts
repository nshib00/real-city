import { defineConfig } from 'playwright/test'
import interfaceConfig from './playwright.interface.config'

export default defineConfig({
  ...interfaceConfig,
  testMatch: 'interface-rollout.spec.ts',
  outputDir: 'rollout-results',
  use: { ...interfaceConfig.use, baseURL: 'http://127.0.0.1:5176' },
  webServer: {
    command: 'npm run dev -- --host 127.0.0.1 --port 5176 --strictPort',
    url: 'http://127.0.0.1:5176',
    reuseExistingServer: !process.env.CI,
  },
})
