import { defineConfig } from 'playwright/test'
import interfaceConfig from './playwright.interface.config'

export default defineConfig({ ...interfaceConfig, testMatch: 'interface-rollout.spec.ts', outputDir: 'rollout-results' })
