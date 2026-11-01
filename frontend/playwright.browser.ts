import { existsSync } from 'node:fs'

// Явный путь имеет приоритет; CI без системного Chromium использует браузер Playwright.
export const browserLaunchOptions = {
  executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH
    || (existsSync('/usr/bin/chromium-browser') ? '/usr/bin/chromium-browser' : undefined),
  args: ['--enable-webgl', '--use-gl=angle', `--use-angle=${process.env.PLAYWRIGHT_GL_BACKEND || (!process.env.CI && existsSync('/dev/dri/renderD128') ? 'gl' : 'swiftshader')}`],
}
