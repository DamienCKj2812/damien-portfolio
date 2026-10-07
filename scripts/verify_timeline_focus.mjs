import assert from 'node:assert/strict'
import fs from 'node:fs'
import { PerspectiveCamera, Vector3 } from 'three'
import { createRoomAlignment } from '../src/components/city/roomJourney.js'
import { createProjectCardFocus } from '../src/components/city/projectCardFocus.js'

const manifest=JSON.parse(fs.readFileSync(new URL('../public/models/rooms/experience/scene.json',import.meta.url)))
const journey=JSON.parse(fs.readFileSync(new URL('../public/models/journey.json',import.meta.url)))
const alignment=createRoomAlignment({manifest},journey)
assert.deepEqual(manifest.exhibits.map(entry=>entry.id),['diploma-information-technology','lyj-events-marketing','cos-great-trading','freelance-full-stack','bachelors-computer-science','current-focus'])
const bachelor=manifest.exhibits.find(entry=>entry.id==='bachelors-computer-science')
assert.equal(bachelor.title,'Bachelor of Degree in Computer Science (Data Analytics Specialism)')
assert.equal(bachelor.cardSpecialism,'(Data Analytics Specialism)')
const diploma=manifest.exhibits[0]
assert.equal(diploma.cardTitle,'DIPLOMA IN IT\n(Software Engineer Specialism)')
assert.equal(diploma.logo.id,'apu')
assert.deepEqual(manifest.exhibits.slice(0,3).map(entry=>entry.logo.id),['apu','lyj','cos'])
assert.match(bachelor.caption,/EXPECTED JUNE 2027.*3\.36/)
const freelance=manifest.exhibits.find(entry=>entry.id==='freelance-full-stack')
assert.ok(freelance.catalogueSections.some(section=>section.heading==='MyRumawip'))
assert.ok(freelance.catalogueSections.some(section=>section.heading==='Amplifii (Ampress)'&&section.markdown.includes('unreleased')))
const sizes=[{width:1440,height:900},{width:1280,height:720},{width:1024,height:768},{width:938,height:986},{width:390,height:844},{width:360,height:740},{width:844,height:390}]
for(const entry of manifest.exhibits) {
  assert.ok(entry.catalogueSections.length>=3)
  assert.ok(entry.metadata.length>=2)
  const normal=new Vector3().fromArray(entry.card.normal),right=new Vector3().fromArray(entry.card.right)
  assert.ok(Math.abs(normal.dot(right))<1e-6,'Timeline card face axes must be orthogonal')
  for(const size of sizes) {
    const pose=createProjectCardFocus(entry,alignment,size,true)
    const camera=new PerspectiveCamera(pose.displayFov,size.width/size.height,.01,350)
    camera.position.copy(pose.position);camera.quaternion.copy(pose.quaternion)
    camera.setViewOffset(size.width,size.height,pose.offsetX,pose.offsetY,size.width,size.height)
    camera.updateMatrixWorld()
    for(const corner of pose.corners) {
      const point=corner.clone().project(camera),x=(point.x+1)*size.width/2,y=(1-point.y)*size.height/2
      assert.ok(point.z>-1&&point.z<1)
      assert.ok(x>=pose.rect.left-.01&&x<=pose.rect.right+.01&&y>=pose.rect.top-.01&&y<=pose.rect.bottom+.01,`${entry.id}: clipped focused card at ${size.width}×${size.height}`)
    }
  }
}
console.log('PASS six actual timeline records, education status, freelance details and 42 responsive focused-card fits')
