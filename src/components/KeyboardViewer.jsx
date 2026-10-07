import { Component, Suspense } from 'react'
import { Canvas } from '@react-three/fiber'
import { Bounds, Center, OrbitControls, useGLTF, useProgress } from '@react-three/drei'
import keyboardUrl from '../../split-keyboard.glb?url'

function KeyboardModel() {
  const { scene } = useGLTF(keyboardUrl)

  return (
    <Bounds fit clip observe margin={1.25}>
      <group rotation={[0, 0, Math.PI / 2]}>
        <Center rotation={[Math.PI / 2, 0, 0]}>
          <primitive object={scene} />
        </Center>
      </group>
    </Bounds>
  )
}

function LoadingIndicator() {
  const { active } = useProgress()
  if (!active) return null
  return <p className="pointer-events-none absolute inset-0 z-10 flex items-center justify-center text-sm text-white" role="status">Loading keyboard…</p>
}

class ViewerErrorBoundary extends Component {
  state = { error: null }

  static getDerivedStateFromError(error) {
    return { error }
  }

  componentDidCatch(error, info) {
    console.error('Keyboard viewer failed:', error, info.componentStack)
  }

  render() {
    if (this.state.error) {
      return (
        <div className="flex h-full flex-col items-center justify-center gap-3 px-6 text-center text-[#b4b5be]" role="alert">
          <p>The 3D viewer couldn’t load.</p>
          <p className="max-w-xl break-words text-sm">{this.state.error.message}</p>
          <button className="cursor-pointer rounded-lg border border-[#35363e] px-4 py-2 hover:text-white" onClick={() => this.setState({ error: null })}>Try again</button>
        </div>
      )
    }

    return this.props.children
  }
}

export default function KeyboardViewer() {
  return (
    <section className="section" id="keyboard-demo" aria-labelledby="keyboard-demo-title">
      <p className="eyebrow">3D / PLAYGROUND</p>
      <h2 id="keyboard-demo-title">A closer look at my keyboard</h2>
      <p>A test of the Blender model. Drag to rotate, pinch or scroll over the viewer to zoom.</p>
      <div className="relative mt-7 h-[460px] overflow-hidden rounded-xl border border-[#292a31] bg-[#15161a] sm:h-[600px]" role="region" aria-label="Interactive 3D split keyboard preview">
        <ViewerErrorBoundary>
          <Canvas
            frameloop="demand"
            dpr={[1, 1.5]}
            camera={{ position: [0, 0, 18], fov: 45 }}
            fallback={<p className="p-6 text-[#b4b5be]">Your browser does not support WebGL. The rest of the portfolio is still available.</p>}
          >
            <ambientLight intensity={1.2} />
            <directionalLight position={[5, 8, 10]} intensity={2.5} />
            <directionalLight position={[-5, -2, 5]} intensity={1} />
            <Suspense fallback={null}>
              <KeyboardModel />
            </Suspense>
            <OrbitControls makeDefault enablePan={false} />
          </Canvas>
          <LoadingIndicator />
        </ViewerErrorBoundary>
      </div>
      <p className="mt-3 text-sm">Interactive preview · Original materials · Pixelated monochrome styling comes next.</p>
    </section>
  )
}
