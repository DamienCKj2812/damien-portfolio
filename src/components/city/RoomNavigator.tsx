/* eslint react-hooks/immutability: "off" -- Demand-rendered camera/navigation resources are mutable Three.js objects. */
import { useEffect, useMemo, useRef } from 'react'
import { useFrame, useThree } from '@react-three/fiber'
import { Box3, Frustum, MathUtils, Matrix4, PerspectiveCamera, Quaternion, Vector3 } from 'three'
import { isRoomAtEntrance, readRoomRoute } from './roomJourney'
import { advanceCameraSpring } from './cameraMotion'
import useSoundEffects from '../../audio/useSoundEffects'
import { clampHallwayY } from './hallwayCategories'
import { createProjectCardFocus } from './projectCardFocus'
import { createHallwayPortalAudio } from './hallwayPortalAudio'
import type { RefObject } from 'react'
import type { LoadedGuidedRoomAssets, LoadedRoomAssets } from '../../types/scene'
import type { ActiveNavigationState, CameraFocusState, NavigationState, RoomAlignment, RoomState, RoomView } from '../../types/navigation'

export interface RoomNavigatorProps {
  assets: LoadedRoomAssets; alignment: RoomAlignment; active: boolean; arrived: boolean; roomState: RoomState
  navigationRef: RefObject<NavigationState>; reducedMotion: boolean; roomFrameRef: RefObject<number>
  onFrame: (frame: number, y: number, walkFrame: number | null, x: number) => void
  onRequestReturn: () => void; onView: (view: RoomView) => void; onToggleWalk: () => void
  onSeekTour: (frame: number, manual?: boolean) => void; onStation: (direction: number) => void; onTourEnd: () => void
}

// The navigator installs these fields in its setup effect. Consumers can safely
// narrow the shared mutable ref only once that installation has completed.
function isActiveNavigationState(nav: NavigationState): nav is ActiveNavigationState {
  return nav.walkFrame !== undefined && nav.walkTarget !== undefined && nav.walkManual !== undefined &&
    nav.walkSpring !== undefined && nav.finished !== undefined && nav.position !== undefined &&
    nav.cameraPosition !== undefined && nav.returnRequested !== undefined && nav.returnCooldown !== undefined &&
    nav.portalAudioSeeking !== undefined
}

function isGuidedRoomAssets(assets: LoadedRoomAssets): assets is LoadedGuidedRoomAssets {
  return (assets.manifest.level === 'skills' || assets.manifest.level === 'experience') && assets.route !== null
}

const BASIS = new Quaternion().setFromAxisAngle(new Vector3(1, 0, 0), -Math.PI / 2)
const INVERSE_BASIS = BASIS.clone().invert()

