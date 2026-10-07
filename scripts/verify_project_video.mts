import assert from 'node:assert/strict'
import fs from 'node:fs'
import { sceneFile } from './node_json.mts'

const manifest=sceneFile(new URL('../public/models/rooms/projects/scene.json',import.meta.url),'projects')
const rootVideos=fs.readdirSync(new URL('..',import.meta.url),{withFileTypes:true}).filter(entry=>entry.isFile()&&/\.(mp4|webm|mov|m4v|avi|mkv)$/i.test(entry.name)).map(entry=>entry.name)
assert.deepEqual(rootVideos,[],'Store video uploads in assets/project-hallway/videos/originals/<project>/, not the repository root')
for(const id of ['agent-property','report-automation','Aria','fedora-dotfiles']) {
const project=manifest.projects.find(project=>project.id===id)
assert.ok(project?.video && project.card)
assert.ok(Math.abs(project.card.width-4.6)<1e-5)
assert.ok(Math.abs(project.card.height-2.5875)<1e-5)
assert.ok(Math.abs(project.card.width/project.card.height-16/9)<1e-5)
for(const key of ['preview','full','previewFallback','fullFallback','poster'] as const) {
  assert.ok(project.video[key])
  assert.match(project.video[key],/^videos\/[^/]+\.(mp4|jpg)$/,'Project browser media belongs in public/videos/')
  const path=new URL(`../public/${project.video[key]}`,import.meta.url)
  assert.ok(fs.statSync(path).size>1000,`Missing or empty video asset: ${key}`)
}
const sharedClip=project.video.preview===project.video.full
assert.ok(fs.statSync(new URL(`../public/${project.video.preview}`,import.meta.url)).size<(sharedClip?10_000_000:4_000_000),sharedClip?'Shared preview/full clip stays below 10 MB':'Lightweight previews stay below 4 MB')
if(id==='fedora-dotfiles') {
  assert.equal(sharedClip,true,'Fedora uses the same recording for preview and full playback')
  assert.equal(project.video.previewFallback,project.video.fullFallback,'Fedora shares one H.264 compatibility recording')
  assert.ok(fs.statSync(new URL(`../public/${project.video.fullFallback}`,import.meta.url)).size<10_000_000)
}
}
assert.equal(manifest.actors.length,15)
assert.equal(manifest.projects.filter(project=>project.video).length,4,'Only the requested four boards should have videos')
console.log('PASS organized video assets with no root recordings, four landscape 16:9 video boards, shared Fedora preview/full recording, real media assets and preserved other projects/NPC count')
