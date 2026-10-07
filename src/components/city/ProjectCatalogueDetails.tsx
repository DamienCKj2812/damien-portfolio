import type { ReactNode } from 'react'
import type { CaseSection, PublicCaseContent } from '../../types/portfolio'
import { isPublicLink, publicMarkdown, publicCaseSections } from '../../data/publicLinks'

export interface ProjectCatalogueContentProps { section: CaseSection; numberedRows?: boolean }
export interface ProjectCatalogueDetailsProps { project: PublicCaseContent }
export interface CatalogueSectionProps { section: CaseSection }

type MarkdownBlock =
  | { type: 'code'; text: string }
  | { type: 'paragraph'; text: string }
  | { type: 'table'; rows: string[][] }
  | { type: 'ordered'; items: string[] }
  | { type: 'list'; items: string[] }

function inline(text: string): ReactNode[] {
  return text.split(/(\[[^\]]+\]\([^)]+\)|\*\*[^*]+\*\*|`[^`]+`)/g).map((part,index) => {
    const link = part.match(/^\[([^\]]+)\]\(([^)]+)\)$/)
    if (link && link[1] !== undefined && link[2] !== undefined) return isPublicLink(link[2]) ? <a key={index} href={link[2]} target={/^https?:/.test(link[2])?'_blank':undefined} rel={/^https?:/.test(link[2])?'noreferrer':undefined}>{inline(link[1])}</a> : <span key={index}>{inline(link[1])}</span>
    if (part.startsWith('**') && part.endsWith('**')) return <strong key={index}>{part.slice(2,-2)}</strong>
    if (part.startsWith('`') && part.endsWith('`')) return <code key={index}>{part.slice(1,-1)}</code>
    return part
  })
}

function markdownBlocks(markdown: string): MarkdownBlock[] {
  const lines = markdown.split('\n'), blocks: MarkdownBlock[] = []
  const lineAt = (index: number) => lines[index] ?? ''
  let i = 0
  const startsBlock = (line: string) => /^```|^\||^[-*] |^\d+\. /.test(line)
  while (i < lines.length) {
    if (!lineAt(i).trim()) { i++;continue }
    if (lineAt(i).startsWith('```')) {
      i++
      const code = []
      while (i < lines.length && !lineAt(i).startsWith('```')) code.push(lineAt(i++))
      i++
      blocks.push({type:'code',text:code.join('\n')})
    } else if (lineAt(i).startsWith('|')) {
      const rows = []
      while (i < lines.length && lineAt(i).startsWith('|')) {
        const cells = lineAt(i++).split('|').slice(1,-1).map(cell => cell.trim())
        if (!cells.every(cell => /^[-: ]+$/.test(cell))) rows.push(cells)
      }
      blocks.push({type:'table',rows})
    } else if (/^[-*] |^\d+\. /.test(lineAt(i))) {
      const ordered = /^\d+\. /.test(lineAt(i)), items = []
      while (i < lines.length && /^[-*] |^\d+\. /.test(lineAt(i))) items.push(lineAt(i++).replace(/^([-*]|\d+\.) /,''))
      blocks.push({type:ordered?'ordered':'list',items})
    } else {
      const paragraph = []
      while (i < lines.length && lineAt(i).trim() && !startsBlock(lineAt(i))) paragraph.push(lineAt(i++))
      blocks.push({type:'paragraph',text:paragraph.join(' ')})
    }
  }
  return blocks
}

export function ProjectCatalogueContent({ section, numberedRows=false }: ProjectCatalogueContentProps) {
  return <div className="project-catalogue-content">{markdownBlocks(publicMarkdown(section.markdown,/^Links(?:\s|$)/i.test(section.heading))).map((block,index) => {
      if (block.type==='code') return <pre key={index}><code>{block.text}</code></pre>
      if (block.type==='table') return <div className="project-catalogue-table" key={index}><table>
        <thead><tr>{block.rows[0]?.map((cell,i)=><th key={i}>{inline(cell)}</th>)}</tr></thead>
        <tbody>{block.rows.slice(1).map((row,i)=><tr key={i}>{row.map((cell,j)=><td key={j}>{inline(cell)}</td>)}</tr>)}</tbody>
      </table></div>
      if (block.type==='list'||block.type==='ordered') {
        if (numberedRows) return <div className="project-case-rows" key={index}>{block.items.map((item,i)=>{
          const parts=item.match(/^\*\*([^*]+)\*\*\s*(.*)$/)
          return <div className="project-case-row" key={i}><span className="project-case-row-number">{String(i+1).padStart(2,'0')}</span><div>{parts && parts[1] !== undefined && parts[2] !== undefined?<><span className="project-case-row-title">{inline(parts[1].replace(/:$/,''))}</span><span className="project-case-row-body">{inline(parts[2])}</span></>:<span className="project-case-row-body">{inline(item)}</span>}</div></div>
        })}</div>
        const List = block.type==='ordered'?'ol':'ul'
        return <List key={index}>{block.items.map((item,i)=><li key={i}>{inline(item)}</li>)}</List>
      }
      return <p key={index}>{inline(block.text)}</p>
    })}</div>
}

function CatalogueSection({ section }: CatalogueSectionProps) {
  return <details className="project-catalogue-section">
    <summary>{section.heading} <span aria-hidden="true">+</span></summary>
    <ProjectCatalogueContent section={section}/>
  </details>
}

export default function ProjectCatalogueDetails({ project }: ProjectCatalogueDetailsProps) {
  return <div className="project-catalogue-details">
    <p className="room-project-label">Reviewed catalogue · 6 October 2026</p>
    {publicCaseSections(project).filter(section=>section.heading!=='Overview').map(section=><CatalogueSection key={section.heading} section={section}/>)}
  </div>
}
