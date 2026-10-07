import { Component, useCallback, useEffect, useLayoutEffect, useRef, useState } from 'react'
import { Canvas } from '@react-three/fiber'
import { NoToneMapping } from 'three'
import { portfolio } from '../data/portfolio.js'
import CityScene from './city/CityScene.jsx'
import NegativeCursor from './city/NegativeCursor.jsx'
import { CITY_ASSET_BASE, loadCityAssets, loadElevatorAssets, loadJourneyConfig, loadLobbyAssets, loadRoomAssets } from './city/cityAssets.js'
import ElevatorControls from './city/ElevatorControls.jsx'
import RoomControls from './city/RoomControls.jsx'
import RoomProgressBar from './city/RoomProgressBar.jsx'
import { getRoomProgress, updateRoomProgress } from './city/roomProgress.js'
import ObserverProfile from './city/ObserverProfile.jsx'
import RoomReturnDialog from './city/RoomReturnDialog.jsx'
import { isRoomAtEntrance } from './city/roomJourney.js'
import { useReducedMotion, useScrollTimeline } from './city/useScrollTimeline.js'
import './city/city.css'
import useSoundEffects from '../audio/useSoundEffects.js'
import { clampHallwayY, hallwayCategoryAt } from './city/hallwayCategories.js'
import HallwayCategoryLabel from './city/HallwayCategoryLabel.jsx'
import GuideOverlay from './city/GuideOverlay.jsx'
import ToplineControl from './city/ToplineControl.jsx'
import { createDoorSoundTiming } from './city/doorSoundTiming.js'

class CityErrorBoundary extends Component {
  state = { error: null }
  static getDerivedStateFromError(error) { return { error } }
  componentDidCatch(error) { console.error('City viewer failed:', error) }
  render() {
    if (this.state.error) return <div className="city-error" role="alert"><p>The interactive view couldn’t start.</p><p>{this.state.error.message}</p><button onClick={() => window.location.reload()}>Reload viewer</button></div>
    return this.props.children
  }
}

const phases = [
  { end: 'lookDown', label: '01 / LOOK UP, THEN DOWN', title: 'A world built from points.', description: 'Scroll to look from the rooftop down to the street. The camera stays still.' },
  { end: 'doors', label: '02 / STREET APPROACH', title: 'Follow the city.', description: 'Keep scrolling toward the entrance. Pedestrians walk as the train and hover cars pass.' },
  { end: 'entrance', label: '03 / AT THE ENTRANCE', title: 'A door into what’s next.', description: 'The doors open as you approach. Scroll back to reverse the journey.' },
  { end: 'lobby', label: '04 / ENTER THE ATRIUM', title: 'Welcome to KAJU.', description: 'The city gives way to the grand lobby. Keep scrolling to explore inside.' },
  { end: 'reception', label: '05 / RECEPTION', title: 'A brighter humanity.', description: 'Follow the carpet into the atrium and pass the reception island.' },
  { end: 'escalator', label: '06 / THROUGH THE ATRIUM', title: 'Another level awaits.', description: 'Continue around reception toward the right escalator.' },
  { end: 'landing', label: '07 / UPWARD', title: 'Take the elevated view.', description: 'Scroll to ride the escalator into the upper foyer.' },
  { end: 'elevator', label: '08 / UPPER FOYER', title: 'Find the next doorway.', description: 'Approach elevator R1. The camera stops safely before its threshold.' },
  { end: 'elevatorOpen', label: '09 / ELEVATOR HANDOFF', title: 'The journey continues.', description: 'Scroll to open the elevator doors and step into the cabin.' },
  { end: 'cabin', label: '10 / ENTER THE CABIN', title: 'Your next chapter.', description: 'Choose a floor to explore About Me, Skills, Projects, or Experience & Education.' },
]

const initialRoomState = () => ({ view: 'main', project: null, projectExploring:false, projectSection:'Overview', projectFocusReady:false, exhibit: null, paused: false, walkPaused: true, profileOpen: false, returnPrompt: false, openedCategories: ['client'] })

