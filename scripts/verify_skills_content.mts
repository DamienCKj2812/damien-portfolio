import assert from 'node:assert/strict'
import fs from 'node:fs'
import { createHash } from 'node:crypto'
import { PerspectiveCamera, Quaternion, Vector3 } from 'three'
import { createProjectCardFocus } from '../src/components/city/projectCardFocus.ts'
import { publicCaseSections } from '../src/data/publicLinks.ts'
import { listValue, numberValue, objectValue, parseCaseSections, parseProjectCatalogue, stringValue } from '../src/types/portfolio.ts'
import type { CardMetadata, Vec3 } from '../src/types/scene.ts'
import { journeyFile, sceneFile } from './node_json.mts'

const file=(path: string)=>fs.readFileSync(new URL(`../${path}`,import.meta.url))
const json=(path: string): unknown=>JSON.parse(file(path).toString('utf8'))
const source=objectValue(json('assets/skills-gallery/skills.json'),'skills source')
const manifest=sceneFile(new URL('../public/models/rooms/skills/scene.json',import.meta.url),'skills')
const projects=parseProjectCatalogue(json('assets/project-hallway/projects.json'))
const vector=(value: unknown,path: string): Vec3=>{
  const values=listValue(value,path,numberValue)
  assert.equal(values.length,3,`${path}: expected XYZ`)
  const [x,y,z]=values
  assert.ok(x!==undefined&&y!==undefined&&z!==undefined)
  return [x,y,z]
}
const cardMetadata=(value: unknown,path: string): CardMetadata=>{
  const card=objectValue(value,path)
  return {center:vector(card.center,`${path}.center`),normal:vector(card.normal,`${path}.normal`),right:vector(card.right,`${path}.right`),
    width:numberValue(card.width,`${path}.width`),height:numberValue(card.height,`${path}.height`),
    ...(card.frontDepth===undefined?{}:{frontDepth:numberValue(card.frontDepth,`${path}.frontDepth`)})}
}
const exhibitRecords=listValue(manifest.exhibits,'skills manifest.exhibits',objectValue)
const cards=exhibitRecords.filter(entry=>entry.kind==='skill').map((entry,index)=>({
  ...entry,id:stringValue(entry.id,`card ${index}.id`),title:stringValue(entry.title,`card ${index}.title`),
  displayItems:listValue(entry.displayItems,`card ${index}.displayItems`,stringValue),
  items:listValue(entry.items,`card ${index}.items`,stringValue),catalogueSections:parseCaseSections(entry.catalogueSections,`card ${index}.catalogueSections`),
  contentStatus:stringValue(entry.contentStatus,`card ${index}.contentStatus`),card:cardMetadata(entry.card,`card ${index}.card`),
  position:vector(entry.position,`card ${index}.position`)
}))
const microservices=cards.find(entry=>entry.title==='Microservices')
assert.ok(microservices)
assert.equal(microservices.displayItems.length,4)
assert.ok(!/kafka|gateways?/i.test(JSON.stringify(microservices)),'Removed tools must not appear in the Microservices board or details')
assert.deepEqual(source.source,['src/data/portfolio.json','docs/project-catalogue.md'])
assert.equal(source.profileSourceHash,createHash('sha256').update(file('src/data/portfolio.json')).digest('hex'))
assert.equal(source.projectSourceHash,createHash('sha256').update(file('assets/project-hallway/projects.json')).digest('hex'))
assert.equal(cards.length,9)
assert.equal(listValue(manifest.actors,'skills manifest.actors',objectValue).length,90)
assert.equal(manifest.frameEnd,959)
assert.equal(manifest.channelStride,12)
const navigation=objectValue(manifest.navigation,'skills manifest.navigation')
assert.equal(objectValue(navigation.route,'skills manifest.navigation.route').frameEnd,2940)
assert.equal(navigation.animationFollowsWalk,false)
assert.equal(exhibitRecords.find(entry=>entry.id==='atat')?.title,'AT-AT walker')
const cameraRecords=objectValue(manifest.cameras,'skills manifest.cameras')
assert.ok(cameraRecords.atat)
const preserved=objectValue(json('assets/skills-gallery/skill-content-verification.json'),'skill-content verification')
assert.equal(preserved.architectureSculptureVisitorsAndRoutePreserved,true)
const journey=journeyFile(new URL('../public/models/journey.json',import.meta.url))
// Build the camera-fit fixture from validated native anchors. This verifier
// needs the room-to-cabin transform, not loaded geometry/animation/textures.
const rotation=new Quaternion().setFromAxisAngle(new Vector3(0,0,1),Math.PI)
const alignment={rotation,position:new Vector3().fromArray(vector(journey.elevatorOffset,'journey elevatorOffset'))
  .sub(new Vector3().fromArray(vector(manifest.entranceAnchor,'skills entranceAnchor')).applyQuaternion(rotation))}
let fits=0
for (const value of listValue(source.entries,'skills source.entries',objectValue)) {
  const entry={id:stringValue(value.id,'skill.id'),title:stringValue(value.title,'skill.title'),
    items:listValue(value.items,'skill.items',stringValue),displayItems:listValue(value.displayItems,'skill.displayItems',stringValue),
    profileOnly:listValue(value.profileOnly,'skill.profileOnly',stringValue),evidenceProjectIds:listValue(value.evidenceProjectIds,'skill.evidenceProjectIds',stringValue),
    catalogueSections:parseCaseSections(value.catalogueSections,'skill.catalogueSections'),
    url:value.url===null?null:stringValue(value.url,'skill.url'),
    repositories:listValue(value.repositories,'skill.repositories',(value,path)=>({url:stringValue(objectValue(value,path).url,`${path}.url`)})),
    siteLinks:listValue(value.siteLinks,'skill.siteLinks',(value,path)=>{
      const site=objectValue(value,path)
      return {url:stringValue(site.url,`${path}.url`),label:stringValue(site.label,`${path}.label`)}
    })}
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
