import visibility from './repository-visibility.json' with { type: 'json' }
import { listValue, objectValue, stringValue } from '../types/portfolio'
import type { CaseSection, PublicCaseContent } from '../types/portfolio'

const registry=objectValue(visibility,'repository visibility')
const repositories=new Set(listValue(registry.publicRepositories,'repository visibility.publicRepositories',stringValue))

export function isPublicLink(href: string | null | undefined): boolean {
  if (!href) return false
  let url
  try { url=new URL(href) } catch { return false }
  if (!['https:','http:','mailto:','tel:'].includes(url.protocol)) return false
  const host=url.hostname.toLowerCase(),parts=url.pathname.split('/').filter(Boolean)
  if (['gitlab.com','bitbucket.org'].includes(host)) return false
  if (['github.com','www.github.com','raw.githubusercontent.com','api.github.com'].includes(host)) {
    if (host==='api.github.com' && parts[0]==='repos') parts.shift()
    if (['github.com','www.github.com'].includes(host) && parts.length<2) return true
    return repositories.has(parts.slice(0,2).join('/').toLowerCase())
  }
  return true
}

export function publicMarkdown(markdown: string, hideSourceRows = false): string {
  return markdown.split('\n').filter(line=>!hideSourceRows || !/^\s*[-*]\s/.test(line) || ![...line.matchAll(/\[([^\]]+)\]\(([^)]+)\)/g)].some(match=>!isPublicLink(match[2])))
    .join('\n').replace(/\[([^\]]+)\]\(([^)]+)\)/g,(match: string,label: string,href: string)=>isPublicLink(href)?match:label)
}

export function publicCaseSections<T extends CaseSection>(project: PublicCaseContent, sections: T[]): T[]
export function publicCaseSections(project: PublicCaseContent): CaseSection[]
export function publicCaseSections(project: PublicCaseContent, sections = project.catalogueSections || []): CaseSection[] {
  const restricted=project.repositoryLinksRestricted || Array.isArray(project.repositories)&&!project.repositories.some(repo=>isPublicLink(repo.url))&&!isPublicLink(project.url)
  return sections.flatMap(section=>{
    const sources=/^Links(?:\s|$)/i.test(section.heading)
    let markdown=publicMarkdown(section.markdown,sources)
    if(sources&&restricted) {
      const sites=project.siteLinks || (project.liveUrl?[{url:project.liveUrl,label:project.liveLabel || 'Website'}]:[])
      markdown=[...new Map(sites.filter(site=>isPublicLink(site.url)).map(site=>[site.url,site])).values()].map(site=>`- [${site.label}](${site.url})`).join('\n')
    }
    return markdown.trim()?[{...section,markdown}]:[]
  })
}
