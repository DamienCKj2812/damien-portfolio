import { Matrix4, Ray, Raycaster, Vector2, Vector3 } from 'three'
import type { BufferGeometry, Camera, Object3D } from 'three'

export interface ContactCardDismissalOptions {
  canvas: HTMLCanvasElement; camera: Camera; root: Object3D; geometry: BufferGeometry; onDismiss: () => void
}

export function attachContactCardDismissal({ canvas, camera, root, geometry, onDismiss }: ContactCardDismissalOptions) {
  const raycaster = new Raycaster(), ray = new Ray(), inverse = new Matrix4()
  const pointer = new Vector2(), a = new Vector3(), b = new Vector3(), c = new Vector3(), hit = new Vector3()
  const positions = geometry.getAttribute('position')
  geometry.computeBoundingBox()
  const bounds = geometry.boundingBox
  const view = canvas.ownerDocument.defaultView
  if (!bounds || !view) return () => {}
  const center = bounds.getCenter(new Vector3())
  const pressed = new Set<number>()
  let gesture: { id: number; x: number; y: number; moved: number; inside: boolean } | null = null
  let pending: number | null = null
  const insideCard = (event: PointerEvent) => {
    const rect = canvas.getBoundingClientRect()
    if (!rect.width || !rect.height) return false
    pointer.set((event.clientX - rect.left) / rect.width * 2 - 1, 1 - (event.clientY - rect.top) / rect.height * 2)
    root.updateWorldMatrix(true, false)
    raycaster.setFromCamera(pointer, camera)
    ray.copy(raycaster.ray).applyMatrix4(inverse.copy(root.matrixWorld).invert())
    for (let i = 0; i < positions.count; i += 3) {
      a.fromBufferAttribute(positions, i);b.fromBufferAttribute(positions, i + 1);c.fromBufferAttribute(positions, i + 2)
      // Include the paper's narrow margin beyond its inset contact face.
      for (const point of [a, b, c]) point.sub(center).multiplyScalar(1.05).add(center)
      if (ray.intersectTriangle(a, b, c, false, hit)) return true
    }
    return false
  }
  const down = (event: PointerEvent) => {
    if (event.button !== 0) return
    pressed.add(event.pointerId);pending = null
    gesture = pressed.size === 1 ? { id: event.pointerId, x: event.clientX, y: event.clientY, moved: 0, inside: insideCard(event) } : null
  }
  const move = (event: PointerEvent) => {
    if (gesture?.id === event.pointerId) gesture.moved = Math.max(gesture.moved, Math.hypot(event.clientX - gesture.x, event.clientY - gesture.y))
  }
  const up = (event: PointerEvent) => {
    pressed.delete(event.pointerId)
    move(event)
    if (gesture?.id === event.pointerId && gesture.moved <= 5 && !gesture.inside && !insideCard(event)) pending = event.pointerId
    gesture = null
  }
  const cancel = (event: PointerEvent) => { pressed.delete(event.pointerId);gesture = null;pending = null }
  const reset = () => { pressed.clear();gesture = null;pending = null }
  const click = (event: MouseEvent) => {
    const accepted = pending !== null && event.button === 0 && !canvas.ownerDocument.hidden &&
      (!('pointerId' in event) || event.pointerId == null || event.pointerId === pending)
    pending = null
    if (!accepted) return
    // Stop the oversized contactPick from reopening the card on the same click.
    event.stopImmediatePropagation()
    onDismiss()
  }
  canvas.addEventListener('pointerdown', down)
  canvas.addEventListener('click', click, true)
  view.addEventListener('pointermove', move)
  view.addEventListener('pointerup', up)
  view.addEventListener('pointercancel', cancel)
  view.addEventListener('blur', reset)
  return () => {
    reset()
    canvas.removeEventListener('pointerdown', down)
    canvas.removeEventListener('click', click, true)
    view.removeEventListener('pointermove', move)
    view.removeEventListener('pointerup', up)
    view.removeEventListener('pointercancel', cancel)
    view.removeEventListener('blur', reset)
  }
}
