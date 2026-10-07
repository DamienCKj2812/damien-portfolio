import assert from 'node:assert/strict'
import fs from 'node:fs'
import { sceneFile } from './node_json.mts'
import type { Intersection } from 'three'
import { performance } from 'node:perf_hooks'
import { BufferGeometry, DoubleSide, InterleavedBuffer, InterleavedBufferAttribute, Mesh, MeshBasicMaterial, Raycaster, Vector3 } from 'three'
import { createVideoOccluder, videoIsOccluded } from '../src/components/city/videoOcclusion.ts'

const manifest=sceneFile(new URL('../public/models/rooms/projects/scene.json',import.meta.url),'projects')
const data=fs.readFileSync(new URL('../public/models/rooms/projects/geometry.bin',import.meta.url))
const buffer=data.buffer.slice(data.byteOffset,data.byteOffset+data.byteLength)
const material=new MeshBasicMaterial({side:DoubleSide}),plain=[],fast=[],geometries=[]
for(const group of manifest.groups.filter(group=>group.actor===0&&group.kind==='solid'&&(group.opacity ?? 0)>=1&&!(group.role==='project'&&group.id==='agent-property'))) {
  const geometry=new BufferGeometry()
  const interleaved=new InterleavedBuffer(new Float32Array(buffer,group.byteOffset,group.floatCount),group.stride)
  geometry.setAttribute('position',new InterleavedBufferAttribute(interleaved,3,0))
  geometry.computeBoundingSphere()
  const originalIndex=geometry.index
  plain.push(new Mesh(geometry,material));fast.push(createVideoOccluder(geometry,material));geometries.push(geometry)
  assert.equal(geometry.index,originalIndex,'Acceleration must not change render vertex/index order')
  const tree=geometry.boundsTree
  geometry.dispose()
  assert.equal(geometry.boundsTree,tree,'StrictMode GPU disposal must retain the valid CPU spatial index')
}
const project=manifest.projects.find(project=>project.id==='agent-property')
assert.ok(project?.card)
const target=new Vector3().fromArray(project.card.center)
const raycaster=new Raycaster(),hits: Intersection[]=[],rays=[]
for(let i=0;i<40;i++) {
  const origin=new Vector3(Math.sin(i*.2)*.15,1+i*.2,2.45)
  rays.push({origin,direction:target.clone().sub(origin).normalize(),far:target.distanceTo(origin)-.06})
}
const results=[]
const before=performance.now()
for(const ray of rays) {raycaster.set(ray.origin,ray.direction);raycaster.far=ray.far;results.push(raycaster.intersectObjects(plain,false).length>0)}
const slowMs=performance.now()-before,start=performance.now()
for(const [index,ray] of rays.entries()) {raycaster.set(ray.origin,ray.direction);raycaster.far=ray.far;assert.equal(videoIsOccluded(raycaster,fast,hits),results[index],'Fast visibility must agree with detailed raycasting')}
const fastMs=performance.now()-start
console.log(`PASS ${rays.length} detailed visibility comparisons, unchanged geometry and StrictMode-safe cache; standard ${slowMs.toFixed(1)} ms vs indexed ${fastMs.toFixed(1)} ms`)
for(const geometry of geometries)geometry.dispose()
material.dispose()
