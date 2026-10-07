/* eslint react-hooks/immutability: "off" -- Shared playback arbitration owns mutable media/candidate refs. */
import { useMemo } from 'react'
import { useFrame, useThree } from '@react-three/fiber'
import ProjectVideoBoard from './ProjectVideoBoard'
import type { ProjectVideoCandidate, ProjectVideoInteract, ProjectVideoSelection, VideoProject } from './ProjectVideoBoard'
import type { RoomState } from '../../types/navigation'
import type { ProjectMetadata, SceneGeometry } from '../../types/scene'

export interface ProjectVideoBoardsProps {
  projects: readonly ProjectMetadata[]
  groups: readonly SceneGeometry[]
  roomState: RoomState
  roomArrived: boolean
  reducedMotion: boolean
  onInteract: ProjectVideoInteract
}

export default function ProjectVideoBoards({ projects, groups, roomState, roomArrived, reducedMotion, onInteract }: ProjectVideoBoardsProps) {
  const { invalidate, gl }=useThree()
  const selection=useMemo<ProjectVideoSelection>(()=>({active:null,prompt:null,entries:new Map<string, ProjectVideoCandidate>()}),[])
  useFrame(()=>{
    let prompt: string | null=null,distance=Infinity,focusedPrompt=false
    for(const [id,entry] of selection.entries) {
      if(!entry.promptElement||!entry.promptEligible||!entry.promptEnabled) continue
      if(entry.focused&&!focusedPrompt||entry.focused===focusedPrompt&&entry.distance<distance) {
        prompt=id;distance=entry.distance;focusedPrompt=entry.focused
      }
    }
    // Hide every losing prompt before revealing the winner. Prompt selection is
    // distance-based and independent of preview playback/reduced-motion policy.
    for(const [id,entry] of selection.entries) {
      const node=entry.promptElement
      if(!node||id===prompt) continue
      if(node.style.visibility!=='hidden') node.style.visibility='hidden'
      if(node.dataset.visible!=='false') node.dataset.visible='false'
    }
    const node=prompt?selection.entries.get(prompt)?.promptElement:null
    if(node) {
      if(node.style.visibility!=='visible') node.style.visibility='visible'
      if(node.dataset.visible!=='true') node.dataset.visible='true'
    }
    if(selection.prompt!==prompt) {
      selection.prompt=prompt
      gl.domElement.dataset.activeProjectPrompt=prompt || ''
      invalidate()
    }
    let best: string | null=null,score=Infinity
    for(const [id,entry] of selection.entries) {
      if(!entry.eligible) continue
      const rank=entry.focused?-100:entry.score-(selection.active===id ? .08 : 0)
      if(rank<score) {best=id;score=rank}
    }
    if(selection.active===best) return
    // Pause the old decoder before enabling the next one, including pending
    // play promises. This guarantees there cannot be overlapping playback.
    for(const [id,entry] of selection.entries) if(id!==best) entry.video.pause()
    selection.active=best
    gl.domElement.dataset.activeProjectVideo=best || ''
    invalidate()
  },-.1)
  return projects.filter((project): project is VideoProject=>Boolean(project.video&&project.card)).map(project=><ProjectVideoBoard key={project.id} project={project} groups={groups} selection={selection}
    enabled={roomArrived&&!roomState.profileOpen&&!roomState.returnPrompt&&['main','project'].includes(roomState.view)&&(roomState.view==='main'||roomState.project===project.id)}
    focused={roomState.view==='project'&&roomState.project===project.id} paused={roomState.paused} reducedMotion={reducedMotion} onInteract={onInteract}/>)
}
