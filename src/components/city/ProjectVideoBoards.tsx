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
  const selection=useMemo<ProjectVideoSelection>(()=>({active:null,entries:new Map<string, ProjectVideoCandidate>()}),[])
  useFrame(()=>{
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
