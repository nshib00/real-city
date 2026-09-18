import { useEffect, useRef } from 'react'
import {
  AmbientLight,
  Box3,
  DirectionalLight,
  Group,
  OrthographicCamera,
  Scene,
  Vector3,
  WebGLRenderer,
} from 'three'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js'

import type { PlacedBuilding } from '../state/useGameStore'
import { buildingModelAsset } from './buildingModelAssets'

export function BuildingGlbModel({ building }: { building: PlacedBuilding }) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null)
  const asset = buildingModelAsset(building)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas || !asset || typeof WebGLRenderingContext === 'undefined') {
      return
    }

    const modelCanvas: HTMLCanvasElement = canvas
    let disposed = false
    const renderer = new WebGLRenderer({ canvas: modelCanvas, alpha: true, antialias: true })
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2))
    renderer.setClearColor(0x000000, 0)

    const scene = new Scene()
    const modelRoot = new Group()
    scene.add(modelRoot)
    scene.add(new AmbientLight(0xffffff, 1.8))
    const keyLight = new DirectionalLight(0xffffff, 2.6)
    keyLight.position.set(4, 5, 7)
    scene.add(keyLight)
    const fillLight = new DirectionalLight(0xb9d7ff, 1.1)
    fillLight.position.set(-5, 3, 2)
    scene.add(fillLight)

    const camera = new OrthographicCamera(-2.8, 2.8, 2.25, -2.25, 0.1, 100)
    camera.position.set(4.4, -5.4, 4.2)
    camera.lookAt(0, 0, 0.55)

    const loader = new GLTFLoader()
    loader.load(asset, (gltf) => {
      if (disposed) {
        return
      }
      modelRoot.add(gltf.scene)
      fitModelToCell(gltf.scene)
      render()
    })

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

    function render() {
      renderer.render(scene, camera)
    }

    resize()
    const observer = new ResizeObserver(resize)
    observer.observe(modelCanvas)

    return () => {
      disposed = true
      observer.disconnect()
      renderer.dispose()
      modelRoot.traverse((object) => {
        const mesh = object as { geometry?: { dispose: () => void }; material?: { dispose?: () => void } | { dispose?: () => void }[] }
        mesh.geometry?.dispose()
        if (Array.isArray(mesh.material)) {
          mesh.material.forEach((material) => material.dispose?.())
        } else {
          mesh.material?.dispose?.()
        }
      })
    }
  }, [asset])

  return <canvas className="building-glb-model" ref={canvasRef} aria-hidden="true" />
}

function fitModelToCell(model: Group) {
  const box = new Box3().setFromObject(model)
  const size = new Vector3()
  const center = new Vector3()
  box.getSize(size)
  box.getCenter(center)
  model.position.sub(center)
  const footprint = Math.max(size.x, size.y)
  if (footprint > 0) {
    model.scale.setScalar(3.55 / footprint)
  }
}