export default function CityWalkthrough({ title }) {
  const { environmentClick: playClick, click: playSystemClick, doorSound, cancelDoorSounds, preferencesOpen, openPreferences, closePreferences } = useSoundEffects()
  const sectionRef = useRef(null)
  const stageRef = useRef(null)
  const roomProgressRef = useRef(null)
  const categoryLabelRef = useRef(null)
  const doorTiming = useRef(createDoorSoundTiming())
  const playDoorEvents = useCallback(events => { for (const event of events) doorSound(event.id, event.delay) }, [doorSound])
  const reducedMotion = useReducedMotion()
  const [load, setLoad] = useState({ assets: null, journey: null, error: null })
  const [lobby, setLobby] = useState({ assets: null, error: null })
  const [cabin, setCabin] = useState({ assets: null, error: null })
  const [elevatorState, setElevatorState] = useState({ level: null, status: 'idle', frame: 180, run: 0 })
  const [focusedLevel, setFocusedLevel] = useState(null)
  const [pressedLevel, setPressedLevel] = useState(null)
  const [retry, setRetry] = useState(0)
  const [cabinRetry, setCabinRetry] = useState(0)
  const [rooms, setRooms] = useState({})
  const [roomRetry, setRoomRetry] = useState(0)
  const [roomState, setRoomState] = useState(initialRoomState)
  const [guideOpen, setGuideOpen] = useState(false)
  const navigationRef = useRef({ y: 0, yaw: 0, pitch: .02, forward: 0, fast: false, dragDistance: 0, invalidate: null })
  const beforeReturn = useRef(null)
  const latestRoomState = useRef(roomState)
  const skillReturnState = useRef(null)
  const roomId = elevatorState.level
  const roomConfig = load.journey?.rooms?.[roomId]
  const roomAssets = rooms[roomId]?.assets || null
  const focusedProject = roomId==='projects' && roomState.view==='project' ? roomAssets?.manifest.projects.find(project=>project.id===roomState.project) : null
  const focusedTimeline = roomId==='experience' && roomState.view==='timeline' ? roomAssets?.manifest.exhibits.find(entry=>entry.id===roomState.exhibit) : null
  const focusedSkill = roomId==='skills' && roomState.view==='skill' ? roomAssets?.manifest.exhibits.find(entry=>entry.id===roomState.exhibit) : null
  const focusedDirectory=roomId==='projects'&&roomState.view==='directory'?roomAssets?.manifest.directory:null
  const roomError = rooms[roomId]?.error
  const elevatorEntryProgress = ((load.journey?.lobbyGlobalEnd ?? 1403) - 1) / Math.max(1, (load.journey?.frameEnd ?? 1521) - 1)
  const interfaceOpen = guideOpen || preferencesOpen
  const { progress, seek } = useScrollTimeline(sectionRef, elevatorState.status === 'idle' && !interfaceOpen, elevatorEntryProgress)
  const sceneRoomState = interfaceOpen ? { ...roomState, paused: true, walkPaused: true, profileOpen: true } : roomState
  const closeGuide = useCallback(() => setGuideOpen(false), [])
  const openGuide = () => {
    closePreferences()
    navigationRef.current.forward = 0
    navigationRef.current.fast = false
    setGuideOpen(true)
  }
  const openSoundPreferences = () => {
    navigationRef.current.forward = 0
    navigationRef.current.fast = false
    setGuideOpen(false)
    openPreferences()
  }
  const firstFrame = 1
  const lastFrame = load.journey?.frameEnd ?? 1521
  const bookmarks = load.journey?.bookmarks ?? { start: 1, lookDown: 90, doors: 245, train: 145, entrance: 383, lobby: 443, reception: 703, escalator: 893, landing: 1073, elevator: 1223, elevatorOpen: 1403, cabin: 1521 }
  const frame = Math.round(firstFrame + progress * (lastFrame - firstFrame))

  useLayoutEffect(() => { latestRoomState.current = roomState }, [roomState])
  const phase = phases.find((item) => frame <= bookmarks[item.end]) || phases[phases.length - 1]

  useEffect(() => {
    const controller = new AbortController()
    Promise.all([loadCityAssets(controller.signal), loadJourneyConfig(controller.signal)])
      .then(([assets, journey]) => { if (!controller.signal.aborted) setLoad({ assets, journey, error: null }) })
      .catch((error) => { if (!controller.signal.aborted) setLoad({ assets: null, journey: null, error }) })
    return () => controller.abort()
  }, [])
  const preloadLobby = Boolean(load.assets) && frame >= (load.journey?.preloadFrame ?? 100)
  useEffect(() => {
    if (!preloadLobby || lobby.assets) return
    const controller = new AbortController()
    loadLobbyAssets(controller.signal)
      .then((assets) => { if (!controller.signal.aborted) setLobby({ assets, error: null }) })
      .catch((error) => { if (!controller.signal.aborted) setLobby({ assets: null, error }) })
    return () => controller.abort()
  }, [preloadLobby, lobby.assets, retry])
  const preloadCabin = Boolean(load.assets) && frame >= (load.journey?.elevatorPreloadFrame ?? 893)
  useEffect(() => {
    if (!preloadCabin || cabin.assets) return
    const controller = new AbortController()
    loadElevatorAssets(controller.signal)
      .then((assets) => { if (!controller.signal.aborted) setCabin({ assets, error: null }) })
      .catch((error) => { if (!controller.signal.aborted) setCabin({ assets: null, error }) })
    return () => controller.abort()
  }, [preloadCabin, cabin.assets, cabinRetry])
  useEffect(() => {
    if (!roomConfig || roomAssets) return
    const controller = new AbortController()
    loadRoomAssets(roomConfig, controller.signal)
      .then((assets) => { if (!controller.signal.aborted) setRooms((current) => ({ ...current, [roomId]: { assets, error: null } })) })
      .catch((error) => { if (!controller.signal.aborted) setRooms((current) => ({ ...current, [roomId]: { assets: null, error } })) })
    return () => controller.abort()
  }, [roomId, roomConfig, roomAssets, roomRetry])
  const reportFrame = useCallback((value) => {
    if (load.journey) playDoorEvents(doorTiming.current.journey(value, load.journey))
    if (stageRef.current) {
      stageRef.current.dataset.renderedFrame = String(Math.round(value))
      stageRef.current.dataset.zone = stageRef.current.dataset.room ? `room-${stageRef.current.dataset.room}` : value > (load.journey?.lobbyGlobalEnd ?? 1403) ? 'elevator' : value > (load.journey?.cityEnd ?? 383) ? 'lobby' : 'city'
    }
  }, [load.journey, playDoorEvents])
  const seekFrame = (value) => seek((value - firstFrame) / Math.max(1, lastFrame - firstFrame))
  const selectLevel = useCallback((level) => {
    if (!load.journey?.rooms?.[level]) return
    cancelDoorSounds();doorTiming.current.resetDeparture()
    setFocusedLevel(null);setPressedLevel(null)
    setRoomState(initialRoomState())
    setElevatorState((current) => ({ level, status: 'departing', frame: 181, run: current.run + 1 }))
    document.body.style.cursor = ''
  }, [load.journey, cancelDoorSounds])
  const replaySelection = useCallback((cancelAudio = true) => {
    if (cancelAudio) cancelDoorSounds()
    setFocusedLevel(null);setPressedLevel(null)
    navigationRef.current.forward = 0
    navigationRef.current.returnRequested = false
    beforeReturn.current = null
    if (stageRef.current) stageRef.current.dataset.returnPhase = ''
    setRoomState(initialRoomState())
    setElevatorState((current) => ({ level: null, status: 'idle', frame: 180, run: current.run + 1 }))
  }, [cancelDoorSounds])
  const reportElevatorFrame = useCallback((value) => {
    playDoorEvents(doorTiming.current.departure(value, cabin.assets?.manifest.flow.doorsOpen[0] ?? 300))
    if (stageRef.current) stageRef.current.dataset.elevatorFrame = String(Math.floor(value))
    setElevatorState((current) => current.status === 'departing' ? { ...current, frame: Math.floor(value) } : current)
  }, [cabin.assets, playDoorEvents])
  const arrive = useCallback(() => setElevatorState((current) => ({ ...current, status: 'arrived', frame: 510 })), [])
  const reportRoomFrame = useCallback((value, y, walkFrame, x = 0) => {
    const walkingProgress = getRoomProgress(roomAssets?.manifest.navigation, y, walkFrame)
    let progressLabel = roomAssets?.manifest.label
    if (stageRef.current) {
      stageRef.current.dataset.roomFrame = String(Math.floor(value));stageRef.current.dataset.roomY = y.toFixed(3);stageRef.current.dataset.roomX = x.toFixed(3)
      stageRef.current.dataset.roomAtEntrance = String(isRoomAtEntrance(roomAssets, navigationRef.current, roomState.view))
      stageRef.current.dataset.cardFocusFramed = String(Boolean(navigationRef.current.projectCardFramed))
      stageRef.current.dataset.cardFocusSettled = String(Boolean(navigationRef.current.projectFocusSettled))
      const category = hallwayCategoryAt(roomAssets?.manifest.navigation, y)
      if (category) {
        stageRef.current.dataset.projectCategory = category.id
        const status = document.getElementById('hallway-category-status')
        const title = `${String(category.number).padStart(2,'0')} / ${category.title}`
        if (status && status.textContent !== title) status.textContent = title
        if (categoryLabelRef.current && categoryLabelRef.current.textContent !== title) {
          categoryLabelRef.current.textContent = title
          categoryLabelRef.current.dataset.category = category.id
        }
        const visited = roomAssets.manifest.navigation.categories.filter(section => section.startY <= y).map(section => section.id)
        if (visited.some(id => !latestRoomState.current.openedCategories.includes(id))) {
          setRoomState(current => visited.every(id => current.openedCategories.includes(id)) ? current : ({ ...current, openedCategories: [...new Set([...current.openedCategories,...visited])] }))
        }
      }
    }
    if (walkFrame != null) {
      if (stageRef.current) stageRef.current.dataset.roomWalkFrame = String(Math.floor(walkFrame))
      if (stageRef.current) stageRef.current.dataset.roomWalkTarget = String(navigationRef.current.walkTarget)
      if (stageRef.current) stageRef.current.dataset.roomScrollSettled = String(walkFrame === navigationRef.current.walkTarget && navigationRef.current.walkSpring?.velocity === 0)
      const route = roomAssets.manifest.navigation.route
      const station = roomAssets.manifest.exhibits.find(item => walkFrame >= item.start && walkFrame <= item.end)
      const label = station ? `${station.title} · ${station.hint}` : !route.loop && walkFrame >= route.frameEnd ? 'Tour complete' : walkFrame < 2 ? 'Entrance' : 'Travelling to the next exhibit'
      progressLabel = label
      const status = document.getElementById('room-tour-status')
      if (status) { status.textContent = station?.title || label;status.title = label }
    } else if (walkingProgress) {
      const project = roomAssets.manifest.projects?.find(item => Math.abs(item.position[1] - y) < 3)
      progressLabel = y <= walkingProgress.min + .1 ? 'Entrance' : y >= walkingProgress.max - .1 ? 'End of hallway' : project?.title || 'Walking through the project hallway'
    }
    updateRoomProgress(roomProgressRef.current, walkingProgress, progressLabel)
    if (roomState.view==='project' && navigationRef.current.projectCardFramed && !latestRoomState.current.projectFocusReady) setRoomState(current=>current.projectFocusReady?current:({...current,projectFocusReady:true}))
  }, [roomAssets, roomState.view])
  const changeRoomView = useCallback((view) => {
    navigationRef.current.forward=0
    const previous=skillReturnState.current
    setRoomState(current=>({...current,view,projectExploring:false,walkPaused:view==='main'&&current.view==='skill'?(previous?.walkPaused??true):view==='main'?current.walkPaused:true}))
    if (view==='main') skillReturnState.current=null
    navigationRef.current.invalidate?.();document.body.style.cursor=''
  }, [])
  const selectProjectSection = useCallback(heading=>setRoomState(current=>({...current,projectSection:heading})),[])
  const openSkillCard = useCallback(id=>{
    const entry=roomAssets?.manifest.exhibits.find(entry=>entry.id===id&&entry.kind==='skill')
    if (!entry) return
    if (latestRoomState.current.view!=='skill') skillReturnState.current={walkPaused:latestRoomState.current.walkPaused}
    navigationRef.current.forward=0;navigationRef.current.fast=false
    setRoomState(current=>({...current,exhibit:id,view:'skill',walkPaused:true,projectExploring:true,projectSection:'Overview',projectFocusReady:false}))
    navigationRef.current.invalidate?.();document.body.style.cursor=''
  },[roomAssets])
  const openTimelineEntry = useCallback(id=>{
    if (!roomAssets?.manifest.exhibits.some(entry=>entry.id===id)) return
    navigationRef.current.forward=0
    setRoomState(current=>({...current,exhibit:id,view:'timeline',projectExploring:true,projectSection:'Overview'}))
    navigationRef.current.invalidate?.();document.body.style.cursor=''
  },[roomAssets])
  useEffect(()=>{
    if (!(['projects','experience','skills'].includes(roomId)&&['project','timeline','skill','directory'].includes(roomState.view))||interfaceOpen) return
    const escape=event=>{
      if (event.key!=='Escape'||event.repeat||event.defaultPrevented) return
      event.preventDefault();playSystemClick();changeRoomView('main')
    }
    window.addEventListener('keydown',escape)
    return ()=>window.removeEventListener('keydown',escape)
  },[roomId,roomState.view,interfaceOpen,changeRoomView,playSystemClick])
  const openObserverProfile = useCallback(() => { setRoomState(current => ({ ...current, profileOpen: true }));document.body.style.cursor = '' }, [])
  const closeObserverProfile = useCallback(() => setRoomState(current => ({ ...current, profileOpen: false })), [])
  const interactWithRoom = useCallback((id, source = 'scene') => {
    if (source === 'scene' && navigationRef.current.dragDistance > 5) return
    if (roomId === 'projects' && id!=='directory' && !roomAssets?.manifest.projects.some(project => project.id === id && latestRoomState.current.openedCategories.includes(project.section))) return
    if (source === 'scene') playClick()
    if (roomId === 'about' && id === 'card') changeRoomView('card')
    else if (roomId === 'about' && latestRoomState.current.view === 'card' && id.startsWith('contact-')) {
      const link = portfolio.contact.links.find(link => link.id === id.slice('contact-'.length))
      if (link && /^https:\/\//.test(link.href)) window.open(link.href, '_blank', 'noopener,noreferrer')
    }
    else if (roomId === 'about' && id === 'observer') openObserverProfile()
    else if (roomId==='projects'&&id==='directory'&&roomAssets?.manifest.directory) {
      navigationRef.current.forward=0;navigationRef.current.fast=false
      setRoomState(current=>({...current,view:'directory',projectExploring:false}))
      navigationRef.current.invalidate?.();document.body.style.cursor=''
    }
    else if (roomId === 'projects') {
      const project = roomAssets?.manifest.projects.find(project => project.id === id)
      if (project && latestRoomState.current.openedCategories.includes(project.section)) {
        navigationRef.current.forward=0
        setRoomState(current=>({...current,project:id,view:'project',projectExploring:true,projectSection:'Overview',projectFocusReady:false}))
        navigationRef.current.invalidate?.()
        document.body.style.cursor=''
      }
    }
    else if (roomId==='experience') openTimelineEntry(id)
    else if (roomId==='skills') {
      if (roomAssets?.manifest.exhibits.some(entry=>entry.id===id&&entry.kind==='skill')) openSkillCard(id)
      else setRoomState(current=>({...current,exhibit:id}))
    }
  }, [roomId, roomAssets, changeRoomView, openObserverProfile, openTimelineEntry, openSkillCard, playClick])
  const jumpToProject = (id, jump) => {
    const project = roomAssets?.manifest.projects.find((item) => item.id === id)
    if (project && !roomState.openedCategories.includes(project.section)) return
    setRoomState(current=>({...current,project:id||null,...(project?{view:'project',projectExploring:true,projectSection:'Overview',projectFocusReady:false}:{})}))
    if (project && jump) {
      const nav = navigationRef.current
      nav.forward=0;nav.fast=false;nav.invalidate?.()
    }
  }
  const moveInRoom = (direction) => { navigationRef.current.forward = direction;navigationRef.current.invalidate?.() }
  const lookInRoom = (amount) => { navigationRef.current.yaw += amount;navigationRef.current.invalidate?.() }
  const seekRoomTour = useCallback((frame, smooth = false) => {
    const route = roomAssets?.manifest.navigation?.route
    if (!route) return
    const nav = navigationRef.current
    nav.walkTarget = Math.max(route.frameStart, Math.min(route.frameEnd, frame));nav.finished = false;nav.forward = 0
    nav.walkManual = true
    if (!smooth || reducedMotion) {
      nav.walkFrame = nav.walkTarget
      if (nav.walkSpring) { nav.walkSpring.value = nav.walkFrame;nav.walkSpring.velocity = 0 }
    }
    setRoomState(current => ({ ...current, view: 'main', walkPaused: true }));nav.invalidate?.()
  }, [roomAssets, reducedMotion])
  const seekRoomProgress = useCallback((value) => {
    const limits = roomAssets?.manifest.navigation
    if (limits?.type === 'guided') { seekRoomTour(value);return }
    if (limits?.type !== 'axis') return
    const nav = navigationRef.current
    nav.y = clampHallwayY(limits, value);nav.forward = 0;nav.portalAudioSeeking = true
    setRoomState(current => ({ ...current, view: 'main' }));nav.invalidate?.()
  }, [roomAssets, seekRoomTour])
  const toggleRoomWalk = useCallback(() => {
    const route = roomAssets?.manifest.navigation?.route, nav = navigationRef.current
    if (!route) return
    if (!route.loop && nav.walkFrame >= route.frameEnd) nav.walkFrame = 1
    nav.walkTarget = nav.walkFrame
    nav.walkManual = false
    if (nav.walkSpring) { nav.walkSpring.value = nav.walkFrame;nav.walkSpring.velocity = 0 }
    nav.finished = false
    setRoomState(current => ({ ...current, view: 'main', walkPaused: !current.walkPaused }));nav.invalidate?.()
  }, [roomAssets])
  const selectRoomExhibit = (id, visit) => {
    if (roomId==='experience') { openTimelineEntry(id);return }
    if (roomId==='skills'&&roomAssets?.manifest.exhibits.some(entry=>entry.id===id&&entry.kind==='skill')) {openSkillCard(id);return}
    setRoomState(current => ({ ...current, exhibit: id || null }))
    const exhibit = roomAssets?.manifest.exhibits.find(item => item.id === id)
    if (visit && exhibit) seekRoomTour(exhibit.start)
  }
  const stepRoomStation = useCallback((direction) => {
    const stations = roomAssets?.manifest.navigation?.stations
    if (!stations?.length) return
    const frame = navigationRef.current.walkFrame
    const station = direction > 0 ? stations.find(item => item.start > frame + 1) || stations[0] : [...stations].reverse().find(item => item.start < frame - 1) || stations.at(-1)
    setRoomState(current => ({ ...current, exhibit: station.id }));seekRoomTour(station.start)
  }, [roomAssets, seekRoomTour])
  const finishRoomTour = useCallback(() => setRoomState(current => ({ ...current, walkPaused: true })), [])
  const resetRoomLook = () => {
    const nav = navigationRef.current, limits = roomAssets?.manifest.navigation
    const yaw = limits?.initialYaw || 0
    nav.yaw = limits?.type === 'look' ? nav.yaw + Math.atan2(Math.sin(yaw - nav.yaw), Math.cos(yaw - nav.yaw)) : yaw
    nav.pitch = limits?.initialPitch ?? .02;nav.invalidate?.()
  }
  const lookAtRoomExhibit = () => {
    const exhibit = roomAssets?.manifest.exhibits.find(item => item.id === roomState.exhibit)
    if (!exhibit) return
    const nav = navigationRef.current, [x,y,z] = nav.position
    const dx = exhibit.position[0]-x, dy = exhibit.position[1]-y, angle = Math.atan2(dx,dy)
    nav.yaw += Math.atan2(Math.sin(angle-nav.yaw),Math.cos(angle-nav.yaw));nav.pitch = Math.atan2(exhibit.position[2]-z,Math.hypot(dx,dy));nav.invalidate?.();changeRoomView('main')
  }
  const requestRoomReturn = useCallback(() => {
    const current = latestRoomState.current
    if (elevatorState.status !== 'arrived' || current.profileOpen || current.returnPrompt) return
    beforeReturn.current = { paused: current.paused, walkPaused: current.walkPaused }
    navigationRef.current.forward = 0
    setRoomState(current => ({ ...current, paused: true, walkPaused: true, returnPrompt: true }))
    document.body.style.cursor = ''
  }, [elevatorState.status])
  const cancelRoomReturn = useCallback(() => {
    navigationRef.current.returnRequested = false
    navigationRef.current.returnCooldown = performance.now() + 900
    const previous = beforeReturn.current
    setRoomState(current => ({ ...current, ...previous, returnPrompt: false }))
    beforeReturn.current = null
    navigationRef.current.invalidate?.()
  }, [])
  const confirmRoomReturn = useCallback(() => {
    doorTiming.current.resetReturn()
    navigationRef.current.forward = 0
    setRoomState(current => ({ ...current, returnPrompt: false, paused: true, walkPaused: true }))
    setElevatorState(current => ({ ...current, status: 'returning', frame: 510, run: current.run + 1 }))
    beforeReturn.current = null
  }, [])
  const enterElevator = useCallback(() => {
    const current = latestRoomState.current
    if (elevatorState.status !== 'arrived' || current.profileOpen || current.returnPrompt || current.view !== 'main') return
    confirmRoomReturn()
  }, [elevatorState.status, confirmRoomReturn])
  const reportRoomReturn = useCallback((value, phase) => {
    playDoorEvents(doorTiming.current.returning(value, reducedMotion, cabin.assets?.manifest.flow.doorsOpen[1] ?? 350))
    if (stageRef.current) { stageRef.current.dataset.elevatorFrame = String(Math.floor(value));stageRef.current.dataset.returnPhase = phase }
    const status = document.getElementById('room-return-status')
    const labels = { turning: 'Turning toward the elevator…', walking: 'Walking back to the elevator…', entering: 'Entering the cabin…', panel: 'Returning to the floor panel…' }
    if (status && status.textContent !== labels[phase]) status.textContent = labels[phase]
  }, [reducedMotion, cabin.assets, playDoorEvents])
  const finishRoomReturn = useCallback(() => {
    replaySelection(false)
    playDoorEvents(doorTiming.current.completeReturn())
  }, [replaySelection, playDoorEvents])
  const chooseReady = Boolean(cabin.assets) && frame >= lastFrame - 1
  const inRoom = ['arrived', 'returning'].includes(elevatorState.status) && Boolean(roomAssets)

  return (
    <section className="city-story" ref={sectionRef} id="city" aria-label="Interactive portfolio walkthrough" tabIndex={0}>
      <div className="city-stage" ref={stageRef} data-frame={frame} data-rendered-frame="1" data-loaded={Boolean(load.assets)} data-lobby-loaded={Boolean(lobby.assets)} data-elevator-loaded={Boolean(cabin.assets)} data-interactive={chooseReady && ['idle', 'arrived'].includes(elevatorState.status) && !roomState.returnPrompt && !interfaceOpen} data-elevator-status={elevatorState.status} data-room={inRoom ? roomId : ''} data-room-loaded={Boolean(roomAssets)} data-room-view={roomState.view} data-profile-open={roomState.profileOpen} data-return-prompt={roomState.returnPrompt} data-guide-open={guideOpen} data-preferences-open={preferencesOpen} data-project-exploring={roomState.projectExploring} data-focus-project={roomState.view==='project'?roomState.project:''} data-focus-skill={roomState.view==='skill'?roomState.exhibit:''}>
        {load.assets ? (
          <CityErrorBoundary>
            <Canvas
              className="city-canvas"
              aria-label={focusedDirectory ? 'Projects directory. Zoom-only view of the raised board and overhead projector. Back to hallway or Escape returns to your saved walking view.' : focusedSkill ? `Skill card: ${focusedSkill.title}. ${focusedSkill.summary}. Scroll or use arrow keys to explore toolkit, project evidence and learning scope. Escape returns to the gallery.` : focusedTimeline ? `Timeline entry: ${focusedTimeline.title}. ${focusedTimeline.summary}. Scroll or use arrow keys to change sections. Escape returns to the observatory.` : focusedProject ? `Full project card: ${focusedProject.title.replaceAll('\n',' ')}. ${focusedProject.summary.replaceAll('\n',' ')}. Scroll or use arrow keys to change sections. Escape returns to the hallway.` : inRoom && roomConfig ? `${roomConfig.label}. ${roomId === 'projects' ? 'Use W/S or arrow keys to walk, drag to look, or use the room controls.' : roomId === 'about' ? `Drag to turn around. Arrow keys look; R resets to the computer. Click ${portfolio.name} or use Meet ${portfolio.name} to read the profile. Click the desk card for contact details.` : 'Drag to look freely. Use the guided-tour and exhibit controls to navigate.'} Scroll up past the entrance to return to the elevator. Keyboard: Home, then Page Up. On touch screens swipe down to move back.` : 'Monochrome city, lobby, and elevator journey controlled by scrolling or the timeline below'}
              frameloop="demand"
              dpr={[1, 1.5]}
              camera={{ position: [12, 1.7, 35], fov: 50, near: 0.05, far: 250 }}
              onCreated={({ raycaster, gl }) => { raycaster.params.Points.threshold = .12;gl.localClippingEnabled = true }}
              gl={{ antialias: true, alpha: false, toneMapping: NoToneMapping, powerPreference: 'high-performance' }}
              fallback={<span>WebGL is unavailable. Reload this page in a browser with 3D graphics support.</span>}
            >
               <CityScene assets={load.assets} lobbyAssets={lobby.assets} elevatorAssets={cabin.assets} elevatorState={elevatorState} focusedLevel={focusedLevel} pressedLevel={pressedLevel} roomAssets={roomAssets} roomState={sceneRoomState} navigationRef={navigationRef} journey={load.journey} progress={progress} reducedMotion={reducedMotion} onFrame={reportFrame} onSelectLevel={selectLevel} onElevatorFrame={reportElevatorFrame} onRoomFrame={reportRoomFrame} onRoomInteract={interactWithRoom} onRoomView={changeRoomView} onToggleWalk={toggleRoomWalk} onSeekTour={seekRoomTour} onStation={stepRoomStation} onTourEnd={finishRoomTour} onRequestReturn={requestRoomReturn} onEnterElevator={enterElevator} onReturnProgress={reportRoomReturn} onReturnComplete={finishRoomReturn} onArrival={arrive} onCancel={replaySelection} />
            </Canvas>
          </CityErrorBoundary>
        ) : (
          <>
            <img className="city-poster" src={`${CITY_ASSET_BASE}preview.png`} alt="Monochrome particle city with an elevated train and a crowd of tall figures" />
            <p className="city-loading" role={load.error ? 'alert' : 'status'}>{load.error ? load.error.message : 'Loading the city…'}</p>
          </>
        )}
        {preloadLobby && !lobby.assets && frame >= (load.journey?.lobbyHoldFrame ?? bookmarks.doors) && <div className="city-chapter-loading" role={lobby.error ? 'alert' : 'status'}>
          <p>{lobby.error ? 'The lobby could not load. Your city view is preserved.' : 'Preparing the atrium…'}</p>
          {lobby.error && <button type="button" onClick={() => { setLobby({ assets: null, error: null }); setRetry((value) => value + 1) }}>Retry lobby</button>}
        </div>}
        {preloadCabin && !cabin.assets && frame >= (load.journey?.elevatorHoldFrame ?? 1283) && <div className="city-chapter-loading" role={cabin.error ? 'alert' : 'status'}>
          <p>{cabin.error ? 'The elevator could not load. Its doors will stay closed.' : 'Preparing the elevator cabin…'}</p>
          {cabin.error && <button type="button" onClick={() => { setCabin({ assets: null, error: null }); setCabinRetry((value) => value + 1) }}>Retry elevator</button>}
        </div>}
        {roomConfig && !roomAssets && elevatorState.status === 'departing' && <div className="city-chapter-loading" role={roomError ? 'alert' : 'status'}>
          <p>{roomError ? `The ${roomConfig.label.toLowerCase()} could not load. The doors will stay closed.` : `Preparing the ${roomConfig.label.toLowerCase()}…`}</p>
          {roomError && <button type="button" onClick={() => { setRooms((current) => ({ ...current, [roomId]: { assets: null, error: null } }));setRoomRetry((value) => value + 1) }}>Retry room</button>}
        </div>}
         <div className="city-topline"><span>{title}</span><div className="city-topline-actions">
           <ToplineControl className="portfolio-preferences" label="Open sound preferences" tooltip="Sound preferences" aria-haspopup="dialog" aria-controls="audio-consent-dialog" aria-expanded={preferencesOpen} onClick={openSoundPreferences}>
             <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1" aria-hidden="true">
               <path d="M3 6h5m4 0h9M3 12h11m4 0h3M3 18h3m4 0h11" /><circle cx="10" cy="6" r="2" /><circle cx="16" cy="12" r="2" /><circle cx="8" cy="18" r="2" />
             </svg>
           </ToplineControl>
           <ToplineControl className="portfolio-help" label="Open navigation guide" tooltip="Navigation guide" aria-haspopup="dialog" aria-controls="portfolio-guide" aria-expanded={guideOpen} onClick={openGuide}>
             <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1" aria-hidden="true">
               <circle cx="12" cy="12" r="9" /><path d="M9.4 9a2.7 2.7 0 0 1 5.2 1c0 1.8-2.6 2-2.6 3.8" /><circle cx="12" cy="17" r=".6" fill="currentColor" stroke="none" />
             </svg>
           </ToplineControl>
           {!inRoom && <ToplineControl className="city-floor-shortcut" label="Choose a floor" tooltip="Choose a floor" onClick={() => { replaySelection();seekFrame(bookmarks.cabin) }}><span className="floor-shortcut-label">Choose a floor </span><span aria-hidden="true">↗</span></ToplineControl>}
         </div></div>
        {roomId === 'projects' && elevatorState.status === 'arrived' && roomAssets && !roomState.returnPrompt && <HallwayCategoryLabel navigation={roomAssets.manifest.navigation} navigationRef={navigationRef} labelRef={categoryLabelRef} />}
        {chooseReady && elevatorState.status !== 'returning' && (elevatorState.status === 'arrived' && roomAssets ? <RoomControls assets={roomAssets} state={roomState} reducedMotion={reducedMotion} onView={changeRoomView} onObserver={openObserverProfile} onProject={jumpToProject} onProjectSection={selectProjectSection} onCloseProject={()=>changeRoomView('main')} onMove={moveInRoom} onLook={lookInRoom} onPause={() => setRoomState((current) => ({ ...current, paused: !current.paused }))} onToggleWalk={toggleRoomWalk} onSeekTour={seekRoomTour} onStation={stepRoomStation} onExhibit={selectRoomExhibit} onLookAt={lookAtRoomExhibit} onResetLook={resetRoomLook} /> : <ElevatorControls levels={cabin.assets.manifest.levels} state={elevatorState} onSelect={selectLevel} onReplay={replaySelection} onEnterRoom={selectLevel} onFocusLevel={setFocusedLevel} onPressLevel={setPressedLevel} />)}
        {roomState.returnPrompt && roomAssets && <RoomReturnDialog label={roomAssets.manifest.label} onConfirm={confirmRoomReturn} onCancel={cancelRoomReturn} />}
        {elevatorState.status === 'returning' && <div className="room-return-status" role="status" aria-live="polite"><span className="room-status-dot" aria-hidden="true"/><span id="room-return-status">Walking back to the elevator…</span></div>}
        {chooseReady && roomId === 'about' && elevatorState.status === 'arrived' && roomAssets && roomState.profileOpen && <ObserverProfile onClose={closeObserverProfile} />}
        <div className="city-controls" hidden={inRoom} aria-label="Walkthrough controls" style={{ '--timeline-progress': `${(frame - firstFrame) / (lastFrame - firstFrame) * 100}%` }}>
          <label className="sr-only" htmlFor="city-timeline">Walkthrough frame. Use arrow keys to move through the city.</label>
          <div className="city-timeline">
            <input id="city-timeline" type="range" min={firstFrame} max={lastFrame} step="1" value={frame} onChange={(event) => { replaySelection();seekFrame(Number(event.target.value)) }} aria-valuetext={`Frame ${frame}: ${phase.title}`} />
          </div>
        </div>
        {elevatorState.status === 'arrived' && roomAssets && roomState.view === 'main' && !roomState.profileOpen && !roomState.returnPrompt && <RoomProgressBar key={roomId} assets={roomAssets} navigationRef={navigationRef} inputRef={roomProgressRef} onSeek={seekRoomProgress} />}
         <NegativeCursor />
         {guideOpen && <GuideOverlay reducedMotion={reducedMotion} onClose={closeGuide} />}
      </div>
    </section>
  )
}
