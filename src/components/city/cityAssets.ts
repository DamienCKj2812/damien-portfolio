import { BufferGeometry, InterleavedBuffer, InterleavedBufferAttribute, ShaderMaterial, SRGBColorSpace, TextureLoader } from 'three'
import { LineSegmentsGeometry } from 'three/addons/lines/LineSegmentsGeometry.js'
import type { IUniform, ShaderMaterialParameters, Texture } from 'three'
import { packedNumber } from '../../types/packedNumbers'
import { prepareLinearRoomRoute } from './linearRoomRoute'
import { isCityManifest, isElevatorManifest, isLobbyManifest, parseJourneyConfig, parseSceneManifest } from '../../types/sceneValidation'
import type { CityManifest, LobbyManifest, ElevatorManifest, RoomManifest, LoadedSceneAssets, RoomDestination, SceneGeometry } from '../../types/scene'

export const CITY_ASSET_BASE = `${import.meta.env.BASE_URL}models/city/`
export const LOBBY_ASSET_BASE = `${import.meta.env.BASE_URL}models/lobby/`
export const ELEVATOR_ASSET_BASE = `${import.meta.env.BASE_URL}models/elevator/`

// ShaderMaterial retains the supplied uniforms object; the intersection records
// its concrete keys without changing the material or uniform resource identity.
export function createSceneShaderMaterial<U extends Record<string, IUniform<unknown>>>(parameters: Omit<ShaderMaterialParameters, 'uniforms'>, uniforms: U): ShaderMaterial & { uniforms: U } {
  return Object.assign(new ShaderMaterial({ ...parameters, uniforms }), { uniforms })
}

function fetchAsset(url: string, signal: AbortSignal, type: 'json'): Promise<unknown>
function fetchAsset(url: string, signal: AbortSignal, type: 'binary'): Promise<ArrayBuffer>
async function fetchAsset(url: string, signal: AbortSignal, type: 'json' | 'binary'): Promise<unknown> {
  const response = await fetch(url, { signal, cache: type === 'json' ? 'no-cache' : 'default' })
  if (!response.ok) throw new Error(`City asset failed to load (${response.status}).`)
  return type === 'json' ? response.json() : response.arrayBuffer()
}

export async function loadSceneAssets(base: string, signal: AbortSignal): Promise<LoadedSceneAssets> {
  const manifest = parseSceneManifest(await fetchAsset(`${base}scene.json`, signal, 'json'))
  if (![1, 2, 3].includes(manifest.version)) throw new Error('Unsupported city asset version.')
  const version = manifest.assetHash ? `?v=${manifest.assetHash}` : ''
  const route = manifest.level === 'skills' || manifest.level === 'experience' ? manifest.navigation.route : undefined
  const [geometryBuffer, animationBuffer, routeBuffer] = await Promise.all([
    fetchAsset(`${base}${manifest.geometry}${version}`, signal, 'binary'),
    fetchAsset(`${base}${manifest.animation}${version}`, signal, 'binary'),
    route ? fetchAsset(`${base}${route.file}${version}`, signal, 'binary') : Promise.resolve(null),
  ])
  const frameCount = manifest.frameEnd - manifest.frameStart + 1
  if (animationBuffer.byteLength !== frameCount * manifest.channelCount * manifest.channelStride * 4) {
    throw new Error('City animation data is incomplete. Refresh to load the latest assets.')
  }
  if (route && (!routeBuffer || routeBuffer.byteLength !== (route.frameEnd - route.frameStart + 1) * route.stride * 4)) throw new Error('Room guided path data is incomplete. Retry to load the latest assets.')
  for (const group of manifest.groups) {
    if (!['points', 'lines', 'outline', 'glow', 'solid', 'screen', 'mask'].includes(group.kind)) throw new Error('Unsupported city geometry type.')
    if (group.byteOffset + group.floatCount * 4 > geometryBuffer.byteLength) {
      throw new Error('City geometry data is incomplete.')
    }
    for (const morph of group.morphs || []) {
      if (morph.floatCount !== group.vertexCount * 3 || morph.byteOffset + morph.floatCount * 4 > geometryBuffer.byteLength) throw new Error('Room animation geometry is incomplete.')
    }
  }
  const textures: Record<string, Texture> = {}
  const loader = new TextureLoader()
  const images = await Promise.allSettled((manifest.textures || []).map(async (file) => {
    const texture = await loader.loadAsync(`${base}${file}${version}`)
    texture.colorSpace = SRGBColorSpace
    texture.anisotropy = 4
    return { file, texture }
  }))
  for (const image of images) {
    if (image.status === 'fulfilled') textures[image.value.file] = image.value.texture
  }
  const failedImage = images.find((image) => image.status === 'rejected')
  if (signal.aborted || failedImage) {
    for (const texture of Object.values(textures)) texture.dispose()
    if (signal.aborted) throw new DOMException('City loading aborted.', 'AbortError')
    throw new Error('A city billboard could not load. Refresh to try again.')
  }
  return prepareLinearRoomRoute({ manifest, geometryBuffer, animation: new Float32Array(animationBuffer), route: routeBuffer ? new Float32Array(routeBuffer) : null, textures })
}

