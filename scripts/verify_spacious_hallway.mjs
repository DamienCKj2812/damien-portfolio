import assert from 'node:assert/strict'
import fs from 'node:fs'

const read=path=>JSON.parse(fs.readFileSync(new URL(`../${path}`,import.meta.url)))
const layout=read('assets/project-hallway/hallway-layout.json')
const manifest=read('public/models/rooms/projects/scene.json')
const journey=read('public/models/journey.json')
assert.equal(layout.widthMeters,14.2)
assert.ok(Math.abs(layout.lengthMeters-126.2)<1e-6)
assert.equal(layout.projectBaySpacingMeters,11.5)
assert.equal(layout.rightDisplayStaggerMeters,3)
assert.equal(journey.rooms.projects.width,14.2)
assert.deepEqual(journey.rooms.projects.entranceAnchor,[0,-10,0])
assert.ok(Math.abs(manifest.navigation.maxY-123.2)<1e-6)
assert.equal(manifest.actors.length,15)
for(const project of manifest.projects)assert.ok(Math.abs(Math.abs(project.position[0])-4.8)<1e-6)
for(const category of manifest.navigation.categories)for(const side of [-1,1]) {
  const ys=manifest.projects.filter(project=>project.section===category.id&&Math.sign(project.position[0])===side).map(project=>project.position[1]).sort((a,b)=>a-b)
  for(let i=1;i<ys.length;i++)assert.ok(Math.abs(ys[i]-ys[i-1]-11.5)<1e-6)
}
console.log('PASS 14.2 m hall, 126.2 m length, 11.5 m project spacing, 3 m stagger, expanded navigation and unchanged elevator anchor/NPC count')
