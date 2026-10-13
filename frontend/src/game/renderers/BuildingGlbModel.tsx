import { useEffect, useRef, useState } from 'react'
import type { Group, Material, Texture } from 'three'

import type { PlacedBuilding } from '../state/useGameStore'
import { resolveBuildingModelAssetUrl } from './buildingRegistry'
import { acquireThreePreviewSlot, releaseThreePreviewSlot } from './threePreviewBudget'

export function BuildingGlbModel({ building }: { building: PlacedBuilding }) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null)
  const [status, setStatus] = useState<'idle' | 'busy' | 'missing' | 'unsupported' | 'failed'>('idle')

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas || typeof WebGLRenderingContext === 'undefined') {
      setStatus('unsupported')
      return
    }

    const modelCanvas: HTMLCanvasElement = canvas
    let disposed = false
    let slotAcquired = false
    let observer: ResizeObserver | null = null
    let cleanupScene: (() => void) | null = null

    void resolveBuildingModelAssetUrl(building).then((asset) => {
      if (disposed) {
        return null
      }
      if (!asset) {
        setStatus('missing')
        return null
      }
      if (!acquireThreePreviewSlot()) {
        setStatus('busy')
        return null
      }
      slotAcquired = true
      return Promise.all([
        Promise.resolve(asset),
        import('three'),
        import('three/examples/jsm/loaders/GLTFLoader.js'),
      ])
    }).then((modules) => {
      if (!modules || disposed) {
        return
      }
      const [asset, three, loaderModule] = modules

      const renderer = new three.WebGLRenderer({ canvas: modelCanvas, alpha: true, antialias: true })
      renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2))
      renderer.setClearColor(0x000000, 0)

      const scene = new three.Scene()
      const modelRoot = new three.Group()
      scene.add(modelRoot)
      scene.add(new three.AmbientLight(0xffffff, 1.8))
      const keyLight = new three.DirectionalLight(0xffffff, 2.6)
      keyLight.position.set(4, 5, 7)
      scene.add(keyLight)
      const fillLight = new three.DirectionalLight(0xb9d7ff, 1.1)
      fillLight.position.set(-5, 3, 2)
      scene.add(fillLight)

      const camera = new three.OrthographicCamera(-2.8, 2.8, 2.25, -2.25, 0.1, 100)
      camera.position.set(4.4, -5.4, 4.2)
      camera.lookAt(0, 0, 0.55)

      function render() {
        renderer.render(scene, camera)
      }

      function resize() {
        const width = Math.max(1, Math.round(modelCanvas.clientWidth))
        const height = Math.max(1, Math.round(modelCanvas.clientHeight))
        renderer.setSize(width, height, false)
        const aspect = width / height
        camera.left = -2.55 * aspect
        camera.right = 2.55 * aspect
        camera.top = 2.55
        camera.bottom = -2.55
        camera.updateProjectionMatrix()
        render()
      }

      const loader = new loaderModule.GLTFLoader()
      loader.load(
        asset,
        (gltf) => {
          if (disposed) {
            disposeModel(gltf.scene)
            return
          }
          modelRoot.add(gltf.scene)
          fitModelToCell(gltf.scene, three.Box3, three.Vector3)
          setStatus('idle')
          render()
        },
        undefined,
        () => {
          if (!disposed) {
            setStatus('failed')
          }
        },
      )

      resize()
      observer = new ResizeObserver(resize)
      observer.observe(modelCanvas)
      cleanupScene = () => {
        observer?.disconnect()
        renderer.dispose()
        disposeModel(modelRoot)
      }
    }).catch(() => {
      if (!disposed) {
        setStatus('failed')
      }
    })

    return () => {
      disposed = true
      cleanupScene?.()
      if (slotAcquired) {
        releaseThreePreviewSlot()
      }
    }
  }, [building])

  return (
    <>
      <canvas className="building-glb-model" ref={canvasRef} aria-hidden="true" />
      {status !== 'idle' ? <span className="building-model-preview-status">{previewStatusText[status]}</span> : null}
    </>
  )
}

const previewStatusText = {
  idle: '',
  busy: 'Лимит 3D preview исчерпан',
  missing: 'GLB не найден',
  unsupported: 'WebGL недоступен',
  failed: 'Не удалось загрузить GLB',
} as const

function fitModelToCell(model: Group, Box3Ctor: typeof import('three').Box3, Vector3Ctor: typeof import('three').Vector3) {
  const box = new Box3Ctor().setFromObject(model)
  const size = new Vector3Ctor()
  const center = new Vector3Ctor()
  box.getSize(size)
  box.getCenter(center)
  model.position.sub(center)
  const footprint = Math.max(size.x, size.y)
  if (footprint > 0) {
    model.scale.setScalar(3.55 / footprint)
  }
}

function disposeModel(model: Group) {
  model.traverse((object) => {
    const mesh = object as { geometry?: { dispose: () => void }; material?: Material | Material[] }
    mesh.geometry?.dispose()
    if (Array.isArray(mesh.material)) {
      mesh.material.forEach(disposeMaterial)
    } else if (mesh.material) {
      disposeMaterial(mesh.material)
    }
  })
}

function disposeMaterial(material: Material) {
  Object.values(material).forEach((value) => {
    const texture = value as Texture | undefined
    if (texture && typeof texture === 'object' && 'isTexture' in texture && texture.isTexture) {
      texture.dispose()
    }
  })
  material.dispose()
}
