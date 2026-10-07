import assert from 'node:assert/strict'
import { preview, createServer } from 'vite'
import { execFileSync } from 'node:child_process'
import { chromium, chromeExecutable, installBrowserHelpers } from './browser_tools.mts'
import type { Locator, Page, ViewportSize } from 'playwright'
import { sceneFile } from './node_json.mts'
const videoProjects=sceneFile(new URL('../public/models/rooms/projects/scene.json',import.meta.url),'projects').projects
const approachY=(id: string)=>{const project=videoProjects.find(project=>project.id===id);assert.ok(project);return project.position[1]-Math.abs(project.position[0])}
const server=process.env.VIDEO_TEST_DEV?await createServer({server:{host:'127.0.0.1',port:5196,strictPort:true}}):await preview({preview:{host:'127.0.0.1',port:5196,strictPort:true}})
if('listen' in server) await server.listen()
const browser=await chromium.launch({executablePath:chromeExecutable,headless:true,args:['--no-sandbox','--enable-unsafe-swiftshader','--use-gl=angle','--use-angle=swiftshader']})
const errors: string[]=[]
declare global { interface Window { __rafCount: number; __testedVideoDock: HTMLElement; __maximumPlayingVideos: number; __maximumVisibleProjectPrompts: number } }
async function enter(viewport: ViewportSize,motion: 'reduce' | 'no-preference'='no-preference',sound=false) {
  const page=await browser.newPage({viewport,reducedMotion:motion})
  page.on('pageerror',error=>errors.push(error.message))
  await installBrowserHelpers(page,()=>{const raf=requestAnimationFrame.bind(window);window.__rafCount=0;window.requestAnimationFrame=callback=>{window.__rafCount++;return raf(callback)}})
  const requests: string[]=[];page.on('request',request=>{if(request.url().includes('/videos/'))requests.push(request.url())})
  await page.goto('http://127.0.0.1:5196/damien-portfolio/')
  await page.getByRole('button',{name:sound?/Enable sound/:'Continue muted'}).click()
  await page.locator('.city-stage[data-loaded="true"]').waitFor({timeout:120000})
  await page.getByRole('button',{name:/Choose a floor/}).click()
  await page.locator('.city-stage[data-elevator-loaded="true"]').waitFor({timeout:120000})
  const floor=page.getByRole('button',{name:/Select level 3:/});await floor.focus();await floor.press('Enter')
  await page.locator('.city-stage[data-elevator-status="arrived"][data-room="projects"]').waitFor({timeout:120000})
  return {page,requests,dock:page.locator('[data-project-video="agent-property"]')}
}
async function outside(dock: Locator) {
  const bounds=await dock.boundingBox(),board=await dock.evaluate((node: HTMLElement)=>({left:Number(node.dataset.boardLeft),right:Number(node.dataset.boardRight),top:Number(node.dataset.boardTop),bottom:Number(node.dataset.boardBottom)}))
  assert.ok(bounds)
  assert.ok(bounds.x+bounds.width<board.left||bounds.x>board.right||bounds.y+bounds.height<board.top||bounds.y>board.bottom,'Prompt/controls overlap the video board')
}
async function exclusiveNearestPrompt(page: Page) {
  const candidates=await page.locator('[data-project-video]').evaluateAll((nodes: HTMLElement[])=>nodes.map(node=>({
    id:node.dataset.projectVideo,eligible:node.dataset.promptEligible==='true',distance:Number(node.dataset.cameraDistance),visible:node.dataset.visible==='true',
  })))
  const eligible=candidates.filter(candidate=>candidate.eligible).sort((a,b)=>a.distance-b.distance)
  assert.ok(eligible.length>=2,'Regression view must contain two eligible project prompts')
  assert.deepEqual(candidates.filter(candidate=>candidate.visible).map(candidate=>candidate.id),[eligible[0]?.id],'Only the nearest eligible project may show its information prompt')
}
async function visiblePixels(page: Page,dock: Locator) {
  await dock.evaluate((node: HTMLElement)=>{window.__testedVideoDock=node})
  await page.waitForFunction(()=>window.__testedVideoDock.dataset.renderedSurface==='video')
  const region=await dock.evaluate((node: HTMLElement)=>({left:Number(node.dataset.boardLeft),right:Number(node.dataset.boardRight),top:Number(node.dataset.boardTop),bottom:Number(node.dataset.boardBottom)}))
  const png=await page.screenshot()
  const score=Number(execFileSync('python3',['-c',`import sys,json,io\nfrom PIL import Image\nr=json.loads(sys.argv[1]);im=Image.open(io.BytesIO(sys.stdin.buffer.read())).convert('RGB');w,h=im.size\nx0=max(0,int(r['left']+20));x1=min(w,int(r['right']-20));y0=max(0,int(r['top']+20));y1=min(h,int(r['bottom']-20))\np=list(im.crop((x0,y0,x1,y1)).resize((64,36)).getdata());print(sum(sum(c)/3>80 for c in p)/len(p))`,JSON.stringify(region)],{input:png}).toString())
  assert.ok(score>.15,`Playback is progressing but the rendered board is blank (${score})`)
}
try {
  const {page,requests,dock}=await enter({width:1440,height:900})
  await page.waitForFunction(()=>document.querySelector('canvas')!.dataset.roomFov)
  await page.evaluate(()=>{
    window.__maximumPlayingVideos=0
    window.__maximumVisibleProjectPrompts=0
    const check=()=>{
      const docks=[...document.querySelectorAll<HTMLElement>('[data-project-video]')]
      window.__maximumPlayingVideos=Math.max(window.__maximumPlayingVideos,docks.filter(node=>node.dataset.videoPaused==='false').length)
      window.__maximumVisibleProjectPrompts=Math.max(window.__maximumVisibleProjectPrompts,docks.filter(node=>node.dataset.visible==='true').length)
    }
    const observer=new MutationObserver(check)
    observer.observe(document.querySelector('.city-stage')!,{subtree:true,attributes:true,attributeFilter:['data-video-paused','data-visible']})
  })
  assert.ok(!requests.some(url=>url.includes('myrumawip-full')))
  const walkingFov=await page.locator('canvas').getAttribute('data-room-fov')
  await page.locator('#room-progress').evaluate((input,y)=>{Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value')!.set!.call(input,String(y));input.dispatchEvent(new Event('input',{bubbles:true}));input.dispatchEvent(new Event('change',{bubbles:true}))},approachY('agent-property'))
  await page.waitForFunction(y=>Math.abs(Number(document.querySelector<HTMLElement>('.city-stage')!.dataset.roomY)-y)<.02,approachY('agent-property'))
  await page.locator('.room-more-controls summary').click()
  await page.locator('.room-more-controls').getByRole('button',{name:'Look left',exact:true}).click()
  await page.getByRole('button',{name:'Hide menu'}).click()
  await dock.locator('.project-video-description').waitFor({state:'visible',timeout:20000})
  await page.waitForFunction(()=>document.querySelector<HTMLElement>('[data-project-video]')!.dataset.videoPaused==='false')
  await outside(dock)
  assert.equal(await page.locator('canvas').getAttribute('data-room-fov'),walkingFov,'Looking at a nearby video must not change the walking FOV')
  await visiblePixels(page,dock)
  assert.ok(!requests.some(url=>url.includes('myrumawip-full')))
  // A shallow view down the left wall brings the near and far video boards
  // into the centre together, reproducing the overlapping information boxes.
  await page.locator('#room-progress').evaluate(input=>{Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value')!.set!.call(input,'2');input.dispatchEvent(new Event('input',{bubbles:true}));input.dispatchEvent(new Event('change',{bubbles:true}))})
  await page.waitForFunction(()=>Math.abs(Number(document.querySelector<HTMLElement>('.city-stage')!.dataset.roomY)-2)<.02)
  await page.mouse.move(720,200);await page.mouse.down();await page.mouse.move(590,200,{steps:8});await page.mouse.up()
  for(const viewport of [{width:1440,height:900},{width:390,height:844}]) {
    await page.setViewportSize(viewport)
    await page.waitForFunction(()=>[...document.querySelectorAll<HTMLElement>('[data-project-video]')].filter(node=>node.dataset.promptEligible==='true').length>=2,undefined,{timeout:20000})
    await exclusiveNearestPrompt(page)
  }
  await page.emulateMedia({reducedMotion:'reduce'})
  await page.waitForFunction(()=>[...document.querySelectorAll<HTMLElement>('[data-project-video]')].every(node=>node.dataset.videoPaused!=='false'))
  await exclusiveNearestPrompt(page)
  assert.ok(await page.evaluate(()=>window.__maximumVisibleProjectPrompts)<=1,'Prompt handoffs must never expose two information boxes')
  await page.emulateMedia({reducedMotion:'no-preference'})
  await page.setViewportSize({width:1440,height:900})
  await page.mouse.move(590,200);await page.mouse.down();await page.mouse.move(720,200,{steps:8});await page.mouse.up()
  await page.locator('#room-progress').evaluate((input,y)=>{Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value')!.set!.call(input,String(y));input.dispatchEvent(new Event('input',{bubbles:true}));input.dispatchEvent(new Event('change',{bubbles:true}))},approachY('agent-property'))
  await page.waitForFunction(y=>Math.abs(Number(document.querySelector<HTMLElement>('.city-stage')!.dataset.roomY)-y)<.02,approachY('agent-property'))
  // Hand off between two previews on the same visit; never overlap decoders.
  await page.getByRole('button',{name:'Show menu'}).click()
  await page.locator('#room-progress').evaluate((input,y)=>{Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value')!.set!.call(input,String(y));input.dispatchEvent(new Event('input',{bubbles:true}));input.dispatchEvent(new Event('change',{bubbles:true}))},approachY('report-automation'))
  await page.waitForFunction(y=>Math.abs(Number(document.querySelector<HTMLElement>('.city-stage')!.dataset.roomY)-y)<.02,approachY('report-automation'))
  if(!await page.locator('.room-more-controls').evaluate((element: HTMLDetailsElement)=>element.open))await page.locator('.room-more-controls summary').click()
  for(let i=0;i<2;i++)await page.locator('.room-more-controls').getByRole('button',{name:'Look right',exact:true}).click()
  await page.waitForFunction(()=>document.querySelector<HTMLElement>('[data-project-video="report-automation"]')!.dataset.videoPaused==='false'&&document.querySelector<HTMLElement>('[data-project-video="agent-property"]')!.dataset.videoPaused==='true')
   // The arrival camera spring can leave sub-millidegree numerical residuals;
   // this still rejects any perceptible/automatic walking zoom.
   assert.ok(Math.abs(Number(await page.locator('canvas').getAttribute('data-room-fov'))-Number(walkingFov))<.001,'Walking past videos must keep the lens fixed')
  await page.locator('#room-progress').evaluate((input,y)=>{Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value')!.set!.call(input,String(y));input.dispatchEvent(new Event('input',{bubbles:true}));input.dispatchEvent(new Event('change',{bubbles:true}))},approachY('agent-property'))
  await page.waitForFunction(y=>Math.abs(Number(document.querySelector<HTMLElement>('.city-stage')!.dataset.roomY)-y)<.02,approachY('agent-property'))
  for(let i=0;i<2;i++)await page.locator('.room-more-controls').getByRole('button',{name:'Look left',exact:true}).click()
  await page.getByRole('button',{name:'Hide menu'}).click()
  await page.waitForFunction(()=>document.querySelector<HTMLElement>('[data-project-video="agent-property"]')!.dataset.videoPaused==='false'&&document.querySelector<HTMLElement>('[data-project-video="report-automation"]')!.dataset.videoPaused==='true')
  const center=await dock.evaluate((node: HTMLElement)=>({x:(Number(node.dataset.boardLeft)+Number(node.dataset.boardRight))/2,y:(Number(node.dataset.boardTop)+Number(node.dataset.boardBottom))/2}))
  await page.mouse.click(center.x,center.y)
  await page.locator('.city-stage[data-room-view="project"][data-card-focus-framed="true"]').waitFor({timeout:30000})
  await page.waitForFunction(()=>Number(document.querySelector<HTMLElement>('[data-project-video]')!.dataset.videoDuration)>40)
  await dock.getByRole('button',{name:'Pause video',exact:true}).waitFor({state:'visible'})
  await outside(dock)
  await visiblePixels(page,dock)
  assert.ok(requests.some(url=>url.includes('myrumawip-full')))
  await dock.getByRole('button',{name:'Pause video',exact:true}).click()
  await page.waitForFunction(()=>document.querySelector<HTMLElement>('[data-project-video]')!.dataset.videoPaused==='true')
  assert.ok(await page.evaluate(()=>window.__maximumPlayingVideos)<=1,'Never decode/play multiple project videos at the same time')
  assert.ok(await page.evaluate(()=>window.__maximumVisibleProjectPrompts)<=1,'Preview prompts and focused controls share one exclusive information dock')
  await page.locator('.city-stage[data-card-focus-settled="true"]').waitFor({timeout:30000})
  await page.evaluate(()=>document.dispatchEvent(new PointerEvent('pointerleave',{pointerType:'mouse'})))
  await page.waitForTimeout(500)
  const frames=await page.evaluate(()=>window.__rafCount);await page.waitForTimeout(700)
  assert.ok(await page.evaluate(()=>window.__rafCount)-frames<=2,'Paused video must settle the Canvas')
  await dock.getByRole('button',{name:'Play video',exact:true}).click()
  await page.getByRole('button',{name:'Open navigation guide'}).click()
  await page.locator('.portfolio-guide[open]').waitFor()
  await page.waitForFunction(()=>document.querySelector<HTMLElement>('[data-project-video]')!.dataset.videoPaused==='true')
  await page.keyboard.press('Escape');await page.locator('.portfolio-guide[open]').waitFor({state:'detached'})
  await page.waitForFunction(()=>document.querySelector<HTMLElement>('[data-project-video]')!.dataset.videoPaused==='false')
  await page.getByRole('button',{name:/Back to hallway/}).click()
  await page.locator('.city-stage[data-room-view="main"]').waitFor()
  await page.getByRole('button',{name:'Show menu'}).click()
  await page.locator('#room-progress').evaluate(input=>{Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value')!.set!.call(input,'30');input.dispatchEvent(new Event('input',{bubbles:true}));input.dispatchEvent(new Event('change',{bubbles:true}))})
  await page.waitForFunction(()=>document.querySelector<HTMLElement>('[data-project-video]')!.dataset.videoPaused==='true')
  await page.close()
  console.log('PASS exclusive camera-facing preview handoffs, fixed walking FOV, full native picks and pause/idle/modal/off-screen cleanup')
  for(const [viewport,sound] of [[{width:390,height:844},false],[{width:1440,height:900},true]] as const) {
    const visit=await enter(viewport,'reduce',sound)
    await visit.page.locator('.room-index-button').filter({hasText:'Agent Property'}).click()
    await visit.page.locator('.city-stage[data-card-focus-framed="true"]').waitFor({timeout:30000})
    await visit.dock.getByRole('button',{name:'Pause video',exact:true}).waitFor({state:'visible',timeout:20000})
    await outside(visit.dock)
    if(sound) {
      await visit.page.waitForFunction(()=>!(document.getElementById('background-music-audio') as HTMLAudioElement).paused)
      await visit.dock.getByRole('button',{name:'Sound off',exact:true}).click()
      await visit.dock.getByRole('button',{name:'Sound on',exact:true}).waitFor()
      await visit.page.waitForFunction(()=>(document.getElementById('background-music-audio') as HTMLAudioElement).paused)
      await visit.dock.getByRole('button',{name:'Sound on',exact:true}).click()
      await visit.page.waitForFunction(()=>!(document.getElementById('background-music-audio') as HTMLAudioElement).paused)
    }
    await visit.page.getByRole('button',{name:/Back to hallway/}).click();await visit.page.close()
  }
  assert.deepEqual(errors,[])
   for(const [id,y,direction,name,duration] of [['report-automation',approachY('report-automation'),'Look right','MyReport',40],['Aria',approachY('Aria'),'Look left','DWMLight',55],['fedora-dotfiles',approachY('fedora-dotfiles'),'Look left','Fedora Dotfiles',27]] as const) {
     const visit=await enter({width:1440,height:900})
     const target=visit.page.locator(`[data-project-video="${id}"]`)
     const project=videoProjects.find(project=>project.id===id)
     assert.ok(project?.video)
     const fullClip=project.video.full
     assert.ok(!visit.requests.some(url=>url.includes(fullClip)))
    await visit.page.locator('#room-progress').evaluate((input,y)=>{Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value')!.set!.call(input,String(y));input.dispatchEvent(new Event('input',{bubbles:true}));input.dispatchEvent(new Event('change',{bubbles:true}))},y)
    await visit.page.waitForFunction(y=>Math.abs(Number(document.querySelector<HTMLElement>('.city-stage')!.dataset.roomY)-y)<.02,y)
    await visit.page.locator('.room-more-controls summary').click()
    await visit.page.locator('.room-more-controls').getByRole('button',{name:direction,exact:true}).click()
    await visit.page.getByRole('button',{name:'Hide menu'}).click()
    await target.locator('.project-video-description').waitFor({state:'visible',timeout:20000})
    await target.evaluate((node: HTMLElement)=>{window.__testedVideoDock=node})
    await visit.page.waitForFunction(()=>window.__testedVideoDock.dataset.videoPaused==='false')
    assert.ok((await visit.page.locator('[data-project-video]').evaluateAll((nodes: HTMLElement[])=>nodes.filter(node=>node.dataset.videoPaused==='false').length))<=1,'Only the camera-facing preview should be playing')
     await outside(target);await visiblePixels(visit.page,target)
     if(id==='fedora-dotfiles') {
       assert.equal(project.video.preview,project.video.full)
       assert.equal(project.video.previewFallback,project.video.fullFallback)
       assert.equal(await target.getAttribute('data-video-mode'),'preview')
       assert.ok((await target.getAttribute('data-video-source'))?.endsWith(project.video.previewFallback || project.video.preview))
       const center=await target.evaluate((node: HTMLElement)=>({x:(Number(node.dataset.boardLeft)+Number(node.dataset.boardRight))/2,y:(Number(node.dataset.boardTop)+Number(node.dataset.boardBottom))/2}))
       await visit.page.mouse.click(center.x,center.y)
     } else await target.getByRole('button',{name:new RegExp(`Watch ${name}`)}).click()
    await visit.page.locator('.city-stage[data-room-view="project"][data-card-focus-framed="true"]').waitFor({timeout:30000})
    await visit.page.waitForFunction(duration=>Number(window.__testedVideoDock.dataset.videoDuration)>duration,duration)
     await target.getByRole('button',{name:'Pause video',exact:true}).waitFor({state:'visible'})
     if(id==='fedora-dotfiles') {
       assert.equal(await target.getAttribute('data-video-mode'),'full')
       assert.ok(Math.abs(Number(await target.getAttribute('data-video-duration'))-28.033333)<.1)
       assert.ok((await target.getAttribute('data-video-source'))?.match(/\/fedora-dotfiles(?:-h264)?\.mp4$/))
     }
    await outside(target);await visiblePixels(visit.page,target)
    const others=await visit.page.locator(`[data-project-video]:not([data-project-video="${id}"])`).evaluateAll((nodes: HTMLElement[])=>nodes.map(node=>node.dataset.videoPaused))
    assert.ok(others.every(paused=>paused!=='false'),'Other previews must pause while a walkthrough is focused')
    await visit.page.getByRole('button',{name:/Back to hallway/}).click();await visit.page.close()
    console.log(`PASS ${name}: correct preview/full files, visible pixels, outside prompt and other-player suspension`)
   }
   const fedoraMobile=await enter({width:390,height:844},'reduce')
   await fedoraMobile.page.locator('#room-progress').evaluate((input,y)=>{Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value')!.set!.call(input,String(y));input.dispatchEvent(new Event('input',{bubbles:true}));input.dispatchEvent(new Event('change',{bubbles:true}))},approachY('fedora-dotfiles'))
   await fedoraMobile.page.locator('.room-index-button').filter({hasText:'Fedora Dotfiles'}).click()
   const fedoraDock=fedoraMobile.page.locator('[data-project-video="fedora-dotfiles"]')
   await fedoraMobile.page.locator('.city-stage[data-card-focus-framed="true"]').waitFor({timeout:30000})
   await fedoraDock.getByRole('button',{name:'Pause video',exact:true}).waitFor({state:'visible',timeout:20000})
   await outside(fedoraDock);await visiblePixels(fedoraMobile.page,fedoraDock)
   await fedoraMobile.page.getByRole('button',{name:/Back to hallway/}).click()
   await fedoraMobile.page.close()
  assert.deepEqual(errors,[])
  console.log('PASS mobile/reduced-motion full playback and non-persistent video/background-music audio focus')
} finally {await browser.close();if('listen' in server)await server.close();else await new Promise<void>(resolve=>server.httpServer.close(()=>resolve()))}
