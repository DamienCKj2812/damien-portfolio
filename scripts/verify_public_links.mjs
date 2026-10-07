import assert from 'node:assert/strict'
import fs from 'node:fs'
import { isPublicLink, publicMarkdown } from '../src/data/publicLinks.js'

const json=path=>JSON.parse(fs.readFileSync(new URL(`../${path}`,import.meta.url)))
const projects=json('public/models/rooms/projects/scene.json').projects
const expected=[
  ['agent-property','https://myrumawip.com/','public','Website'],
  ['Aria','https://dwmlight.com/en','public','Website'],
  ['amplifii','https://amplyfii.io/login?redirect=%2F','unreleased','Preview (unreleased)'],
]
for(const [id,url,status,label] of expected) {
  const project=projects.find(project=>project.id===id)
  assert.equal(project.liveUrl,url);assert.equal(project.liveStatus,status);assert.equal(project.liveLabel,label)
  assert.equal(project.url,null,`${id}: private/organization repository button must be absent`)
  assert.deepEqual(project.repositories,[])
  const sources=project.catalogueSections.find(section=>/^Links/.test(section.heading))
  assert.ok(sources)
  assert.equal(sources.markdown.split('\n').filter(Boolean).length,1,'Private/organization Sources must contain only the site link')
  assert.ok(!/Repository|PRODUCT\.md|AGENTS\.md|trustScore\.ts/i.test(sources.markdown),'Internal repository/file rows must be removed, not rendered as plain text')
}
const report=projects.find(project=>project.id==='report-automation')
assert.equal(report.liveStatus,'private')
assert.equal(report.liveUrl,undefined)
assert.equal(report.url,null)
assert.match(report.overview,/Tailscale.*not publicly accessible/)
assert.ok(!report.catalogueSections.some(section=>/^Links/.test(section.heading)),'Private project without a site should have no empty Sources section')
const ampress=projects.find(project=>project.id==='amplifii')
assert.equal(ampress.title,'AMPLYFII (Ampress)')
assert.equal(ampress.overview.split('\n')[0],'An influencer-marketing platform that helps teams manage creator partnerships and campaigns.')
assert.ok(!ampress.catalogueSections.some(section=>/technical|architecture|features/i.test(section.heading)), 'NDA-covered project must have general-purpose sections only')
assert.deepEqual(ampress.tags,['Influencer marketing','Product development','Team collaboration'])
const confidentialTerms=/React|TypeScript|Express|Supabase|PostgreSQL|Docker|PM2|FastAPI|API\b|AI\b|scor(?:e|ing)|WhatsApp|Instagram|incoming messages|orchestration|SSE\b|server-owned/i
assert.ok(!confidentialTerms.test(JSON.stringify(ampress)), 'NDA-covered project must not disclose implementation or detailed features')
const skills=json('public/models/rooms/skills/scene.json')
assert.ok(!/amplifii|amplyfii|ampress/i.test(JSON.stringify(skills)), 'Skills must not associate NDA-covered work with technical evidence')
const experience=json('public/models/rooms/experience/scene.json')
const timeline=experience.milestones || experience.exhibits
const freelance=timeline.find(entry=>entry.id==='freelance-full-stack')
const ndaSection=freelance.catalogueSections.find(section=>section.heading==='Amplifii (Ampress)')
assert.ok(ndaSection&&!confidentialTerms.test(ndaSection.markdown), 'Timeline must retain only general NDA-covered product/contribution copy')
assert.ok(isPublicLink('https://github.com/DamienCKj2812/ConcurrentProgrammingAssignment'))
assert.ok(isPublicLink('https://github.com/BaconCoding74/rust-gcs-ocs-assignment/tree/gcs-branch'))
for(const url of ['https://github.com/maxscale-io/Aria','https://github.com/jarvisCoorpr/amplifii','https://github.com/DamienCKj2812/report-automation','https://github.com/DamienCKj2812/unknown-new-repo']) {
  assert.equal(isPublicLink(url),false)
  assert.equal(publicMarkdown(`[Source](${url})`),'Source','Stale Markdown must not create a restricted href')
}
function audit(value,path) {
  if(typeof value==='string') {
    for(const url of value.match(/https?:\/\/[^\s<>()\[\]"'`]+/g)||[]) {
      if(/github\.com|githubusercontent\.com|gitlab\.com|bitbucket\.org/.test(url)) assert.ok(isPublicLink(url),`${path}: published restricted repository URL ${url}`)
    }
  } else if(Array.isArray(value)) value.forEach((item,index)=>audit(item,`${path}[${index}]`))
  else if(value&&typeof value==='object') for(const [key,item] of Object.entries(value)) audit(item,`${path}.${key}`)
}
for(const level of ['projects','skills','experience']) audit(json(`public/models/rooms/${level}/scene.json`),level)
console.log('PASS public sites, unreleased preview, private Tailscale status, verified-public repository policy and no restricted URLs in published room metadata')
