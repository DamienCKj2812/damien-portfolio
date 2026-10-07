// Generate the native/browser timeline from the same confirmed data as About.
import fs from 'node:fs'
import vm from 'node:vm'

const portfolioSource=fs.readFileSync(new URL('../../src/data/portfolio.js',import.meta.url),'utf8')
  .replace(/^import portraitAsset .*$/m,'const portraitAsset = {}')
  .replace('export const portfolio =','const portfolio =')
const portfolio=vm.runInNewContext(`${portfolioSource}\nportfolio`,{}, {timeout:1000})
const projects=JSON.parse(fs.readFileSync(new URL('../project-hallway/projects.json',import.meta.url))).projects
const bullet=items=>items.map(item=>`- ${item}`).join('\n')
const section=(heading,markdown)=>({heading,markdown})
const record=id=>portfolio.journey.items.find(item=>item.id===id)
const media=JSON.parse(fs.readFileSync(new URL('../media/manifest.json',import.meta.url))).files
const logos={
  'diploma-information-technology':{id:'apu',texture:'logos/apu-logo.png',source:media.apuLogo.source},
  'lyj-events-marketing':{id:'lyj',texture:'logos/lyj-logo.png',source:media.lyjLogo.source},
  'cos-great-trading':{id:'cos',texture:'logos/cos-logo.png',source:media.cosLogo.source},
}
const entries=[
  ['diploma-information-technology','DIPLOMA\nIN IT','mountains'],
  ['lyj-events-marketing','LYJ EVENTS\n& MARKETING','cube'],
  ['cos-great-trading','COS GREAT\nTRADING','graduation'],
  ['freelance-full-stack','FREELANCE\nDEVELOPMENT','buildings'],
  ['bachelors-computer-science','COMPUTER\nSCIENCE','gears'],
]
const milestones=entries.map(([id,cardTitle,icon],index)=>{
  const item=record(id)
  if(!item) throw new Error(`Missing confirmed timeline record: ${id}`)
  const education=item.category==='EDUCATION'
  const sections=[section('Overview',`${item.title}\n\n${item.organization}\n\n${item.description}`)]
  if(education) {
    sections.push(section('Qualification',item.title),section('Status and results',`${item.period}\n\n${item.description}`))
    if(id==='bachelors-computer-science') sections.push(section('Specialisation','Computer Science with a specialism in Data Analytics. Final results have been received; graduation is expected in June 2027.'))
  } else if(id==='freelance-full-stack') {
    for(const [projectId,title] of [['agent-property','MyRumawip'],['Aria','DWMLight / ANVA CMS'],['amplifii','Amplifii (Ampress)']]) {
      const project=projects.find(project=>project.id===projectId)
      const details=item.highlights.filter(text=>text.startsWith(title.split(' / ')[0])&&!text.includes('achievement:')).join('\n\n')
      sections.push(section(title,`${details}\n\n${project.overview}\n\n${bullet(project.tags)}`))
    }
    sections.push(section('Achievements',bullet(item.highlights.filter(text=>text.includes('achievement:')))))
    const websites=['agent-property','Aria','amplifii'].map(id=>projects.find(project=>project.id===id))
    sections.push(section('Links and source references',bullet([...websites.map(project=>`[${project.id==='agent-property'?'MyRumawip website':project.id==='Aria'?'DWMLight website':'Amplifii (Ampress) preview (unreleased)'}](${project.liveUrl})`),'[MyRumawip repository](https://github.com/DamienCKj2812/agent-limenghar-property)','[DWMLight website repository](https://github.com/maxscale-io/Aria)','[ANVA CMS repository](https://github.com/maxscale-io/anva-cms)'])))
  } else {
    sections.push(section('Responsibilities',bullet(item.highlights)))
    if(id==='cos-great-trading') {
      sections.push(section('AI knowledge-base workflow','Users build knowledge bases for their departments. The CRM uses retrieval-augmented generation (RAG), with Pinecone supporting retrieval to answer department-specific questions.'))
      sections.push(section('Technologies','Python · TypeScript · Express · MongoDB · Next.js · Pinecone · AI SDKs'))
    } else sections.push(section('Delivered interfaces',bullet(item.highlights.filter(text=>text.startsWith('Built user interfaces')))))
  }
  return {id,title:item.displayTitle || (education?(id==='diploma-information-technology'?'Diploma in Information Technology':'BSc Computer Science'):item.organization==='Freelance / Client projects'?'Freelance development':item.organization),
    cardTitle:item.cardTitle || cardTitle,...(item.cardHeading?{cardHeading:item.cardHeading,cardSpecialism:item.cardSpecialism}:{}),
    ...(logos[id]?{logo:logos[id]}:{}),caption:education?`${item.period.toUpperCase()} / CGPA ${item.description.match(/\d\.\d+/)[0]}`:item.period.toUpperCase(),
    icon,categoryLabel:education?'Education':'Experience',catalogueNumber:index+1,summary:item.title,
    metadata:[['Org.',item.organization],['Period',item.period],...(education?[['CGPA',item.description.match(/\d\.\d+/)[0]]]:[['Role',item.title]])],
    ...(id==='freelance-full-stack'?{repositoryLinksRestricted:true,siteLinks:['agent-property','Aria','amplifii'].map(id=>projects.find(project=>project.id===id)).map(project=>({url:project.liveUrl,label:project.id==='agent-property'?'MyRumawip website':project.id==='Aria'?'DWMLight website':'Amplifii (Ampress) preview (unreleased)'}))}:{}),catalogueSections:sections}
})
milestones.push({id:'current-focus',title:'Current focus',cardTitle:'BACKEND\n& BEYOND',caption:'OPEN TO JOBS / FREELANCE',icon:'globe',categoryLabel:'Current focus',catalogueNumber:6,
  summary:portfolio.about.profile.status,metadata:[['Focus',portfolio.about.profile.focus],['Based',portfolio.about.profile.location]],
  catalogueSections:[section('Overview',portfolio.about.description),section('Approach',portfolio.about.profile.approach),section('Currently learning',bullet(portfolio.skills.learning)),section('Interests',bullet(portfolio.about.profile.interests)),section('Contact',bullet(portfolio.contact.links.map(link=>`[${link.label}](${link.href})`)))]})
const content={title:'MY JOURNEY SO FAR',subtitle:'EDUCATION / EXPERIENCE\nBUILDING / LEARNING',description:'Confirmed education, employment, freelance projects and current focus from src/data/portfolio.js and the Level 03 project catalogue.',milestones}
fs.writeFileSync(new URL('milestones.json',import.meta.url),JSON.stringify(content,null,2)+'\n')
console.log(`PASS generated ${milestones.length} confirmed timeline entries`)
