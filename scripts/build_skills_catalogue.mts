import fs from 'node:fs'
import { createHash } from 'node:crypto'
import { parsePortfolio, parseProjectCatalogue } from '../src/types/portfolio.ts'

const read=(path: string)=>fs.readFileSync(new URL(`../${path}`,import.meta.url))
const profileSource=read('src/data/portfolio.json')
const profile=parsePortfolio(JSON.parse(profileSource.toString('utf8')) as unknown)
const projectSource=read('assets/project-hallway/projects.json')
const projects=parseProjectCatalogue(JSON.parse(projectSource.toString('utf8')) as unknown)
interface SkillConfig {
  key: string; rows: string[]; extra?: string[]; projects: string[]; profileOnly: string[]
  summary: string; application: string; workflow: string; decisions: string; scope: string
}
const configs: SkillConfig[]=[
  {key:'languages',rows:['TypeScript / JavaScript','Python / Go / R / SQL','Java / C++ / Rust','HTML / CSS','C / PHP'],extra:['Go','R','Rust'],projects:['agent-property','report-automation','fyp','DTMAssignment','PFDAGroupAssignment','ConcurrentProgrammingAssignment','DSTRAssignment','rust-gcs-ocs-assignment'],profileOnly:['C','PHP'],
    summary:'Typed web development, data tooling and academic programming.',
    application:'TypeScript and JavaScript connect public websites, dashboards and APIs. Python supports automation and data/ML tooling, Go appears in the FYP telemetry/API backend, and R supports academic analysis. Java, C++ and Rust appear in simulations and data-structure/control work.',
    workflow:'Start from the data model and interface contract. Use typed records for application boundaries, keep parsing/validation explicit, and choose concurrency or data structures according to the problem.',
    decisions:'TypeScript adds useful checks around API and UI data. SQL describes relational operations. Academic Java/C++ projects expose synchronization, ownership and algorithm mechanics rather than hiding them behind framework code.',
    scope:'C and PHP are listed in the completed About toolkit. The current 16-project catalogue does not present a dedicated C or PHP exhibit; they are profile-backed rather than attached to invented project evidence.'},
  {key:'frameworks',rows:['React / Next.js','Tailwind CSS / Radix UI','Vite / routing','Responsive UI / SEO','Spring Boot'],extra:['Three.js / React Three Fiber / Drei','Blender asset integration'],projects:['agent-property','report-automation','SDMGroupAssignment','damien-portfolio'],profileOnly:['Spring Boot'],
    summary:'Responsive interfaces, server-rendered websites and reusable UI.',
     application:'Agent Property and MyReport use Next.js. This portfolio uses React/Vite. The property catalogue documents CMS-managed SEO fields and structured-data support; the About profile confirms practical SEO knowledge.',
    workflow:'Separate presentation, application state and data fetching. Build reusable components and responsive controls, then verify keyboard, touch, loading and failure states.',
    decisions:'Next.js suits server-side CMS fetching and content revalidation. Vite supports interactive React applications. The portfolio uses a single demand-rendered Canvas, capped DPR and native Blender point/line exports to control ongoing work.',
    scope:'Spring Boot is self-reported in About, not demonstrated by a current catalogue entry. DWMLight frontend technology is system context; the confirmed contribution is CMS/backend and deployment, not sole frontend authorship.'},
  {key:'backend',rows:['Express / REST APIs','WebSockets / integration','FastAPI / Python','Authentication','Validation / workflows'],extra:['Go / chi / OTLP gRPC'],projects:['Aria','report-automation','fyp'],profileOnly:['FastAPI'],
    summary:'Backend-focused application development and integration.',
     application:'DWMLight/ANVA CMS uses Express services and structured content APIs. MyReport coordinates ingestion, reviewed extraction and customer workflows. FYP serves REST/WebSocket telemetry and anomaly data.',
    workflow:'Define input/output contracts, validate requests, separate routes from domain services and persistence, and preserve job or workflow state across client reconnects.',
    decisions:'Schema-driven validation supports configurable CMS content. Idempotent ingestion protects message history. Durable run state is preferable to request-lifetime ownership for long searches.',
     scope:'Backend development is the main focus stated in About. FastAPI is listed in the toolkit as a profile-backed skill.'},
  {key:'databases',rows:['PostgreSQL / Supabase','MongoDB / Redis','Pinecone / RAG','SQL / data modeling','MySQL'],extra:['Supabase / database RPCs','Redis Streams'],projects:['agent-property','report-automation','Aria','fyp'],profileOnly:['MySQL'],
    summary:'Relational, document, stream and retrieval-oriented data.',
    application:'Client projects use PostgreSQL/Supabase and MongoDB. FYP uses Redis Streams with PostgreSQL persistence when configured. The completed About experience at COS Great Trading confirms Pinecone-based RAG for departmental AI knowledge bases.',
    workflow:'Model domain records and ownership first. Use relational constraints/RPCs for coordinated writes, schema validation for flexible documents, stream consumers for background work and retrieval stores for knowledge context.',
    decisions:'Supabase is MyReport’s canonical store; Sheets is not its primary database. Redis decouples telemetry processing. Vector retrieval supplies relevant knowledge context rather than replacing transactional records.',
    scope:'MySQL is profile-backed. FYP metric/trace database insertion is configuration-dependent; a database connection does not imply every live telemetry sample is persisted.'},
  {key:'data-ai',rows:['Python / Pandas / NumPy','AI SDKs / RAG','ML / attribution','Locust / automation','AI / ML (learning)'],extra:['R / exploratory analysis','XGBoost / LOF','Locust / Toxiproxy','NLTK / TextBlob'],projects:['report-automation','fyp','DTMAssignment','PFDAGroupAssignment','txsa-group-assignment'],profileOnly:['Pandas / NumPy'],
    summary:'Data preparation, AI-assisted workflows and ongoing ML learning.',
    application:'MyReport separates proposed AI updates from confirmed customer facts. FYP compares hybrid anomaly detectors. DTM/PFDA/TXSA cover preprocessing, statistical/model experiments and tokenization. About confirms RAG and AI knowledge-base work at COS Great Trading.',
    workflow:'Preserve original data, validate structured outputs, prepare reproducible datasets and keep recorded offline evaluation separate from live operation. Use human review when model proposals change business records.',
     decisions:'The catalogue identifies XGBoost + LOF as the current FYP model. Attribution explains baseline deviations, not proven causal root causes.',
    scope:'About explicitly lists machine learning, artificial intelligence and 3D modeling as ongoing learning areas. The FYP notebook results are recorded offline evidence with injected anomaly labels, not a reproduced production benchmark.'},
  {key:'security',rows:['JWT / OAuth','Access control / permissions','RLS / validation','Reviewed data / audit history','Encryption / secure APIs'],projects:['Aria','report-automation'],profileOnly:['Encryption'],
    summary:'Validation, ownership and permission boundaries in applications.',
     application:'ANVA CMS checks authenticated content-operation permissions. MyReport uses owner-scoped database contracts, structured AI validation and calendar OAuth.',
    workflow:'Validate input at boundaries, enforce ownership in server/database operations and preserve audit history when updating customer or eligibility records.',
    decisions:'Keep privileged CMS tokens server-side. Separate immutable messages, proposed AI values and confirmed records. Treat client-side route selection as UI behavior rather than a complete authorization boundary.',
    scope:'Encryption and secure APIs are profile-listed skills. These project examples demonstrate implemented controls; the catalogue does not claim an independent security audit or guarantees of complete system security.'},
  {key:'devops',rows:['Docker / PM2','Git / GitHub Actions','Ansible / deployment','Observability','Bitbucket'],projects:['agent-property','Aria','fyp','damien-portfolio'],profileOnly:['Bitbucket'],
    summary:'Deployment, server operations and repeatable application delivery.',
     application:'Agent Property includes deployment/sync tooling, Docker, PM2 and Ansible. DWMLight’s confirmed work includes deployment/server operations. FYP uses a multi-service Compose topology.',
    workflow:'Separate application and environment configuration, use repeatable builds/deployments, define process boundaries and validate generated artifacts before consuming them.',
    decisions:'The portfolio checks native/browser geometry, routes and hashes before a Vite deployment. Operational configuration demonstrates a deployment design; it is not by itself evidence of live uptime or measured business outcomes.',
    scope:'Bitbucket is profile-backed. The catalogue distinguishes delivered code/configuration from unconfirmed production status and does not invent availability or performance measurements.'},
  {key:'microservices',rows:['Redis Streams / OTLP','REST / WebSockets','Metrics / traces','Queues / resilience'],projects:['fyp','report-automation'],profileOnly:[],
    summary:'Service boundaries, asynchronous processing and observability.',
     application:'FYP separates the Go telemetry receiver, stream consumers, Python inference and REST/WebSocket API. MyReport normalizes provider messages into an owner-scoped workflow.',
    workflow:'Define transport contracts, decouple ingestion from expensive processing, keep durable state for recoverable work and make operational events observable.',
     decisions:'FYP supports OTLP metrics and traces, not a complete implemented logs receiver. Redis Streams is its evidenced messaging path.',
    scope:'Resilience is listed in About. The current catalogue demonstrates Redis Streams and service integration, without claiming a proven fault-tolerance guarantee.'},
  {key:'linux',rows:['Fedora / Linux','KDE / Hyprland','Shell / servers','Ubuntu / Debian','Arch / Mint'],projects:['fedora-dotfiles','agent-property','Aria','fyp'],profileOnly:['Ubuntu','Debian','Arch','Mint'],
    summary:'Linux workstations, custom desktop tools and application servers.',
    application:'Fedora Dotfiles combines Stow, KDE/Hyprland, Quickshell/QML and a native PyQt6 sharing chooser. Client work includes server/deployment responsibilities, and FYP provides shell-driven load/chaos tooling.',
    workflow:'Version configuration, separate session/service responsibilities, preserve upstream protocols and clean up asynchronous previews or processes when they stop being useful.',
    decisions:'The sharing chooser customizes selection UI while the existing portal/PipeWire services retain permission and sharing responsibilities. Desktop customization integrates upstream tools rather than reimplementing Linux graphics.',
    scope:'About confirms an interest in installing/customizing distributions including Arch and Mint. Fedora has a dedicated catalogue project; the other named distributions are profile-backed, without invented clean-machine benchmarks.'},
]
const groups=profile.skills.groups
const entries=configs.map((config,index)=>{
  const group=groups.find(group=>group.id===config.key)
  if (!group) throw new Error(`Missing approved About skill group: ${config.key}`)
   // NDA-covered work must not imply any project-specific technical toolkit.
   const evidenceProjectIds=config.projects.filter(id=>id!=='amplifii')
   const evidence=evidenceProjectIds.map(id=>{
    const project=projects.find(project=>project.id===id)
    if (!project) throw new Error(`Missing catalogue evidence: ${id}`)
    return project
  })
  const evidenceText=evidence.map(project=>`- **${project.catalogueTitle || project.title.replaceAll('\n',' ')}:** ${project.overview}`).join('\n')
  const links=evidence.flatMap(project=>project.repositories || []).filter((repository,i,all)=>all.findIndex(item=>item.url===repository.url)===i)
  const websites=evidence.filter(project=>project.liveUrl).map(project=>`- [${project.id==='agent-property'?'MyRumawip':project.title.replaceAll('\n',' ')} ${project.liveStatus==='unreleased'?'preview (unreleased)':'website'}](${project.liveUrl})`).join('\n')
  const privateNotes=evidence.filter(project=>project.liveNote).map(project=>`${project.title}: ${project.liveNote}`).join('\n\n')
  const sections=[
    {heading:'Overview',markdown:`${config.summary}\n\n${profile.about.profile.approach}`},
    {heading:'Core toolkit',markdown:[...new Set([...group.items,...(config.extra||[])])].map(item=>`- ${item}`).join('\n')},
    {heading:'Applied in projects',markdown:`${config.application}\n\n${evidenceText}`},
    {heading:'Engineering workflow',markdown:config.workflow},
    {heading:'Technical decisions',markdown:config.decisions},
     {heading:'Collaboration and delivery',markdown:`The completed About profile identifies **${profile.about.profile.strengths.join(' and ')}** as strengths. Frontend work at LYJ Events & Marketing includes stakeholder collaboration, QA feedback and evolving requirements. DWMLight's confirmed contribution focuses on CMS/backend and deployment.`},
    {heading:'Learning and scope',markdown:config.scope},
    {heading:'Links and sources',markdown:`Project evidence comes from the completed project catalogue; broader toolkit claims come from the completed About profile.\n\n${links.map(repository=>`- [${repository.title}${repository.id==='Aria'?'':` / ${repository.id}`}](${repository.url})`).join('\n')}${websites?`\n\nWebsites and previews\n\n${websites}`:''}${privateNotes?`\n\n${privateNotes}`:''}`},
  ]
  const siteLinks=evidence.filter(project=>project.liveUrl).map(project=>({url:project.liveUrl,label:`${project.id==='agent-property'?'MyRumawip':project.title.replaceAll('\n',' ')} ${project.liveStatus==='unreleased'?'preview (unreleased)':'website'}`}))
  const namedSections=sections.map(section=>({...section,markdown:section.markdown.replace(/\bAMPLYFII\b(?!\s*\(Ampress\))/g,'AMPLYFII (Ampress)')}))
   return {id:`skill-${String(index+1).padStart(2,'0')}`,kind:'skill',number:index+1,catalogueNumber:index+1,title:group.title,section:'skills',category:'APPLIED SKILLS / '+group.title.toUpperCase(),summary:config.summary,focus:profile.about.profile.focus,items:[...new Set([...group.items,...(config.extra||[])])],displayItems:config.rows,profileOnly:config.profileOnly,evidenceProjectIds,url:links[0]?.url || null,repositories:links,siteLinks,catalogueSections:namedSections,contentStatus:'Approved About toolkit and project-catalogue evidence; profile-only/learning scope stated explicitly'}
})
const output={version:1,source:['src/data/portfolio.json','docs/project-catalogue.md'],profileSourceHash:createHash('sha256').update(profileSource).digest('hex'),projectSourceHash:createHash('sha256').update(projectSource).digest('hex'),description:profile.skills.description,learning:profile.skills.learning,entries}
fs.writeFileSync(new URL('../assets/skills-gallery/skills.json',import.meta.url),JSON.stringify(output,null,2)+'\n')
console.log(`SKILLS CATALOGUE: ${entries.length} approved areas / About toolkit, project evidence and qualified learning scope`)
