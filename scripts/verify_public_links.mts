import assert from 'node:assert/strict'
import { jsonFile, sceneFile } from './node_json.mts'
import { listValue, objectValue, parseCaseSections, stringValue } from '../src/types/portfolio.ts'
import { isPublicLink, publicMarkdown } from '../src/data/publicLinks.ts'
import flatProjects from '../src/data/projects2d.generated.json' with { type: 'json' }

const projects=sceneFile(new URL('../public/models/rooms/projects/scene.json',import.meta.url),'projects').projects
const expected=[
  ['agent-property','https://myrumawip.com/','public','Website'],
  ['Aria','https://dwmlight.com/en','public','Website'],
  ['amplifii','https://amplyfii.io/login?redirect=%2F','unreleased','Preview (unreleased)'],
]
for(const [id,url,status,label] of expected) {
  const project=projects.find(project=>project.id===id)
  assert.ok(project)
  assert.equal(project.liveUrl,url);assert.equal(project.liveStatus,status);assert.equal(project.liveLabel,label)
  assert.equal(project.url,null,`${id}: private/organization repository button must be absent`)
  assert.deepEqual(project.repositories,[])
  const sources=project.catalogueSections.find(section=>/^Links/.test(section.heading))
  assert.ok(sources)
  assert.equal(sources.markdown.split('\n').filter(Boolean).length,1,'Private/organization Sources must contain only the site link')
  assert.ok(!/Repository|PRODUCT\.md|AGENTS\.md|trustScore\.ts/i.test(sources.markdown),'Internal repository/file rows must be removed, not rendered as plain text')
}
const report=projects.find(project=>project.id==='report-automation')
assert.ok(report)
assert.equal(report.liveStatus,'private')
assert.equal(report.liveUrl,undefined)
assert.equal(report.url,null)
assert.match(report.overview,/Tailscale.*not publicly accessible/)
assert.ok(!report.catalogueSections.some(section=>/^Links/.test(section.heading)),'Private project without a site should have no empty Sources section')
const ampress=projects.find(project=>project.id==='amplifii')
assert.ok(ampress)
assert.equal(ampress.title,'AMPLYFII (Ampress)')
assert.equal(ampress.overview.split('\n')[0],'An influencer-marketing platform that helps teams manage creator partnerships and campaigns.')
assert.ok(!ampress.catalogueSections.some(section=>/technical|architecture|features/i.test(section.heading)), 'NDA-covered project must have general-purpose sections only')
assert.deepEqual(ampress.tags,['Influencer marketing','Product development','Team collaboration'])
const confidentialTerms=/React|TypeScript|Express|Supabase|PostgreSQL|Docker|PM2|FastAPI|API\b|AI\b|scor(?:e|ing)|WhatsApp|Instagram|incoming messages|orchestration|SSE\b|server-owned/i
assert.ok(!confidentialTerms.test(JSON.stringify(ampress)), 'NDA-covered project must not disclose implementation or detailed features')
const skills=sceneFile(new URL('../public/models/rooms/skills/scene.json',import.meta.url),'skills')
assert.ok(!/amplifii|amplyfii|ampress/i.test(JSON.stringify(skills)), 'Skills must not associate NDA-covered work with technical evidence')
const experience=sceneFile(new URL('../public/models/rooms/experience/scene.json',import.meta.url),'experience')
const experienceRaw=objectValue(jsonFile(new URL('../public/models/rooms/experience/scene.json',import.meta.url)), 'experience')
const timeline=experienceRaw.milestones
  ? listValue(experienceRaw.milestones, 'experience.milestones', (value,path)=>{
    const entry=objectValue(value,path)
    return {id:stringValue(entry.id,`${path}.id`),catalogueSections:parseCaseSections(entry.catalogueSections,`${path}.catalogueSections`)}
  })
  : experience.exhibits
const freelance=timeline.find(entry=>entry.id==='freelance-full-stack')
assert.ok(freelance?.catalogueSections)
const ndaSection=freelance.catalogueSections.find(section=>section.heading==='Amplifii (Ampress)')
assert.ok(ndaSection&&!confidentialTerms.test(ndaSection.markdown), 'Timeline must retain only general NDA-covered product/contribution copy')
assert.ok(isPublicLink('https://github.com/DamienCKj2812/ConcurrentProgrammingAssignment'))
assert.ok(isPublicLink('https://github.com/BaconCoding74/rust-gcs-ocs-assignment/tree/gcs-branch'))
for(const url of ['https://github.com/maxscale-io/Aria','https://github.com/jarvisCoorpr/amplifii','https://github.com/DamienCKj2812/report-automation','https://github.com/DamienCKj2812/unknown-new-repo']) {
  assert.equal(isPublicLink(url),false)
  assert.equal(publicMarkdown(`[Source](${url})`),'Source','Stale Markdown must not create a restricted href')
}
function audit(value: unknown,path: string) {
  if(typeof value==='string') {
    for(const url of value.match(/https?:\/\/[^\s<>()[\]"'`]+/g)||[]) {
      if(/github\.com|githubusercontent\.com|gitlab\.com|bitbucket\.org/.test(url)) assert.ok(isPublicLink(url),`${path}: published restricted repository URL ${url}`)
    }
  } else if(Array.isArray(value)) value.forEach((item,index)=>audit(item,`${path}[${index}]`))
  else if(value&&typeof value==='object') for(const [key,item] of Object.entries(value)) audit(item,`${path}.${key}`)
}
for(const level of ['projects','skills','experience'] as const) audit(sceneFile(new URL(`../public/models/rooms/${level}/scene.json`,import.meta.url),level),level)
assert.deepEqual(flatProjects.map(project=>project.id),projects.map(project=>project.id),'2D must include every published project in catalogue order')
for(const flat of flatProjects) {
  const source=projects.find(project=>project.id===flat.id)
  assert.ok(source)
  assert.equal(flat.overview,source.overview,'2D content must match the published catalogue')
  assert.deepEqual(flat.tags,source.tags)
  assert.deepEqual(flat.sections,source.catalogueSections)
  for(const link of flat.links) assert.ok(isPublicLink(link.href))
}
audit(flatProjects,'2D projects')
const flatAmpress=flatProjects.find(project=>project.id==='amplifii')
assert.ok(flatAmpress&&!confidentialTerms.test(JSON.stringify(flatAmpress)),'2D must preserve the NDA content boundary')
console.log('PASS public sites, unreleased preview, private Tailscale status, verified-public repository policy and aligned 2D/3D public project content')
