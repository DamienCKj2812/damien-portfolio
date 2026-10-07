import assert from 'node:assert/strict'
import fs from 'node:fs'

const manifest=JSON.parse(fs.readFileSync(new URL('../public/models/rooms/projects/scene.json',import.meta.url)))
for(const id of ['agent-property','report-automation','Aria']) {
const project=manifest.projects.find(project=>project.id===id)
assert.ok(project.video)
assert.ok(Math.abs(project.card.width-4.6)<1e-5)
assert.ok(Math.abs(project.card.height-2.5875)<1e-5)
assert.ok(Math.abs(project.card.width/project.card.height-16/9)<1e-5)
for(const key of ['preview','full','previewFallback','fullFallback','poster']) {
  const path=new URL(`../public/${project.video[key]}`,import.meta.url)
  assert.ok(fs.statSync(path).size>1000,`Missing or empty video asset: ${key}`)
}
assert.ok(fs.statSync(new URL(`../public/${project.video.preview}`,import.meta.url)).size<4_000_000)
}
assert.equal(manifest.actors.length,15)
assert.equal(manifest.projects.filter(project=>project.video).length,3,'Only the requested three boards should have videos')
console.log('PASS three landscape 16:9 video boards, real preview/full/poster/fallback assets and preserved other projects/NPC count')
