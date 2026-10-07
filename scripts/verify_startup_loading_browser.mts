import assert from 'node:assert/strict'
import { createServer, preview } from 'vite'
import { chromium, chromeExecutable, installBrowserHelpers, screenshotPath } from './browser_tools.mts'

declare global { interface Window { startupAudioContexts: number; startupHandoffTimes: {prepared: number; entered: number} } }

const dev=Boolean(process.env.STARTUP_TEST_DEV)
const server=dev?await createServer({server:{host:'127.0.0.1',port:0}}):await preview({preview:{host:'127.0.0.1',port:0}})
if(dev && 'listen' in server) await server.listen()
let browser
try {
  browser=await chromium.launch({executablePath:chromeExecutable,headless:true,args:['--no-sandbox','--enable-unsafe-swiftshader','--use-gl=angle','--use-angle=swiftshader']})
  const address=server.httpServer?.address()
  assert.ok(address && typeof address!=='string')
  const url=`http://127.0.0.1:${address.port}/damien-portfolio/`
  const context=await browser.newContext({viewport:{width:1440,height:900},reducedMotion:'reduce'})
  await installBrowserHelpers(context)
  const page=await context.newPage()
  const errors: string[]=[]
  page.on('pageerror',error=>errors.push(error.message))
  const requests: string[]=[]
  page.on('request',request=>requests.push(request.url()))
  let releaseRuntime!: () => void
  const runtimeGate=new Promise<void>(resolve=>{releaseRuntime=resolve})
  let releaseRoom!: () => void
  const roomGate=new Promise<void>(resolve=>{releaseRoom=resolve})
  await page.route(dev?'**/src/components/CityWalkthrough.tsx':'**/assets/CityWalkthrough-*.js',async route=>{await runtimeGate;await route.continue()})
  await page.route('**/models/rooms/experience/scene.json',async route=>{await roomGate;await route.continue()})
  await page.goto(url,{waitUntil:'domcontentloaded'})
  const loader=page.getByRole('region',{name:'Preparing portfolio'})
  await loader.waitFor()
  await loader.evaluate(element=>{element.setAttribute('data-instance','persistent')})
  assert.equal(await page.getByRole('dialog').count(),0,'Sound choice waits behind startup preparation')
  assert.equal(await loader.getAttribute('data-progress'),'0')
  await page.screenshot({path:screenshotPath('startup-loading-initial.png')})
  releaseRuntime()
  await page.locator('.city-stage[data-loaded="true"]').waitFor({timeout:120000})
  await loader.locator('[data-stage="experience"][data-state="loading"]').waitFor({timeout:120000})
  assert.equal(await loader.getAttribute('data-instance'),'persistent','Lazy runtime and asset loads share one uninterrupted loader')
  assert.equal(await loader.locator('[data-stage="experience"] span').last().textContent(),'Loading')
  assert.ok(Number(await loader.getAttribute('data-progress'))<100)
  assert.equal(await page.locator('.portfolio-scene').getAttribute('inert'),'')
  assert.equal(await page.evaluate(()=>(document.getElementById('background-music-audio') as HTMLAudioElement).paused),true,'Preloading is silent')
  assert.equal(await page.locator('.city-loading,.city-loading-shell').count(),0)
  for(const viewport of [{width:390,height:844},{width:320,height:568},{width:844,height:390}]) {
    await page.setViewportSize(viewport)
    for(const selector of ['header','.startup-summary','.startup-log']) {
      const bounds=await loader.locator(selector).boundingBox()
      assert.ok(bounds && bounds.x>=0 && bounds.y>=0 && bounds.x+bounds.width<=viewport.width+1 && bounds.y+bounds.height<=viewport.height+1,`Loader ${selector} fits ${viewport.width}×${viewport.height}`)
    }
    if(viewport.width===390) await page.screenshot({path:screenshotPath('startup-loading-mobile.png')})
  }
  await page.screenshot({path:screenshotPath('startup-loading-landscape.png')})
  await page.evaluate(()=>{
    window.startupHandoffTimes={prepared:0,entered:0}
    const observer=new MutationObserver(()=>{
      if(document.querySelector('.startup-loader[data-starting="true"]') && !window.startupHandoffTimes.prepared) window.startupHandoffTimes.prepared=performance.now()
      if(document.querySelector('.experience[data-startup-ready="true"]')) {window.startupHandoffTimes.entered=performance.now();observer.disconnect()}
    })
    observer.observe(document.body,{attributes:true,subtree:true,childList:true})
  })
  releaseRoom()
  await loader.locator('.startup-summary [role="status"]').filter({hasText:'Starting your journey…'}).waitFor({timeout:30000})
  assert.equal(await loader.getAttribute('data-progress'),'100')
  assert.equal(await page.getByRole('dialog').count(),0,'Sound choice stays deferred throughout the one-second handoff')
  await page.locator('.experience[data-startup-ready="true"]').waitFor({timeout:30000}).catch(async error=>{console.log(await loader.textContent(),errors);throw error})
  const handoff=await page.evaluate(()=>window.startupHandoffTimes)
  assert.ok(handoff.prepared>0 && handoff.entered-handoff.prepared>=950,'Completed loader remains visible for one additional second')
  assert.equal(await loader.count(),0)
  assert.equal(await page.locator('.city-stage').getAttribute('data-lobby-loaded'),'true')
  assert.equal(await page.locator('.city-stage').getAttribute('data-elevator-loaded'),'true')
  for(const room of ['about','skills','projects','experience']) assert.ok(requests.some(request=>request.includes(`/rooms/${room}/scene.json`)))
  assert.ok(requests.some(request=>request.includes('damien-original.png')))
  assert.ok(requests.some(request=>request.includes('myrumawip-poster.jpg')))
  assert.ok(!requests.some(request=>/videos\/.*\.mp4/.test(request)),'Walkthrough videos retain selective playback loading')
  await page.getByRole('dialog',{name:/ENTER WITH SOUND/i}).waitFor()
  await page.getByRole('button',{name:'Continue muted'}).click()
  await page.setViewportSize({width:1440,height:900})
  await page.screenshot({path:screenshotPath('startup-city-ready.png')})
  await page.getByRole('button',{name:/^Choose a floor/}).click()
  const packageCount=requests.filter(request=>/models\/.*\.(bin|json)/.test(request)).length
  for(const level of [1,2,3,4]) {
    const floor=page.getByRole('button',{name:new RegExp(`^Select level ${level}:`)})
    await floor.focus();await floor.press('Enter')
    await page.locator('.city-stage[data-elevator-status="arrived"][data-room-loaded="true"]').waitFor({timeout:120000})
    await page.locator('#city').focus();await page.keyboard.press('Home');await page.keyboard.press('PageUp')
    await page.getByRole('dialog',{name:'Return to elevator?'}).waitFor()
    await page.getByRole('button',{name:'Yes, return to elevator',exact:true}).click()
    await page.locator('.city-stage[data-elevator-status="idle"]').waitFor({timeout:30000})
  }
  assert.equal(requests.filter(request=>/models\/.*\.(bin|json)/.test(request)).length,packageCount,'Floor visits reuse startup-preloaded packages')
  assert.deepEqual(errors,[])
  await context.close()

  const retryContext=await browser.newContext({viewport:{width:390,height:844},reducedMotion:'reduce'})
  await installBrowserHelpers(retryContext,()=>{
    localStorage.setItem('damien-portfolio:audio-consent','enabled')
    localStorage.setItem('damien-portfolio:background-music',JSON.stringify({enabled:false,volume:.35}))
    localStorage.setItem('damien-portfolio:sound-effects',JSON.stringify({enabled:true,volume:.45}))
    window.startupAudioContexts=0
    const NativeContext=window.AudioContext
    window.AudioContext=new Proxy(NativeContext,{construct(target,args){window.startupAudioContexts++;return Reflect.construct(target,args)}})
  })
  const retryPage=await retryContext.newPage()
  let failCity=true
  await retryPage.route('**/models/city/geometry.bin*',async route=>{if(failCity)await route.fulfill({status:503,body:'temporarily unavailable'});else await route.continue()})
  await retryPage.goto(url)
  await retryPage.locator('.startup-loader[data-error="true"]').waitFor({timeout:120000})
  failCity=false
  await retryPage.getByRole('button',{name:'Retry loading ↻'}).click()
  assert.equal(await retryPage.evaluate(()=>window.startupAudioContexts),0,'Loader Retry stays silent even with remembered enabled effects')
  await retryPage.locator('.experience[data-startup-ready="true"]').waitFor({timeout:120000})
  await retryPage.reload()
  await retryPage.locator('.experience[data-startup-ready="true"]').waitFor({timeout:120000})
  assert.equal(await retryPage.locator('.startup-loader').count(),0,'Reload settles to the prepared city')
  await retryContext.close()

  const optionalContext=await browser.newContext({viewport:{width:390,height:844},reducedMotion:'reduce'})
  await installBrowserHelpers(optionalContext,()=>localStorage.setItem('damien-portfolio:audio-consent','muted'))
  const optionalPage=await optionalContext.newPage()
  let failProjects=true
  let releaseOptional!: () => void
  const optionalGate=new Promise<void>(resolve=>{releaseOptional=resolve})
  await optionalPage.route('**/models/rooms/experience/scene.json',async route=>{await optionalGate;await route.continue()})
  await optionalPage.route('**/models/rooms/projects/scene.json',async route=>{if(failProjects)await route.fulfill({status:503,body:'temporarily unavailable'});else await route.continue()})
  await optionalPage.route('**/media/audio/effects/*.mp3',route=>route.fulfill({status:503,body:'temporarily unavailable'}))
  await optionalPage.goto(url)
  await optionalPage.locator('[data-stage="projects"][data-state="unavailable"]').waitFor({timeout:120000})
  assert.equal(await optionalPage.locator('[data-stage="effects"]').getAttribute('data-state'),'unavailable','Failed optional audio is not falsely marked OK')
  releaseOptional()
  await optionalPage.locator('.experience[data-startup-ready="true"]').waitFor({timeout:120000})
  await optionalPage.getByRole('button',{name:/^Choose a floor/}).click()
  const projectFloor=optionalPage.getByRole('button',{name:/^Select level 3:/})
  await projectFloor.focus();await projectFloor.press('Enter')
  await optionalPage.getByRole('button',{name:'Retry room',exact:true}).waitFor({timeout:30000})
  failProjects=false
  await optionalPage.getByRole('button',{name:'Retry room',exact:true}).click()
  await optionalPage.locator('.city-stage[data-elevator-status="arrived"][data-room="projects"]').waitFor({timeout:120000})
  await optionalContext.close()
  console.log(`PASS startup ${dev?'StrictMode':'production'}: persistent loader, real delayed progress, responsive bounds, silent audio, prepared floor reuse, failure/Retry and reload`)
} finally {
  await browser?.close()
  if(dev && 'close' in server) await server.close()
  else await new Promise<void>(done=>server.httpServer?.close(()=>done()))
}
