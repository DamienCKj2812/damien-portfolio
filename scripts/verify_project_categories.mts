import assert from 'node:assert/strict'
import fs from 'node:fs'
import { categoryContentFile, sceneFile } from './node_json.mts'
import { createHash } from 'node:crypto'
import { clampHallwayY, hallwayCategoryAt, hallwayMaxY } from '../src/components/city/hallwayCategories.ts'
import { publicCaseSections } from '../src/data/publicLinks.ts'

const content = categoryContentFile(new URL('../assets/project-hallway/projects.json', import.meta.url))
const manifest = sceneFile(new URL('../public/models/rooms/projects/scene.json', import.meta.url), 'projects')
const expected = {
  client: ['agent-property','report-automation','Aria','amplifii'],
  academic: ['fyp','ConcurrentProgrammingAssignment','DSTRAssignment','DTMAssignment','Java-Programming-G18-','OODJ','PFDAGroupAssignment','txsa-group-assignment','SDMGroupAssignment','rust-gcs-ocs-assignment'],
  personal: ['fedora-dotfiles','damien-portfolio'],
}
assert.deepEqual(content.categories.map(category => category.id), Object.keys(expected))
for (const [id, projects] of Object.entries(expected)) {
  assert.deepEqual(content.projects.filter(project => project.section === id).map(project => project.id), projects)
  assert.deepEqual(manifest.projects.filter(project => project.section === id).map(project => project.id), projects)
}
const fyp = manifest.projects.find(project => project.id === 'fyp')
assert.ok(fyp)
assert.equal(fyp.featured, true)
assert.deepEqual(fyp.repositories.map(repository => repository.id), ['logging-loading','logging-microservice-ui'])
const catalogue = fs.readFileSync(new URL('../docs/project-catalogue.md', import.meta.url))
assert.equal(content.catalogueSourceHash, createHash('sha256').update(catalogue).digest('hex'))
for (const project of manifest.projects) {
  assert.ok(project.overview && project.catalogueSections.length >= (project.id==='amplifii'?3:9))
  const source=content.projects.find(item=>item.id===project.id)
  assert.ok(source)
  assert.deepEqual(publicCaseSections(project),publicCaseSections(source),`Published catalogue content changed: ${project.id}`)
  for (const repository of project.repositories) assert.ok(catalogue.toString().includes(repository.url) || repository.url.includes('/tree/'))
}
assert.equal(manifest.projects.find(project => project.id==='DSTRAssignment')!.repositories.length,1)
assert.equal(manifest.projects.find(project => project.id==='txsa-group-assignment')!.repositories.length,1)
const navigation = manifest.navigation
const [client, academic, personal] = navigation.categories
assert.equal(client.door, undefined)
for (const category of [academic, personal]) {
  assert.ok(category.door)
  assert.ok(category.door.revealY < category.door.y && category.door.automatic)
  for (const role of ['categoryFrame','categoryCurtain','categoryDoorLabel']) assert.ok(manifest.groups.some(group => group.role === role && group.id === category.id))
  assert.ok(manifest.groups.some(group => group.role==='categoryCurtain' && group.id===category.id && group.kind==='points'))
  assert.ok(manifest.groups.some(group => group.role==='categoryCurtain' && group.id===category.id && group.kind==='solid' && group.opacity !== undefined && group.opacity < .05))
  assert.ok(!manifest.groups.some(group=>['categoryDoorLeft','categoryDoorRight'].includes(group.role ?? '')))
}
assert.equal(hallwayMaxY(navigation),navigation.maxY)
for (const category of [academic,personal]) {
  assert.ok(category.door)
  assert.equal(clampHallwayY(navigation, category.door.y+1),category.door.y+1,'Portal crossing must be uninterrupted')
  assert.equal(hallwayCategoryAt(navigation,category.door.y-1)!.id,category.door.previousCategory)
  assert.equal(hallwayCategoryAt(navigation,category.door.y+1)!.id,category.id)
}
assert.equal(clampHallwayY(navigation,navigation.maxY+10),navigation.maxY)
assert.equal(clampHallwayY(navigation,navigation.minY-10),navigation.minY)
assert.equal(hallwayCategoryAt(navigation, navigation.minY)!.id, 'client')
console.log('PASS 16 catalogue-backed exhibits and evidence, featured FYP, transparent automatic portals, uninterrupted crossing and reverse category labels')
