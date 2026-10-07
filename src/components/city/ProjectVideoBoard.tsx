/* eslint react-hooks/immutability: "off" -- Media, projection and Three.js resources update on demand frames. */
import { useEffect, useMemo, useRef, useState } from 'react'
import { useFrame, useThree } from '@react-three/fiber'
import type { ThreeEvent } from '@react-three/fiber'
import { Html } from '@react-three/drei'
import { DoubleSide, Matrix4, MeshBasicMaterial, Quaternion, Raycaster, SRGBColorSpace, TextureLoader, Vector3, VideoTexture } from 'three'
import type { Group, Intersection, Texture } from 'three'
import type { CardMetadata, ProjectMetadata, SceneGeometry, VideoMetadata } from '../../types/scene'
import { createVideoOccluder, videoIsOccluded } from './videoOcclusion'
import { setVideoAudioFocus } from '../../audio/videoAudioFocus'
import './projectVideoBoard.css'

export type VideoProject = ProjectMetadata & { card: CardMetadata; video: VideoMetadata }
export type ProjectVideoInteract = (id: string, source?: 'scene' | 'label') => void

export interface ProjectVideoCandidate {
  video: HTMLVideoElement
  eligible: boolean
  focused: boolean
  score: number
  centred: boolean
  promptElement: HTMLDivElement | null
  promptEligible: boolean
  promptEnabled: boolean
  distance: number
}

export interface ProjectVideoSelection {
  active: string | null
  prompt: string | null
  entries: Map<string, ProjectVideoCandidate>
}

export interface ProjectVideoPlaybackController {
  visible: boolean
  enabled: boolean
  focused: boolean
  paused: boolean
  source: string | null | undefined
  mode: 'preview' | 'full' | null
  manualPause: boolean
  pending: boolean
  generation: number
  frame: number
  fallbackFrame: number
}

interface ProjectVideoMedia {
  video: HTMLVideoElement
  texture: VideoTexture | null
  textureSource: string | null
  poster: Texture | null
}

export interface ProjectVideoBoardProps {
  project: VideoProject
  groups: readonly SceneGeometry[]
  enabled: boolean
  focused: boolean
  paused: boolean
  reducedMotion: boolean
  onInteract: ProjectVideoInteract
  selection: ProjectVideoSelection
}

const screenOrigin = (): [number, number] => [0, 0]
const seconds = (value: number) => `${Math.floor(value / 60)}:${String(Math.floor(value % 60)).padStart(2, '0')}`