export default function RoomNavigator({ assets, alignment, active, arrived, roomState, navigationRef, reducedMotion, roomFrameRef, onFrame, onRequestReturn, onView, onToggleWalk, onSeekTour, onStation, onTourEnd }: RoomNavigatorProps) {
  const { click: playClick, portalCrossing: playPortal } = useSoundEffects()
  const { camera, gl, size, invalidate } = useThree()
  const clock = useRef(0)
  const lastTick = useRef(0)
  const visible = useRef(true)
  const animationVisible = useRef(!assets.manifest.navigation?.animationBounds)
  const guided = assets.manifest.navigation?.type === 'guided'
  const lookOnly = assets.manifest.navigation?.type === 'look'
  const currentX = useRef(assets.manifest.cameras.main.position[0])
  const currentY = useRef(assets.manifest.cameras.main.position[1])
  const currentYaw = useRef(0)
  const currentPitch = useRef(.02)
  const focus = useRef<CameraFocusState>({ position: null, quaternion: null, fov: null })
  const homeTransition = useRef(false)
  const previousView = useRef(roomState.view)
  const portalAudio = useMemo(() => assets.manifest.level === 'projects' ? createHallwayPortalAudio(assets.manifest.navigation) : null, [assets])
  const viewOffset = useRef({x:0,y:0})
  const focusedCard = assets.manifest.level==='projects'&&roomState.view==='directory' ? assets.manifest.directory : assets.manifest.level==='projects' && roomState.view==='project' ? assets.manifest.projects.find(project=>project.id===roomState.project) : assets.manifest.level==='experience' && roomState.view==='timeline' || assets.manifest.level==='skills' && roomState.view==='skill' ? assets.manifest.exhibits.find(entry=>entry.id===roomState.exhibit) : null
  const cardFocus = useMemo(()=>focusedCard?createProjectCardFocus(focusedCard,alignment,size,['timeline','skill'].includes(roomState.view)||roomState.projectExploring):null,[focusedCard,alignment,size,roomState.view,roomState.projectExploring])
  const inverseAlignment = useMemo(()=>alignment.rotation.clone().invert(),[alignment])
  const animationBox = useMemo(() => {
    const bounds = assets.manifest.navigation?.animationBounds
    if (!bounds) return null
    const transform = new Matrix4().compose(alignment.position.clone().applyQuaternion(BASIS), BASIS.clone().multiply(alignment.rotation), new Vector3(1, 1, 1))
    return new Box3(new Vector3().fromArray(bounds.min), new Vector3().fromArray(bounds.max)).applyMatrix4(transform)
  }, [assets, alignment])
  const scratch = useMemo(() => ({ position: new Vector3(), localPosition:new Vector3(), corner:new Vector3(), quaternion: new Quaternion(), horizontal: new Quaternion(), tilt: new Quaternion(), up: new Vector3(0, 0, 1), right: new Vector3(1, 0, 0), frustum: new Frustum(), projection: new Matrix4() }), [])
  useEffect(() => {
    const nav = navigationRef.current
    nav.y = assets.manifest.cameras.main.position[1];nav.yaw = assets.manifest.navigation?.initialYaw || 0;nav.pitch = assets.manifest.navigation?.initialPitch ?? .02;nav.forward = 0;nav.fast = false;nav.dragDistance = 0;nav.invalidate = invalidate;nav.walkFrame = 1;nav.finished = false
    nav.position = [...assets.manifest.cameras.main.position]
    nav.cameraPosition = [...nav.position];nav.projectCardFramed=false
    nav.returnRequested = false;nav.returnCooldown = 0
    nav.portalAudioSeeking = false
    portalAudio?.reset(nav.y)
    nav.walkTarget = 1;nav.walkManual = false;nav.walkSpring = { value: 1, velocity: 0 }
    currentY.current = nav.y;currentYaw.current = nav.yaw;currentPitch.current = nav.pitch;clock.current = 0
    animationVisible.current = !animationBox
    return () => { nav.forward = 0;nav.invalidate = null }
  }, [assets, animationBox, navigationRef, invalidate, portalAudio])
  useEffect(()=>()=>{ if (camera instanceof PerspectiveCamera && camera.view?.enabled) camera.clearViewOffset() },[camera])
  useEffect(() => { lastTick.current = performance.now();invalidate() }, [active, arrived, roomState.view, roomState.project, roomState.exhibit, roomState.projectExploring, roomState.paused, roomState.walkPaused, roomState.profileOpen, roomState.returnPrompt, roomState.openedCategories, reducedMotion, size.width, size.height, invalidate])
  useEffect(() => {
    const observer = new IntersectionObserver(([entry]) => { if (!entry) return;visible.current = entry.isIntersecting;lastTick.current = performance.now();if (entry.isIntersecting) invalidate() })
    observer.observe(gl.domElement)
    const resume = () => { lastTick.current = performance.now();if (!document.hidden) invalidate() }
    document.addEventListener('visibilitychange', resume)
    return () => { observer.disconnect();document.removeEventListener('visibilitychange', resume) }
  }, [gl, invalidate])
  useEffect(() => {
    if (!arrived || !(camera instanceof PerspectiveCamera)) { focus.current.position = null;return }
    const aspect = size.width / Math.max(1, size.height)
    focus.current = {
      position: camera.position.clone().applyQuaternion(INVERSE_BASIS),
      quaternion: INVERSE_BASIS.clone().multiply(camera.quaternion).normalize(),
      fov: MathUtils.radToDeg(2 * Math.atan(Math.tan(MathUtils.degToRad(camera.fov)/2) / Math.max(1, 1.6/aspect))),
    }
    homeTransition.current = roomState.view==='main' && (lookOnly || ['project','timeline','skill','directory'].includes(previousView.current))
    previousView.current = roomState.view
  }, [arrived, alignment, roomState.view, roomState.project, roomState.exhibit, camera, size.width, size.height, lookOnly])
  useEffect(() => {
    if (!active || !arrived || roomState.profileOpen || roomState.returnPrompt) return
    const canvas = gl.domElement
    const navigation = navigationRef.current
    if (!isActiveNavigationState(navigation)) return
    const limits = assets.manifest.navigation
    const oldTabIndex = canvas.getAttribute('tabindex')
    canvas.tabIndex = 0
    const keys = new Set<string>()
    let drag: { x: number; y: number; startX: number; startY: number; touch: boolean; mode: 'look' | 'scroll' | null } | null = null
    const touches = new Set<number>()
    const editable = (target: EventTarget | null) => target instanceof Element && target.closest('input, select, textarea, button, a, [role="dialog"]')
    const scroll = (pixels: number) => {
      if (!pixels || navigation.returnRequested || performance.now() < navigation.returnCooldown) return
      if (roomState.view !== 'main') { if (pixels < 0 && !['project','timeline'].includes(roomState.view)) onView('main');return }
      if (pixels < 0 && isRoomAtEntrance(assets, navigation, roomState.view)) {
        navigation.forward = 0;navigation.returnRequested = true;keys.clear();drag = null
        onRequestReturn();return
      }
      const limits = assets.manifest.navigation
      if (guided) onSeekTour((navigation.walkTarget ?? navigation.walkFrame) + pixels * .15, true)
      else if (limits?.type === 'axis') { navigation.y = clampHallwayY(limits, navigation.y + pixels * .012);invalidate() }
    }
    const updateKeys = () => {
      const nav = navigationRef.current
      nav.forward = Number(keys.has('w') || keys.has('ArrowUp')) - Number(keys.has('s') || keys.has('ArrowDown'))
      nav.fast = keys.has('Shift');invalidate()
    }
    const keydown = (event: KeyboardEvent) => {
      if (event.defaultPrevented || !visible.current || editable(event.target) || event.ctrlKey || event.metaKey || event.altKey) return
      const discreteAction = event.key === 'Home' || event.key === 'Escape' && roomState.view !== 'main' ||
        roomState.view === 'main' && (guided && (event.code === 'Space' || ['ArrowLeft', 'ArrowRight'].includes(event.key) || event.key.toLowerCase() === 'r') || lookOnly && event.key.toLowerCase() === 'r')
      if (discreteAction && !event.repeat) playClick()
      if (event.key === 'Escape') { if (roomState.view !== 'main') { event.preventDefault();onView('main') }return }
      if (['PageUp', 'PageDown'].includes(event.key)) { event.preventDefault();if (!event.repeat) scroll((event.key === 'PageUp' ? -1 : 1) * window.innerHeight);return }
      if (event.key === 'Home') {
        event.preventDefault()
        if (limits.type === 'guided') onSeekTour(limits.route.frameStart)
        else {
          onView('main')
          if (limits.type === 'look') { navigation.yaw += Math.atan2(Math.sin(limits.initialYaw - navigation.yaw), Math.cos(limits.initialYaw - navigation.yaw));navigation.pitch = limits.initialPitch }
          else if (limits.type === 'axis') { navigation.y = limits.minY;navigation.portalAudioSeeking = true }
          navigation.forward = 0;invalidate()
        }
        return
      }
      if (!assets.manifest.navigation) return
      if (limits.type === 'look') {
        if (roomState.view !== 'main') return
        if (event.key.toLowerCase() === 'r') { event.preventDefault();navigation.yaw += Math.atan2(Math.sin(limits.initialYaw - navigation.yaw), Math.cos(limits.initialYaw - navigation.yaw));navigation.pitch = limits.initialPitch;invalidate();return }
        if (['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown'].includes(event.key)) {
          event.preventDefault()
          navigation.yaw += event.key === 'ArrowLeft' ? -.12 : event.key === 'ArrowRight' ? .12 : 0
          navigation.pitch = MathUtils.clamp(navigation.pitch + (event.key === 'ArrowUp' ? .08 : event.key === 'ArrowDown' ? -.08 : 0), -Math.PI * .47, Math.PI * .47)
          invalidate()
        }
        return
      }
      if (limits.type === 'guided') {
        if (roomState.view !== 'main') return
        if (event.code === 'Space') { event.preventDefault();if (!event.repeat) onToggleWalk();return }
        if (['ArrowLeft', 'ArrowRight', 'Home'].includes(event.key)) { event.preventDefault();if (event.key === 'Home') onSeekTour(1);else onStation(event.key === 'ArrowRight' ? 1 : -1);return }
        if (event.key.toLowerCase() === 'r') { navigation.yaw = limits.initialYaw;navigation.pitch = limits.initialPitch;invalidate() }
        return
      }
      const key = event.key.length === 1 ? event.key.toLowerCase() : event.key
      if (roomState.view!=='main') return
      if (['w', 's', 'ArrowUp', 'ArrowDown', 'Shift'].includes(key)) { event.preventDefault();keys.add(key);updateKeys() }
    }
    const keyup = (event: KeyboardEvent) => { keys.delete(event.key.length === 1 ? event.key.toLowerCase() : event.key);updateKeys() }
    const blur = () => { keys.clear();touches.clear();drag = null;updateKeys() }
    const down = (event: PointerEvent) => {
      if (event.button !== 0) return
      if (event.pointerType === 'touch') { touches.add(event.pointerId);if (touches.size > 1) { drag = null;return } }
      canvas.focus({ preventScroll: true });navigationRef.current.dragDistance = 0
      if (event.pointerType === 'touch' || assets.manifest.navigation && roomState.view === 'main') {
        drag = { x: event.clientX, y: event.clientY, startX: event.clientX, startY: event.clientY, touch: event.pointerType === 'touch', mode: event.pointerType === 'touch' ? null : 'look' }
        canvas.setPointerCapture(event.pointerId)
      }
    }
    const move = (event: PointerEvent) => {
      if (!drag) return
      if (drag.touch && !drag.mode) {
        const totalX = event.clientX - drag.startX, totalY = event.clientY - drag.startY
        if (Math.max(Math.abs(totalX), Math.abs(totalY)) < 12) return
        drag.mode = Math.abs(totalY) > Math.abs(totalX) * 1.25 ? 'scroll' : 'look'
      }
      const dx = event.clientX - drag.x, dy = event.clientY - drag.y
      const nav = navigationRef.current
      nav.dragDistance += Math.abs(dx) + Math.abs(dy)
      if (drag.mode === 'scroll') { scroll(-dy);if (!drag) return }
      else if (assets.manifest.navigation && roomState.view === 'main') { nav.yaw -= dx * (lookOnly && drag.touch ? .005 : .003);nav.pitch = MathUtils.clamp(nav.pitch + dy * .003, -Math.PI * .47, Math.PI * .47);invalidate() }
      drag.x = event.clientX;drag.y = event.clientY
    }
    const up = (event: PointerEvent) => { touches.delete(event.pointerId);drag = null }
    const wheel = (event: WheelEvent) => {
      if (event.ctrlKey || event.metaKey || Math.abs(event.deltaX) > Math.abs(event.deltaY)) return
      event.preventDefault()
      const unit = event.deltaMode === 1 ? 16 : event.deltaMode === 2 ? size.height : 1
      scroll(event.deltaY * unit)
    }
    window.addEventListener('keydown', keydown);window.addEventListener('keyup', keyup);window.addEventListener('blur', blur)
    canvas.addEventListener('pointerdown', down);canvas.addEventListener('pointermove', move);canvas.addEventListener('pointerup', up);canvas.addEventListener('pointercancel', up);canvas.addEventListener('wheel', wheel, { passive: false })
    return () => {
      keys.clear();touches.clear();navigation.forward = 0
      if (oldTabIndex == null) canvas.removeAttribute('tabindex');else canvas.setAttribute('tabindex', oldTabIndex)
      window.removeEventListener('keydown', keydown);window.removeEventListener('keyup', keyup);window.removeEventListener('blur', blur)
      canvas.removeEventListener('pointerdown', down);canvas.removeEventListener('pointermove', move);canvas.removeEventListener('pointerup', up);canvas.removeEventListener('pointercancel', up);canvas.removeEventListener('wheel', wheel)
    }
  }, [active, arrived, assets, gl, navigationRef, roomState.view, roomState.profileOpen, roomState.returnPrompt, roomState.openedCategories, guided, lookOnly, invalidate, onRequestReturn, onView, onToggleWalk, onSeekTour, onStation, size.height, playClick])

  useFrame((_, delta) => {
    if (!active) { portalAudio?.reset();return }
    const now = performance.now()
    const elapsed = Math.max(0, now - lastTick.current) / 1000
    const nav = navigationRef.current, limits = assets.manifest.navigation
    if (!isActiveNavigationState(nav) || !(camera instanceof PerspectiveCamera)) return
    nav.projectFocusSettled=false
    const live = limits && assets.manifest.frameEnd > 1 && !cardFocus && !reducedMotion && !roomState.paused && !roomState.profileOpen && !roomState.returnPrompt && !document.hidden && visible.current && (!animationBox || animationVisible.current && arrived && roomState.view === 'main') && (!limits.animationFollowsWalk || arrived && !roomState.walkPaused && roomState.view === 'main')
    if (live) { clock.current += elapsed;invalidate() }
    lastTick.current = now
    if (limits.type === 'guided' && arrived && live && !roomState.walkPaused && !nav.walkManual && roomState.view === 'main') {
      const route = limits.route, next = nav.walkFrame + elapsed * assets.manifest.fps
      nav.walkFrame = route.loop ? 1 + MathUtils.euclideanModulo(next-1, route.frameEnd) : Math.min(route.frameEnd, next)
      nav.walkTarget = nav.walkFrame;nav.walkSpring.value = nav.walkFrame;nav.walkSpring.velocity = 0
      if (!route.loop && nav.walkFrame === route.frameEnd && !nav.finished) { nav.finished = true;onTourEnd() }
    }
    if (limits.type === 'guided' && arrived && roomState.view === 'main' && !roomState.profileOpen && !roomState.returnPrompt && !document.hidden && visible.current && (nav.walkFrame !== nav.walkTarget || nav.walkSpring.velocity !== 0)) {
      const route = limits.route
      if (reducedMotion) { nav.walkFrame = nav.walkTarget;nav.walkSpring.value = nav.walkFrame;nav.walkSpring.velocity = 0 }
      else {
        nav.walkFrame = MathUtils.clamp(advanceCameraSpring(nav.walkSpring, nav.walkTarget, delta, 14), route.frameStart, route.frameEnd)
        if (nav.walkFrame !== nav.walkSpring.value) { nav.walkSpring.value = nav.walkFrame;nav.walkSpring.velocity = 0 }
        if (nav.walkFrame !== nav.walkTarget || nav.walkSpring.velocity !== 0) invalidate()
      }
    }
    roomFrameRef.current = 1 + (limits?.animationFollowsWalk ? nav.walkFrame - 1 : clock.current * assets.manifest.fps) % assets.manifest.frameEnd
    if (!arrived) { portalAudio?.reset();return }
    let fov = alignment.poses.main.fov
    if (limits && roomState.view === 'main') {
      if (isGuidedRoomAssets(assets)) {
        readRoomRoute(assets, nav.walkFrame, scratch.position)
        currentX.current = scratch.position.x;currentY.current = scratch.position.y
      } else if (limits.type === 'axis') {
        nav.y = clampHallwayY(limits, nav.y + nav.forward * (nav.fast ? limits.fastSpeed : limits.speed) * Math.min(delta, .1))
        if (nav.forward) invalidate()
        currentY.current = reducedMotion ? nav.y : MathUtils.damp(currentY.current, nav.y, 18, Math.min(delta, .1))
        scratch.position.set(0, currentY.current, limits.eyeHeight)
      } else {
        scratch.position.fromArray(assets.manifest.cameras.main.position)
        currentX.current = scratch.position.x;currentY.current = scratch.position.y
      }
      currentYaw.current = reducedMotion ? nav.yaw : MathUtils.damp(currentYaw.current, nav.yaw, 18, Math.min(delta, .1))
      currentPitch.current = reducedMotion ? nav.pitch : MathUtils.damp(currentPitch.current, nav.pitch, 18, Math.min(delta, .1))
      if ((!guided && Math.abs(currentY.current-nav.y) > .0001) || Math.abs(currentYaw.current-nav.yaw) + Math.abs(currentPitch.current-nav.pitch) > .0001) invalidate()
      nav.position = scratch.position.toArray()
      scratch.position.applyQuaternion(alignment.rotation).add(alignment.position)
      // Blender camera local -Z looks into +Y; local Y points up.
      const yaw = currentYaw.current, pitch = currentPitch.current
      scratch.horizontal.setFromAxisAngle(scratch.up, -yaw);scratch.tilt.setFromAxisAngle(scratch.right, Math.PI / 2 + pitch)
      scratch.quaternion.copy(alignment.rotation).multiply(scratch.horizontal).multiply(scratch.tilt)
      if (homeTransition.current && focus.current.position && focus.current.quaternion && focus.current.fov !== null) {
        const current = focus.current, t = reducedMotion ? 1 : 1 - Math.exp(-8 * Math.min(delta, .1))
        if (!current.position || !current.quaternion || current.fov === null) return
        current.position.lerp(scratch.position, t);current.quaternion.slerp(scratch.quaternion, t);current.fov = MathUtils.lerp(current.fov, fov, t)
        if (current.position.distanceTo(scratch.position) > .0001 || current.quaternion.angleTo(scratch.quaternion) > .0001 || Math.abs(current.fov - fov) > .001) invalidate()
        else homeTransition.current = false
        scratch.position.copy(current.position);scratch.quaternion.copy(current.quaternion);fov = current.fov
      }
    } else {
      const target = cardFocus || alignment.poses[roomState.view] || alignment.poses.main
      const current = focus.current
      if (!current.position || !current.quaternion || current.fov === null) return
      const t = reducedMotion ? 1 : 1 - Math.exp(-8 * Math.min(delta, .1))
      current.position.lerp(target.position, t);current.quaternion.slerp(target.quaternion, t);current.fov = MathUtils.lerp(current.fov, target.fov, t)
      const settled=current.position.distanceTo(target.position)<=.0001&&current.quaternion.angleTo(target.quaternion)<=.0001&&Math.abs(current.fov-target.fov)<=.001
      if (!settled) invalidate()
      else {current.position.copy(target.position);current.quaternion.copy(target.quaternion);current.fov=target.fov}
      nav.projectFocusSettled=Boolean(cardFocus)&&settled
      scratch.position.copy(current.position);scratch.quaternion.copy(current.quaternion);fov = current.fov
    }
    scratch.localPosition.copy(scratch.position).sub(alignment.position).applyQuaternion(inverseAlignment)
    nav.cameraPosition=scratch.localPosition.toArray()
    if (portalAudio) {
      const crossingActive = roomState.view === 'main' && !homeTransition.current && !nav.portalAudioSeeking &&
        !roomState.profileOpen && !roomState.returnPrompt && !document.hidden && visible.current
      for (const portal of portalAudio.update(nav.cameraPosition[1], crossingActive)) playPortal(portal.id)
      if (nav.portalAudioSeeking && Math.abs(currentY.current - nav.y) < .02) nav.portalAudioSeeking = false
    }
    camera.position.copy(scratch.position).applyQuaternion(BASIS);camera.quaternion.copy(BASIS).multiply(scratch.quaternion)
    const aspect = size.width / Math.max(1, size.height)
    const adjusted = Math.min(85, MathUtils.radToDeg(2 * Math.atan(Math.tan(MathUtils.degToRad(fov) / 2) * Math.max(1, 1.6 / aspect))))
    if (Math.abs(camera.fov-adjusted) > .001 || camera.near !== .01) { camera.fov = adjusted;camera.near = .01;camera.updateProjectionMatrix() }
    if(gl.domElement.dataset.roomFov!==String(camera.fov)) gl.domElement.dataset.roomFov=String(camera.fov)
    const targetX=cardFocus?.offsetX||0,targetY=cardFocus?.offsetY||0
    viewOffset.current.x=reducedMotion?targetX:MathUtils.damp(viewOffset.current.x,targetX,18,Math.min(delta,.1))
    viewOffset.current.y=reducedMotion?targetY:MathUtils.damp(viewOffset.current.y,targetY,18,Math.min(delta,.1))
    if (Math.abs(viewOffset.current.x-targetX)+Math.abs(viewOffset.current.y-targetY)<.01) { viewOffset.current.x=targetX;viewOffset.current.y=targetY } else invalidate()
    nav.projectFocusSettled &&= viewOffset.current.x===targetX&&viewOffset.current.y===targetY
    if (cardFocus || viewOffset.current.x || viewOffset.current.y) {
      if (!camera.view?.enabled || camera.view.fullWidth!==size.width || camera.view.fullHeight!==size.height || camera.view.offsetX!==viewOffset.current.x || camera.view.offsetY!==viewOffset.current.y) camera.setViewOffset(size.width,size.height,viewOffset.current.x,viewOffset.current.y,size.width,size.height)
    } else if (camera.view?.enabled) camera.clearViewOffset()
    camera.updateMatrixWorld()
    nav.projectCardFramed=Boolean(cardFocus)
    if (cardFocus) {
      for (const corner of cardFocus.corners) {
        scratch.corner.copy(corner).applyQuaternion(BASIS).project(camera)
        const x=(scratch.corner.x+1)*size.width/2,y=(1-scratch.corner.y)*size.height/2
        if (scratch.corner.z<-1||scratch.corner.z>1||x<cardFocus.rect.left-2||x>cardFocus.rect.right+2||y<cardFocus.rect.top-2||y>cardFocus.rect.bottom+2) nav.projectCardFramed=false
      }
    }
    onFrame(roomFrameRef.current,nav.cameraPosition[1],guided?nav.walkFrame:null,nav.cameraPosition[0])
    if (animationBox) {
      scratch.frustum.setFromProjectionMatrix(scratch.projection.multiplyMatrices(camera.projectionMatrix, camera.matrixWorldInverse))
      const next = scratch.frustum.intersectsBox(animationBox)
      if (next !== animationVisible.current) { animationVisible.current = next;invalidate() }
    }
  }, -.5)
  return null
}
