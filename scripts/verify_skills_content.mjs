import assert from 'node:assert/strict'
import fs from 'node:fs'
import { createHash } from 'node:crypto'
import { PerspectiveCamera } from 'three'
import { createRoomAlignment } from '../src/components/city/roomJourney.js'
import { createProjectCardFocus } from '../src/components/city/projectCardFocus.js'
import { publicCaseSections } from '../src/data/publicLinks.js'

const file=path=>fs.readFileSync(new URL(`../${path}`,import.meta.url))
const json=path=>JSON.parse(file(path))
const source=json('assets/skills-gallery/skills.json')
const manifest=json('public/models/rooms/skills/scene.json')
const projects=json('assets/project-hallway/projects.json').projects
const cards=manifest.exhibits.filter(entry=>entry.kind==='skill')
const microservices=cards.find(entry=>entry.title==='Microservices')
assert.equal(microservices.displayItems.length,4)
assert.ok(!/kafka|gateways?/i.test(JSON.stringify(microservices)),'Removed tools must not appear in the Microservices board or details')
assert.equal(source.profileSourceHash,createHash('sha256').update(file('src/data/portfolio.js')).digest('hex'))
assert.equal(source.projectSourceHash,createHash('sha256').update(file('assets/project-hallway/projects.json')).digest('hex'))
assert.equal(cards.length,9)
assert.equal(manifest.actors.length,90)
assert.equal(manifest.frameEnd,959)
assert.equal(manifest.channelStride,12)
assert.equal(manifest.navigation.route.frameEnd,2940)
assert.equal(manifest.navigation.animationFollowsWalk,false)
assert.equal(manifest.exhibits.find(entry=>entry.id==='atat').title,'AT-AT walker')
assert.ok(manifest.cameras.atat)
const preserved=json('assets/skills-gallery/skill-content-verification.json')
assert.equal(preserved.architectureSculptureVisitorsAndRoutePreserved,true)
const alignment=createRoomAlignment({manifest},json('public/models/journey.json'))
let fits=0
for (const entry of source.entries) {
  const card=cards.find(card=>card.id===entry.id)
  assert.ok(card)
  assert.deepEqual(card.items,entry.items)
  assert.deepEqual(card.catalogueSections,publicCaseSections(entry))
  assert.equal(entry.displayItems.length,entry.title==='Microservices'?4:5)
  assert.equal(entry.catalogueSections.length,8)
  assert.ok(!/concept exhibit|sample project/i.test(card.contentStatus))
  for (const id of entry.evidenceProjectIds) assert.ok(projects.some(project=>project.id===id))
  assert.ok(entry.profileOnly.every(item=>card.catalogueSections.some(section=>section.markdown.includes(item))))
  assert.ok(card.card.normal&&card.card.right)
  for (const size of [{width:1440,height:900},{width:1024,height:768},{width:938,height:986},{width:390,height:844},{width:360,height:740},{width:844,height:390}]) {
    const pose=createProjectCardFocus(card,alignment,size,true)
    const camera=new PerspectiveCamera(pose.displayFov,size.width/size.height,.01,350)
    camera.position.copy(pose.position);camera.quaternion.copy(pose.quaternion)
    camera.setViewOffset(size.width,size.height,pose.offsetX,pose.offsetY,size.width,size.height);camera.updateMatrixWorld()
    for (const corner of pose.corners) {
      const projected=corner.clone().project(camera),x=(projected.x+1)*size.width/2,y=(1-projected.y)*size.height/2
      assert.ok(x>=pose.rect.left-.01&&x<=pose.rect.right+.01&&y>=pose.rect.top-.01&&y<=pose.rect.bottom+.01,`${entry.id}: card clipped at ${size.width}×${size.height}`)
    }
    fits++
  }
}
console.log(`PASS nine evidence-backed Skills areas, explicit profile/learning scope, preserved AT-AT/90 parts/2940-frame route and ${fits} full-card camera fits`)
