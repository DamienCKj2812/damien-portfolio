import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { BufferGeometry, Float32BufferAttribute, Matrix4, Object3D, PerspectiveCamera, Quaternion, Vector3 } from 'three'
import { attachContactCardDismissal } from '../src/components/city/contactCardDismissal.ts'
import { sceneFile } from './node_json.mts'

const base = new URL('../public/models/rooms/about/', import.meta.url)
const manifest = sceneFile(new URL('scene.json', base), 'about')
const binary = readFileSync(new URL(manifest.geometry, base))
const group = manifest.groups.find(group => group.role === 'contact' && group.id === 'card')
assert.ok(group)
const positions = []
for (let i = 0; i < group.vertexCount; i++) for (let axis = 0; axis < 3; axis++) positions.push(binary.readFloatLE(group.byteOffset + (i * group.stride + axis) * 4))
const geometry = new BufferGeometry().setAttribute('position', new Float32BufferAttribute(positions, 3))
geometry.computeBoundingBox()
assert.ok(geometry.boundingBox)
const center = geometry.boundingBox.getCenter(new Vector3())
const rotation = new Quaternion().setFromAxisAngle(new Vector3(1, 0, 0), -Math.PI / 2)
  .multiply(new Quaternion().setFromAxisAngle(new Vector3(0, 0, 1), Math.PI))
const matrix = new Matrix4().compose(new Vector3(2.55, 30.615, 6.12), rotation, new Vector3(1, 1, 1))
const root = new Object3D()
root.matrixAutoUpdate = false
root.matrix.copy(matrix)
root.updateMatrixWorld(true)

function event(type: string, x: number, y: number, id = 1) {
  const event = new Event(type)
  Object.assign(event, { clientX: x, clientY: y, pointerId: id, button: 0 })
  return event
}

for (const [width, height] of [[1280, 800], [390, 844]]) {
  const view = new EventTarget()
  const canvas = Object.assign(new EventTarget(), {
    ownerDocument: { defaultView: view, hidden: false },
    getBoundingClientRect: () => ({ left: 0, top: 0, width, height }),
  })
  const pose = manifest.cameras.card
  const fov = Math.min(85, 2 * Math.atan(Math.tan(pose.fov * Math.PI / 360) * Math.max(1, 1.6 / (width / height))) * 180 / Math.PI)
  const camera = new PerspectiveCamera(fov, width / height, .01, 350)
  camera.position.fromArray(pose.position).applyMatrix4(matrix)
  camera.quaternion.copy(rotation).multiply(new Quaternion().fromArray(pose.quaternion))
  camera.updateMatrixWorld()
  let dismissals = 0, sceneClicks = 0
  // The fixture implements only the event target, document and rect operations
  // exercised by the handler; no browser canvas rendering is invoked here.
  const dispose = attachContactCardDismissal({ canvas: canvas as unknown as HTMLCanvasElement, camera, root, geometry, onDismiss: () => dismissals++ })
  const sceneClick = () => sceneClicks++
  canvas.addEventListener('click', sceneClick)
  const clickAt = (x: number, y: number) => {
    canvas.dispatchEvent(event('pointerdown', x, y))
    view.dispatchEvent(event('pointerup', x, y))
    canvas.dispatchEvent(event('click', x, y))
  }
  const card = center.clone().applyMatrix4(matrix).project(camera)
  const cardX = (card.x + 1) / 2 * width, cardY = (1 - card.y) / 2 * height
  clickAt(cardX, cardY)
  assert.equal(dismissals, 0, `Clicking the card must keep it open (${width}px viewport)`)
  clickAt(5, 5)
  assert.equal(dismissals, 1, 'Clicking the background must dismiss')
  assert.equal(sceneClicks, 1, 'Dismissal must stop the card pick from reopening it')

  canvas.dispatchEvent(event('pointerdown', 5, 5))
  view.dispatchEvent(event('pointermove', 40, 20))
  view.dispatchEvent(event('pointermove', 5, 5))
  view.dispatchEvent(event('pointerup', 5, 5))
  canvas.dispatchEvent(event('click', 5, 5))
  assert.equal(dismissals, 1, 'Dragging away and back must not dismiss')

  canvas.dispatchEvent(event('pointerdown', 5, 5, 1))
  canvas.dispatchEvent(event('pointerdown', 10, 10, 2))
  view.dispatchEvent(event('pointerup', 5, 5, 1))
  view.dispatchEvent(event('pointerup', 10, 10, 2))
  canvas.dispatchEvent(event('click', 5, 5, 1))
  assert.equal(dismissals, 1, 'Multi-touch must not dismiss')
  canvas.dispatchEvent(event('pointerdown', 5, 5))
  view.dispatchEvent(event('pointercancel', 5, 5))
  canvas.dispatchEvent(event('click', 5, 5))
  assert.equal(dismissals, 1, 'Cancelled gestures must not dismiss')

  canvas.ownerDocument.hidden = true
  clickAt(5, 5)
  assert.equal(dismissals, 1, 'Hidden page must not accept dismissal')
  canvas.ownerDocument.hidden = false
  dispose()
  clickAt(5, 5)
  assert.equal(dismissals, 1, 'Disabled or unmounted handler must be removed')
  canvas.removeEventListener('click', sceneClick)
}
geometry.dispose()
console.log('PASS contact-card dismissal: desktop/mobile card hits, background dismissal, no reopening, drag/multi-touch/cancel guards, hidden-page suspension and cleanup')