export default function ProjectVideoBoard({ project, groups, enabled, focused, paused, reducedMotion, onInteract, selection }: ProjectVideoBoardProps) {
  const root = useRef<Group | null>(null), material = useRef<MeshBasicMaterial | null>(null), dock = useRef<HTMLDivElement | null>(null), hovered = useRef(false), held = useRef(false)
  const playback = useRef<ProjectVideoPlaybackController>({ visible:false, enabled:false, focused:false, paused:false, source:null, mode:null, manualPause:false, pending:false, generation:0, frame:0, fallbackFrame:0 })
  const { camera, size, invalidate } = useThree()
  const [state, setState] = useState({ playing:false, muted:true, time:0, duration:0, error:'' })
  const media = useMemo<ProjectVideoMedia>(() => {
    const video=document.createElement('video')
    video.muted=true;video.playsInline=true;video.preload='none';video.setAttribute('playsinline','')
    // Construct the texture only after a decoded frame exists. A memoized
    // VideoTexture cannot survive StrictMode's dispose/replay or a size change.
    return {video,texture:null,textureSource:null,poster:null}
  }, [])
  const candidate=useMemo<ProjectVideoCandidate>(()=>({video:media.video,eligible:false,focused:false,score:Infinity,centred:false,promptElement:null,promptEligible:false,promptEnabled:false,distance:Infinity}),[media])
  useEffect(()=>{
    selection.entries.set(project.id,candidate)
    return ()=>{selection.entries.delete(project.id);media.video.pause();if(selection.active===project.id) selection.active=null;if(selection.prompt===project.id) selection.prompt=null}
  },[selection,project.id,candidate,media])
  const face = useMemo(() => {
    const card=project.card,normal=new Vector3().fromArray(card.normal),right=new Vector3().fromArray(card.right || [0,1,0]),up=new Vector3(0,0,1)
    return {center:new Vector3().fromArray(card.center).addScaledVector(normal,(card.frontDepth ?? .035)+.002),normal,right,up,
      rotation:new Quaternion().setFromRotationMatrix(new Matrix4().makeBasis(right,up,normal)),
      corners:[-1,1].flatMap(x=>[-1,1].map(y=>new Vector3().fromArray(card.center).addScaledVector(right,x*(card.width/2+.05)).addScaledVector(up,y*(card.height/2+.05))))}
  }, [project])
  const scratch=useMemo(()=>{
    const hits: Intersection[]=[]
    return {point:new Vector3(),center:new Vector3(),localCamera:new Vector3(),direction:new Vector3(),matrix:new Matrix4(),cameraMatrix:new Matrix4(),projection:new Matrix4(),rootMatrix:new Matrix4(),raycaster:new Raycaster(),hits,dirty:true}
  },[])
  const occlusion=useMemo(()=>{
    const pickMaterial=new MeshBasicMaterial({side:DoubleSide})
    return {material:pickMaterial,meshes:groups.filter(item=>item.actor===0&&item.kind==='solid'&&(item.opacity??1)>=1&&!(item.role==='project'&&item.id===project.id)).map(item=>createVideoOccluder(item.geometry,pickMaterial))}
  },[groups,project.id])

  useEffect(() => {
    let disposed=false
    const loader=new TextureLoader()
    const poster=loader.load(`${import.meta.env.BASE_URL}${project.video.poster}`,()=>{
      if(disposed) {poster.dispose();return}
      media.poster=poster
      if(material.current&&!media.texture) {material.current.map=poster;material.current.color.set(0xffffff);material.current.needsUpdate=true}
      invalidate()
    })
    poster.colorSpace=SRGBColorSpace
    return ()=>{disposed=true;poster.dispose();media.poster=null}
  },[project.video.poster,media,invalidate])

  useEffect(() => {
    const video=media.video,control=playback.current
    // lib.dom declares these APIs; older browsers can omit either capability.
    const videoFrames: Partial<Pick<HTMLVideoElement, 'requestVideoFrameCallback' | 'cancelVideoFrameCallback'>>=video
    const stopFrames=()=>{
      if(control.frame&&videoFrames.cancelVideoFrameCallback) videoFrames.cancelVideoFrameCallback(control.frame)
      cancelAnimationFrame(control.fallbackFrame);control.frame=0;control.fallbackFrame=0
    }
    const draw=()=>{
      control.frame=0;control.fallbackFrame=0
      if(video.paused||document.hidden||selection.active!==project.id||!control.visible||!control.enabled||control.paused) return
      if(media.texture&&video.readyState>=video.HAVE_CURRENT_DATA) media.texture.needsUpdate=true
      invalidate()
      if(videoFrames.requestVideoFrameCallback) control.frame=videoFrames.requestVideoFrameCallback(draw)
      else control.fallbackFrame=requestAnimationFrame(draw)
    }
    const sync=()=>{
      if(dock.current) {
        dock.current.dataset.videoPaused=String(video.paused);dock.current.dataset.videoTime=String(video.currentTime)
        dock.current.dataset.videoDuration=String(Number.isFinite(video.duration)?video.duration:0);dock.current.dataset.videoSource=video.currentSrc || video.src
      }
      setVideoAudioFocus(video,control.focused&&!video.paused&&!video.muted&&!document.hidden)
      if(control.focused) setState({playing:!video.paused,muted:video.muted,time:video.currentTime,duration:Number.isFinite(video.duration)?video.duration:0,error:''})
    }
    const ready=()=>{
      if(video.readyState<video.HAVE_CURRENT_DATA||!video.videoWidth||!video.videoHeight) return
      const source=video.currentSrc || video.src
      if(!media.texture||media.textureSource!==source) {
        media.texture?.dispose()
        media.texture=new VideoTexture(video);media.texture.colorSpace=SRGBColorSpace;media.textureSource=source
      }
      media.texture.needsUpdate=true
      if(material.current) {material.current.map=media.texture;material.current.color.set(0xffffff);material.current.needsUpdate=true}
      sync();invalidate()
    }
    const play=()=>{control.pending=false;if(selection.active!==project.id||!control.enabled||control.paused||document.hidden){video.pause();return}stopFrames();sync();draw()}
    const pause=()=>{stopFrames();sync();invalidate()}
    const ended=()=>{control.manualPause=true;pause()}
    const error=()=>{
      const fallback=control.focused?project.video.fullFallback:project.video.preview
      if(fallback&&!video.src.endsWith(fallback)) {
        media.texture?.dispose();media.texture=null;media.textureSource=null
        if(material.current) {material.current.map=media.poster;material.current.needsUpdate=true}
        video.src=`${import.meta.env.BASE_URL}${fallback}`;video.load()
        if(selection.active===project.id&&control.visible&&control.enabled&&!control.paused) void video.play().catch(()=>{})
      } else {setState(current=>({...current,playing:false,error:'Video unavailable. Use the project website link.'}));stopFrames()}
    }
    const visibility=()=>{
      if(document.hidden) video.pause()
      else {scratch.dirty=true;invalidate();if(selection.active===project.id&&control.visible&&control.enabled&&!control.paused&&!control.manualPause&&(control.focused||!reducedMotion)) void video.play().catch(()=>{})}
    }
    const listeners: [keyof HTMLMediaElementEventMap, () => void][]=[['loadeddata',ready],['loadedmetadata',sync],['emptied',sync],['playing',play],['pause',pause],['ended',ended],['timeupdate',sync],['volumechange',sync],['seeked',ready],['error',error]]
    for(const [event,handler] of listeners) video.addEventListener(event,handler)
    document.addEventListener('visibilitychange',visibility)
    return ()=>{
      control.generation++;stopFrames();video.pause();setVideoAudioFocus(video,false)
      for(const [event,handler] of listeners) video.removeEventListener(event,handler)
      document.removeEventListener('visibilitychange',visibility)
      video.removeAttribute('src');video.load();media.texture?.dispose();media.texture=null;media.textureSource=null
      control.source=null;control.mode=null;control.pending=false
    }
  },[media,project.video,project.id,reducedMotion,invalidate,selection,scratch])
  useEffect(()=>()=>occlusion.material.dispose(),[occlusion])
  useEffect(()=>{scratch.dirty=true;invalidate()},[enabled,focused,paused,reducedMotion,size.width,size.height,scratch,invalidate])

  useFrame(()=>{
    const control=playback.current,video=media.video
    control.enabled=enabled;control.paused=paused;control.focused=focused
    if(!root.current||!dock.current) return
    root.current.updateWorldMatrix(true,false)
    const changed=scratch.dirty||!scratch.cameraMatrix.equals(camera.matrixWorld)||!scratch.projection.equals(camera.projectionMatrix)||!scratch.rootMatrix.equals(root.current.matrixWorld)
    if(changed) {
      scratch.dirty=false;scratch.cameraMatrix.copy(camera.matrixWorld);scratch.projection.copy(camera.projectionMatrix);scratch.rootMatrix.copy(root.current.matrixWorld)
      scratch.localCamera.copy(camera.position).applyMatrix4(scratch.matrix.copy(root.current.matrixWorld).invert())
      let visible=enabled&&!document.hidden&&scratch.direction.subVectors(scratch.localCamera,face.center).dot(face.normal)>0
      let left=Infinity,right=-Infinity,top=Infinity,bottom=-Infinity
      for(const corner of face.corners) {
        scratch.point.copy(corner).applyMatrix4(root.current.matrixWorld).project(camera)
        if(scratch.point.z < -1 || scratch.point.z > 1) visible=false
        const x=(scratch.point.x+1)*size.width/2,y=(1-scratch.point.y)*size.height/2
        left=Math.min(left,x);right=Math.max(right,x);top=Math.min(top,y);bottom=Math.max(bottom,y)
      }
      visible=visible&&right>0&&left<size.width&&bottom>0&&top<size.height&&right-left>32
      const centred=left<=size.width/2+32&&right>=size.width/2-32&&top<=size.height/2+32&&bottom>=size.height/2-32
      if(visible&&(focused||centred||hovered.current||held.current)) {
        scratch.center.copy(face.center).applyMatrix4(root.current.matrixWorld)
        for(const mesh of occlusion.meshes) mesh.matrixWorld.copy(root.current.matrixWorld)
        scratch.raycaster.set(camera.position,scratch.direction.subVectors(scratch.center,camera.position).normalize())
        scratch.raycaster.far=Math.max(.01,scratch.center.distanceTo(camera.position)-.06);scratch.hits.length=0
        if(videoIsOccluded(scratch.raycaster,occlusion.meshes,scratch.hits)) visible=false
      }
      control.visible=visible
      candidate.centred=centred
      candidate.score=Math.abs((left+right)/2-size.width/2)/size.width+Math.abs((top+bottom)/2-size.height/2)/size.height*.25
      const show=visible&&(focused||hovered.current||held.current||centred)
      const node=dock.current,width=Math.min(focused?620:330,size.width-40),gap=14
      node.style.width=`${width}px`
      const height=node.offsetHeight||90,bottomLimit=size.height-(focused?106:55)
      let x=Math.max(20,Math.min(size.width-width-20,(left+right-width)/2)),y=bottom+gap
      if(y+height>bottomLimit) y=top-height-gap
      if(y<82) {
        if(right+gap+width<size.width-20) {x=right+gap;y=Math.max(82,Math.min(size.height-height-106,(top+bottom-height)/2))}
        else if(left-gap-width>20) {x=left-gap-width;y=Math.max(82,Math.min(size.height-height-106,(top+bottom-height)/2))}
        else y=-10000
      }
      const menu=!focused&&document.querySelector('.city-stage[data-room="projects"] .room-interface[data-collapsed="false"]')
      if(menu) {
        const bounds=menu.getBoundingClientRect()
        if(x<bounds.right&&x+width>bounds.left&&y<bounds.bottom&&y+height>bounds.top) {
          x=Math.max(x,bounds.right+20)
          if(x+width>size.width-20) y=-10000
        }
      }
      const outside=x+width<=left-gap||x>=right+gap||y+height<=top-gap||y>=bottom+gap
      node.style.width=`${width}px`;node.style.transform=`translate(${x}px,${y}px)`
      candidate.promptEligible=show&&outside&&y>=0
      candidate.distance=scratch.center.copy(face.center).applyMatrix4(root.current.matrixWorld).distanceToSquared(camera.position)
      node.dataset.boardLeft=String(left);node.dataset.boardRight=String(right);node.dataset.boardTop=String(top);node.dataset.boardBottom=String(bottom)
    }
    candidate.promptElement=dock.current
    candidate.promptEnabled=enabled&&!paused&&!document.hidden
    dock.current.dataset.promptEligible=String(candidate.promptEligible&&candidate.promptEnabled)
    dock.current.dataset.cameraDistance=String(candidate.distance)
    const source=focused?(video.canPlayType('video/mp4; codecs="av01.0.08M.08"')?project.video.full:project.video.fullFallback):(project.video.previewFallback || project.video.preview)
    const mode=focused?'full':'preview'
    if(control.mode!==mode) {
      control.generation++;control.mode=mode;control.source=null;control.manualPause=false;control.pending=false;video.pause();video.muted=true;video.loop=!focused
      video.removeAttribute('src');video.load()
      media.texture?.dispose();media.texture=null;media.textureSource=null
      if(material.current) {material.current.map=media.poster;material.current.needsUpdate=true}
    }
    candidate.focused=focused
    candidate.eligible=control.visible&&enabled&&!paused&&!document.hidden&&(focused||candidate.centred&&!reducedMotion)
    if(dock.current) dock.current.dataset.cameraSelected=String(selection.active===project.id)
    const shouldPlay=selection.active===project.id&&candidate.eligible&&!control.manualPause
    if(shouldPlay&&control.source!==source) {
      control.source=source;video.pause()
      media.texture?.dispose();media.texture=null;media.textureSource=null
      if(material.current) {material.current.map=media.poster;material.current.needsUpdate=true}
      video.src=`${import.meta.env.BASE_URL}${source}`;video.load()
      control.pending=true
      const generation=control.generation
      void video.play().catch((failure: unknown)=>{
        if(generation!==control.generation) return
        control.pending=false
        if(!(typeof failure==='object'&&failure!==null&&'name' in failure&&failure.name==='AbortError')) {control.manualPause=true;setState(current=>({...current,playing:false,error:'Press Play to start the walkthrough.'}))}
      })
    } else if(!shouldPlay&&!video.paused) video.pause()
    else if(shouldPlay&&video.paused&&!video.ended&&control.source&&!control.pending) {control.pending=true;void video.play().catch(()=>{control.pending=false;control.manualPause=true})}
  },-.2)

  const toggle=()=>{
    const video=media.video,control=playback.current
    control.manualPause=!video.paused
    if(video.paused) {if(video.ended) video.currentTime=0;void video.play().catch(()=>{})}
    else video.pause()
    invalidate()
  }
  const point=(active: boolean)=>{hovered.current=active;scratch.dirty=true;document.body.style.cursor=active&&!focused?'pointer':'';invalidate()}
  return <group ref={root} name={`project-video-board-${project.id}`}>
    <mesh position={face.center.toArray()} quaternion={face.rotation} renderOrder={1}
      onAfterRender={()=>{if(dock.current){dock.current.dataset.renderedSurface=material.current?.map===media.texture&&media.texture?'video':material.current?.map===media.poster&&media.poster?'poster':'empty'}}}
      {...(enabled&&!focused&&!paused?{onClick:(event: ThreeEvent<MouseEvent>)=>{event.stopPropagation();if(event.delta<=5) onInteract(project.id)}}:{})}
      {...(enabled&&!focused?{onPointerOver:(event: ThreeEvent<PointerEvent>)=>{event.stopPropagation();point(true)}}:{})} onPointerOut={()=>point(false)}>
      <planeGeometry args={[project.card.width,project.card.height]}/>
      <meshBasicMaterial ref={material} color={media.poster?'white':'#080808'} toneMapped={false} side={DoubleSide}/>
    </mesh>
    {/* Our cached projection/raycast owns visibility; Html's fixed screen origin must not cache an arrival-time behind-camera result. */}
    <Html position={face.center.toArray()} calculatePosition={screenOrigin} onOcclude={()=>{}} zIndexRange={[24,16]} style={{pointerEvents:'none'}}>
      <div ref={dock} className={`project-video-dock ${focused?'project-video-controls':''}`} data-project-video={project.id} data-video-mode={focused?'full':'preview'}
        onPointerEnter={()=>{held.current=true;scratch.dirty=true;invalidate()}} onPointerLeave={()=>{held.current=false;scratch.dirty=true;invalidate()}}>
        {focused?<>
          <div className="project-video-control-row">
            <button type="button" onClick={toggle}>{state.playing?'Pause video':state.time>=state.duration&&state.duration>0?'Replay video':'Play video'}</button>
            <label className="sr-only" htmlFor={`project-video-seek-${project.id}`}>Walkthrough playback position</label>
            <input id={`project-video-seek-${project.id}`} type="range" min="0" max={state.duration || 1} step=".1" value={Math.min(state.time,state.duration || 1)} disabled={!state.duration}
              onChange={event=>{media.video.currentTime=Number(event.target.value);invalidate()}}/>
            <output>{seconds(state.time)} / {seconds(state.duration)}</output>
            <button type="button" aria-pressed={!state.muted} onClick={()=>{media.video.muted=!media.video.muted;if(!media.video.paused) void media.video.play().catch(()=>{})}}>{state.muted?'Sound off':'Sound on'}</button>
          </div>
          {state.error&&<p role="status">{state.error}</p>}
        </>:<button type="button" className="project-video-description" data-sound-effect="environment" aria-label={`Watch ${project.title} full walkthrough`} disabled={!enabled||paused}
          onFocus={()=>{held.current=true;scratch.dirty=true;invalidate()}} onBlur={()=>{held.current=false;scratch.dirty=true;invalidate()}} onClick={()=>{if(selection.prompt===project.id) onInteract(project.id,'label')}}>
          <strong>{project.title}</strong><span>{project.summary.replaceAll('\n',' ')}</span><span className="project-video-action">Watch full walkthrough ↗</span>
        </button>}
      </div>
    </Html>
  </group>
}
