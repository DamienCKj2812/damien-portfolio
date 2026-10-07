import { isPublicLink, publicMarkdown, publicCaseSections } from '../../data/publicLinks.js'

function inline(text) {
  return text.split(/(\[[^\]]+\]\([^)]+\)|\*\*[^*]+\*\*|`[^`]+`)/g).map((part,index) => {
    const link = part.match(/^\[([^\]]+)\]\(([^)]+)\)$/)
    if (link) return isPublicLink(link[2]) ? <a key={index} href={link[2]} target={/^https?:/.test(link[2])?'_blank':undefined} rel={/^https?:/.test(link[2])?'noreferrer':undefined}>{inline(link[1])}</a> : <span key={index}>{inline(link[1])}</span>
    if (part.startsWith('**') && part.endsWith('**')) return <strong key={index}>{part.slice(2,-2)}</strong>
    if (part.startsWith('`') && part.endsWith('`')) return <code key={index}>{part.slice(1,-1)}</code>
    return part
  })
}

function markdownBlocks(markdown) {
  const lines = markdown.split('\n'), blocks = []
  let i = 0
  const startsBlock = line => /^```|^\||^[-*] |^\d+\. /.test(line)
  while (i < lines.length) {
    if (!lines[i].trim()) { i++;continue }
    if (lines[i].startsWith('```')) {
      i++
      const code = []
      while (i < lines.length && !lines[i].startsWith('```')) code.push(lines[i++])
      i++
      blocks.push({type:'code',text:code.join('\n')})
    } else if (lines[i].startsWith('|')) {
      const rows = []
      while (i < lines.length && lines[i].startsWith('|')) {
        const cells = lines[i++].split('|').slice(1,-1).map(cell => cell.trim())
        if (!cells.every(cell => /^[-: ]+$/.test(cell))) rows.push(cells)
      }
      blocks.push({type:'table',rows})
    } else if (/^[-*] |^\d+\. /.test(lines[i])) {
      const ordered = /^\d+\. /.test(lines[i]), items = []
      while (i < lines.length && /^[-*] |^\d+\. /.test(lines[i])) items.push(lines[i++].replace(/^([-*]|\d+\.) /,''))
      blocks.push({type:ordered?'ordered':'list',items})
    } else {
      const paragraph = []
      while (i < lines.length && lines[i].trim() && !startsBlock(lines[i])) paragraph.push(lines[i++])
      blocks.push({type:'paragraph',text:paragraph.join(' ')})
    }
  }
  return blocks
}

export function ProjectCatalogueContent({ section, numberedRows=false }) {
  return <div className="project-catalogue-content">{markdownBlocks(publicMarkdown(section.markdown,/^Links(?:\s|$)/i.test(section.heading))).map((block,index) => {
      if (block.type==='code') return <pre key={index}><code>{block.text}</code></pre>
      if (block.type==='table') return <div className="project-catalogue-table" key={index}><table>
        <thead><tr>{block.rows[0].map((cell,i)=><th key={i}>{inline(cell)}</th>)}</tr></thead>
        <tbody>{block.rows.slice(1).map((row,i)=><tr key={i}>{row.map((cell,j)=><td key={j}>{inline(cell)}</td>)}</tr>)}</tbody>
      </table></div>
      if (block.type==='list'||block.type==='ordered') {
        if (numberedRows) return <div className="project-case-rows" key={index}>{block.items.map((item,i)=>{
          const parts=item.match(/^\*\*([^*]+)\*\*\s*(.*)$/)
          return <div className="project-case-row" key={i}><span className="project-case-row-number">{String(i+1).padStart(2,'0')}</span><div>{parts?<><span className="project-case-row-title">{inline(parts[1].replace(/:$/,''))}</span><span className="project-case-row-body">{inline(parts[2])}</span></>:<span className="project-case-row-body">{inline(item)}</span>}</div></div>
        })}</div>
        const List = block.type==='ordered'?'ol':'ul'
        return <List key={index}>{block.items.map((item,i)=><li key={i}>{inline(item)}</li>)}</List>
      }
      return <p key={index}>{inline(block.text)}</p>
    })}</div>
}

function CatalogueSection({ section }) {
  return <details className="project-catalogue-section">
    <summary>{section.heading} <span aria-hidden="true">+</span></summary>
    <ProjectCatalogueContent section={section}/>
  </details>
}

export default function ProjectCatalogueDetails({ project }) {
  return <div className="project-catalogue-details">
    <p className="room-project-label">Reviewed catalogue · 6 October 2026</p>
    {publicCaseSections(project).filter(section=>section.heading!=='Overview').map(section=><CatalogueSection key={section.heading} section={section}/>)}
  </div>
}