function rejectScenePackage(assets: LoadedSceneAssets, message: string): never {
  for (const texture of Object.values(assets.textures)) texture.dispose()
  throw new Error(message)
}

export async function loadCityAssets(signal: AbortSignal): Promise<LoadedSceneAssets<CityManifest>> {
  const assets = await loadSceneAssets(CITY_ASSET_BASE, signal)
  const manifest = assets.manifest
  if (!isCityManifest(manifest)) return rejectScenePackage(assets, 'Expected a city scene package.')
  return { ...assets, manifest }
}
export async function loadLobbyAssets(signal: AbortSignal): Promise<LoadedSceneAssets<LobbyManifest>> {
  const assets = await loadSceneAssets(LOBBY_ASSET_BASE, signal)
  const manifest = assets.manifest
  if (!isLobbyManifest(manifest)) return rejectScenePackage(assets, 'Expected a lobby scene package.')
  return { ...assets, manifest }
}
export async function loadElevatorAssets(signal: AbortSignal): Promise<LoadedSceneAssets<ElevatorManifest>> {
  const assets = await loadSceneAssets(ELEVATOR_ASSET_BASE, signal)
  const manifest = assets.manifest
  if (!isElevatorManifest(manifest)) return rejectScenePackage(assets, 'Expected an elevator scene package.')
  return { ...assets, manifest }
}
export async function loadJourneyConfig(signal: AbortSignal) {
  return parseJourneyConfig(await fetchAsset(`${import.meta.env.BASE_URL}models/journey.json`, signal, 'json'))
}
export async function loadRoomAssets(room: RoomDestination, signal: AbortSignal): Promise<LoadedSceneAssets<RoomManifest>> {
  const assets = await loadSceneAssets(`${import.meta.env.BASE_URL}${room.assetBase}`, signal)
  const manifest = assets.manifest
  if (manifest.level === undefined) return rejectScenePackage(assets, 'Expected a room scene package.')
  return { ...assets, manifest }
}

export function createCityGeometries(assets: LoadedSceneAssets): SceneGeometry[] {
  return assets.manifest.groups.map((descriptor) => {
    const data = new Float32Array(assets.geometryBuffer, descriptor.byteOffset, descriptor.floatCount)
    if (descriptor.kind === 'outline' || descriptor.kind === 'glow') {
      // Establish the bounded position/luminance read range once at creation.
      if (!Number.isInteger(descriptor.stride) || descriptor.stride < 4 || !Number.isInteger(descriptor.vertexCount) || descriptor.vertexCount < 0 || descriptor.vertexCount * descriptor.stride > data.length) throw new Error('City line geometry data is incomplete.')
      const positions = new Float32Array(descriptor.vertexCount * 3)
      const colors = new Float32Array(descriptor.vertexCount * 3)
      for (let i = 0; i < descriptor.vertexCount; i++) {
        positions.set(data.subarray(i * descriptor.stride, i * descriptor.stride + 3), i * 3)
        colors.fill(packedNumber(data, i * descriptor.stride + 3), i * 3, i * 3 + 3)
      }
      const geometry = new LineSegmentsGeometry()
      geometry.setPositions(positions)
      geometry.setColors(colors)
      geometry.computeBoundingSphere()
      return { ...descriptor, geometry }
    }
    const buffer = new InterleavedBuffer(data, descriptor.stride)
    const geometry = new BufferGeometry()
    geometry.setAttribute('position', new InterleavedBufferAttribute(buffer, 3, 0))
    for (const [index, morph] of (descriptor.morphs || []).entries()) {
      const delta = new InterleavedBuffer(new Float32Array(assets.geometryBuffer, morph.byteOffset, morph.floatCount), 3)
      geometry.setAttribute(`shape${index}`, new InterleavedBufferAttribute(delta, 3, 0))
    }
    if (descriptor.kind === 'points') {
      geometry.setAttribute('radius', new InterleavedBufferAttribute(buffer, 1, 3))
      geometry.setAttribute('luminance', new InterleavedBufferAttribute(buffer, 1, 4))
    } else if (descriptor.kind === 'screen') {
      geometry.setAttribute('uv', new InterleavedBufferAttribute(buffer, 2, 3))
    } else if (descriptor.kind === 'lines' || descriptor.kind === 'solid') {
      geometry.setAttribute('luminance', new InterleavedBufferAttribute(buffer, 1, 3))
    }
    geometry.computeBoundingSphere()
    if (descriptor.morphs?.length && geometry.boundingSphere) geometry.boundingSphere.radius += .6
    if (descriptor.kind === 'points' && geometry.boundingSphere && assets.manifest.actors.some((actor) => actor.index === descriptor.actor && actor.walk)) geometry.boundingSphere.radius += 0.25
    return { ...descriptor, geometry }
  })
}
