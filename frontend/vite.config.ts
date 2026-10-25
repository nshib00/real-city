import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { readdir, rm } from 'node:fs/promises'
import path from 'node:path'

const apiProxyTarget = process.env.VITE_API_PROXY_TARGET ?? 'http://localhost:8080'
const runtimePublicGlbDirectories = [
  '/assets/buildings/housing/stone_house/',
  '/assets/buildings/housing/villa/',
  '/assets/buildings/industry/',
]
const nonRuntimeAssetPatterns = [
  /\.backup-/,
  /\.blend1?$/,
  /(?:^|[_-])(?:contact_sheet|review|preview)(?:[_-]|\.)/,
]

export default defineConfig({
  plugins: [react(), pruneNonRuntimePublicAssets()],
  build: {
    chunkSizeWarningLimit: 900,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes('node_modules')) {
            return undefined
          }
          if (id.includes('/pixi.js/')) {
            return 'vendor-pixi'
          }
          if (id.includes('/three/')) {
            return 'vendor-three-preview'
          }
          if (id.includes('/@tanstack/react-query/')) {
            return 'vendor-query'
          }
          if (id.includes('/react/') || id.includes('/react-dom/') || id.includes('/scheduler/')) {
            return 'vendor-react'
          }
          return 'vendor-misc'
        },
      },
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': apiProxyTarget,
    },
  },
  test: {
    environment: 'jsdom',
    exclude: ['node_modules/**', 'dist/**', 'tests/e2e/**'],
    globals: true,
  },
})

function pruneNonRuntimePublicAssets() {
  return {
    name: 'real-city-prune-non-runtime-public-assets',
    apply: 'build' as const,
    async closeBundle() {
      const assetsRoot = path.resolve('dist', 'assets')
      await pruneTree(assetsRoot)
    },
  }
}

async function pruneTree(dir: string) {
  let entries: Awaited<ReturnType<typeof readdir>>
  try {
    entries = await readdir(dir, { withFileTypes: true })
  } catch {
    return
  }
  await Promise.all(entries.map(async (entry) => {
    const entryPath = path.join(dir, entry.name)
    const normalized = entryPath.split(path.sep).join('/')
    const devOnlyDirectory = entry.isDirectory() && (entry.name === 'preview' || entry.name.startsWith('backup_') || entry.name.endsWith('_test'))
    const unusedGlb = normalized.endsWith('.glb') && !runtimePublicGlbDirectories.some((directory) => normalized.includes(directory))
    if (devOnlyDirectory || unusedGlb || nonRuntimeAssetPatterns.some((pattern) => pattern.test(normalized))) {
      await rm(entryPath, { recursive: true, force: true })
      return
    }
    if (entry.isDirectory()) {
      await pruneTree(entryPath)
    }
  }))
}
