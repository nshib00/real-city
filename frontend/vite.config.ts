import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { readdir, rm } from 'node:fs/promises'
import path from 'node:path'
import { isRuntimeAsset } from './scripts/runtime-assets.mjs'

const apiProxyTarget = process.env.VITE_API_PROXY_TARGET ?? 'http://localhost:8080'

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
      '/api': { target: apiProxyTarget, ws: true },
      '/ready': apiProxyTarget,
    },
  },
  test: {
    environment: 'jsdom',
    exclude: ['node_modules/**', 'dist/**', 'tests/e2e/**', 'scripts/**'],
    globals: true,
  },
})

function pruneNonRuntimePublicAssets() {
  return {
    name: 'real-city-prune-non-runtime-public-assets',
    apply: 'build' as const,
    async closeBundle() {
      const assetsRoot = path.resolve('dist', 'assets')
      await pruneTree(assetsRoot, assetsRoot)
    },
  }
}

async function pruneTree(dir: string, root: string) {
  let entries: Awaited<ReturnType<typeof readdir>>
  try {
    entries = await readdir(dir, { withFileTypes: true })
  } catch {
    return
  }
  await Promise.all(entries.map(async (entry) => {
    const entryPath = path.join(dir, entry.name)
    if (!isRuntimeAsset(path.relative(root, entryPath))) {
      await rm(entryPath, { recursive: true, force: true })
      return
    }
    if (entry.isDirectory()) {
      await pruneTree(entryPath, root)
    }
  }))
}
