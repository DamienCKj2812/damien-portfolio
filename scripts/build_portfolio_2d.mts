import fs from 'node:fs'
import { objectValue, listValue, stringValue, parseCaseSections } from '../src/types/portfolio.ts'
import { isPublicLink, publicCaseSections } from '../src/data/publicLinks.ts'

// Consume the published, sanitized catalogue rather than internal repository evidence.
const scene = objectValue(JSON.parse(fs.readFileSync(new URL('../public/models/rooms/projects/scene.json', import.meta.url), 'utf8')) as unknown, 'projects scene')
const projects = listValue(scene.projects, 'projects', (value, path) => {
  const project = objectValue(value, path)
  const liveUrl = typeof project.liveUrl === 'string' && isPublicLink(project.liveUrl) ? project.liveUrl : null
  const repositories = listValue(project.repositories, `${path}.repositories`, (value, path) => {
    const repo = objectValue(value, path)
    return { label: stringValue(repo.title, `${path}.title`), href: stringValue(repo.url, `${path}.url`) }
  }).filter(repo => isPublicLink(repo.href))
  const sections = publicCaseSections({ catalogueSections: parseCaseSections(project.catalogueSections, `${path}.catalogueSections`) })
  return {
    id: stringValue(project.id, `${path}.id`), title: stringValue(project.title, `${path}.title`).replaceAll('\n', ' '),
    summary: stringValue(project.summary, `${path}.summary`).replaceAll('\n', ' '),
    section: stringValue(project.section, `${path}.section`), overview: stringValue(project.overview, `${path}.overview`),
    tags: listValue(project.tags, `${path}.tags`, stringValue), sections,
    status: typeof project.liveStatus === 'string' ? project.liveStatus : null,
    links: [...(liveUrl ? [{ label: project.liveStatus === 'unreleased' ? 'Preview (unreleased)' : 'Website', href: liveUrl }] : []), ...repositories],
  }
})
const output = JSON.stringify(projects, null, 2) + '\n'
const target = new URL('../src/data/projects2d.generated.json', import.meta.url)
if (!fs.existsSync(target) || fs.readFileSync(target, 'utf8') !== output) fs.writeFileSync(target, output)
console.log(`PASS 2D catalogue: ${projects.length} published projects, public links and reviewed case sections`)
