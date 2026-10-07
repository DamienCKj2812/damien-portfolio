import assert from 'node:assert/strict'
import { journeyFile, sceneFile } from './node_json.mts'
import { PerspectiveCamera, Vector3 } from 'three'
import { createRoomAlignment } from '../src/components/city/roomJourney.ts'
import { createProjectCardFocus } from '../src/components/city/projectCardFocus.ts'

const manifest=sceneFile(new URL('../public/models/rooms/projects/scene.json',import.meta.url),'projects')
const journey=journeyFile(new URL('../public/models/journey.json',import.meta.url))
const alignment=createRoomAlignment({manifest},journey)
const sizes=[{width:1440,height:900},{width:1280,height:720},{width:1024,height:768},{width:938,height:986},{width:390,height:844},{width:360,height:740},{width:844,height:390}]
let count=0
for (const project of manifest.projects) {
  assert.ok(project.card,'Exported authored card bounds are required')
  assert.ok(project.video?project.card.width>4&&project.card.height>2.5:project.card.width>2&&project.card.height>3)
  assert.ok(project.card.right)
  const normal=new Vector3().fromArray(project.card.normal),right=new Vector3().fromArray(project.card.right)
  assert.ok(Math.abs(normal.y+Math.sin(45*Math.PI/180))<1e-6,'Project board must angle 45 degrees toward approaching visitors')
  assert.ok(Math.abs(normal.dot(right))<1e-6,'Authored card right/normal axes must remain orthogonal')
  for (const size of sizes) for (const exploring of [false,true]) {
    const pose=createProjectCardFocus(project,alignment,size,exploring)
    const camera=new PerspectiveCamera(pose.displayFov,size.width/size.height,.01,350)
    camera.position.copy(pose.position);camera.quaternion.copy(pose.quaternion)
    camera.setViewOffset(size.width,size.height,pose.offsetX,pose.offsetY,size.width,size.height)
    camera.updateMatrixWorld()
    for (const corner of pose.corners) {
      const projected=corner.clone().project(camera)
      const x=(projected.x+1)*size.width/2,y=(1-projected.y)*size.height/2
      assert.ok(projected.z>-1&&projected.z<1)
      assert.ok(x>=pose.rect.left-.01&&x<=pose.rect.right+.01&&y>=pose.rect.top-.01&&y<=pose.rect.bottom+.01,`${project.id} ${size.width}×${size.height} explore=${exploring}: clipped card corner ${x},${y}`)
    }
    count++
  }
}
console.log(`PASS ${count} full-card fits: all exhibits, both wall facings, desktop/portrait/mobile/landscape and Explore layout`)
