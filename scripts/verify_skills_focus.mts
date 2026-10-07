import assert from 'node:assert/strict'
import { resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { preview } from 'vite'
import { chromium, chromeExecutable, installBrowserHelpers, screenshotPath } from './browser_tools.mts'
import type { BrowserContext, Page } from 'playwright'
declare global { interface Window { __rafCount: number } }

const root=resolve(fileURLToPath(new URL('..',import.meta.url)))
const server=await preview({root,build:{outDir:process.env.VITE_TEST_OUT_DIR||'dist'},preview:{host:'127.0.0.1',port:5199,strictPort:true}})
let browser
try {
  browser=await chromium.launch({executablePath:chromeExecutable,headless:true,args:['--no-sandbox','--enable-unsafe-swiftshader','--use-gl=angle','--use-angle=swiftshader']})
  const errors: string[]=[]
  async function enter(context: BrowserContext) {
    await installBrowserHelpers(context,()=>{
      localStorage.setItem('damien-portfolio:audio-consent','muted')
      localStorage.setItem('damien-portfolio:background-music',JSON.stringify({enabled:false}))
      localStorage.setItem('damien-portfolio:sound-effects',JSON.stringify({enabled:false}))
      localStorage.setItem('damien-portfolio:room-menu:02','expanded')
      window.__rafCount=0;const raf=requestAnimationFrame.bind(window)
      window.requestAnimationFrame=callback=>{window.__rafCount++;return raf(callback)}
    })
    const page=await context.newPage()
    page.on('pageerror',error=>errors.push(error.message))
    await page.goto('http://127.0.0.1:5199/damien-portfolio/')
    await page.locator('.city-stage[data-loaded="true"]').waitFor({timeout:120000})
    await page.getByRole('button',{name:/Choose a floor/}).click()
    await page.locator('.city-stage[data-elevator-loaded="true"]').waitFor({timeout:120000})
    const floor=page.getByRole('button',{name:'Select level 2: Skills'})
    await floor.focus();await floor.press('Enter')
    await page.locator('.city-stage[data-elevator-status="arrived"][data-room="skills"]').waitFor({timeout:120000})
    await page.waitForFunction(()=>document.querySelector<HTMLElement>('.city-stage')!.dataset.roomWalkFrame!==undefined)
    return page
  }
  async function seek(page: Page,frame: number) {
    await page.locator('#room-progress').evaluate((input,value)=>{
      Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value')!.set!.call(input,String(value))
      input.dispatchEvent(new Event('input',{bubbles:true}));input.dispatchEvent(new Event('change',{bubbles:true}))
    },frame)
    await page.waitForFunction(value=>Math.abs(Number(document.querySelector<HTMLElement>('.city-stage')!.dataset.roomWalkFrame)-value)<1,frame)
  }
  const desktop=await browser.newContext({viewport:{width:1440,height:900},reducedMotion:'reduce'})
  const page=await enter(desktop)
  await page.getByRole('button',{name:'Next exhibit',exact:true}).click()
  await page.waitForFunction(()=>Math.abs(Number(document.querySelector<HTMLElement>('.city-stage')!.dataset.roomY)+.3)<.05)
  const savedStation=await page.locator('.city-stage').getAttribute('data-room-walk-frame')
  await seek(page,Number(savedStation))
  const more=page.locator('.room-more-controls')
  await more.locator('summary').click()
  await more.getByRole('button',{name:'Look left'}).click();await more.getByRole('button',{name:'Look left'}).click()
  await page.getByRole('button',{name:'Hide menu'}).click()
  const canvas=page.locator('canvas').first(),bounds=await canvas.boundingBox()
  assert.ok(bounds)
  await page.mouse.click(bounds.x+bounds.width/2,bounds.y+bounds.height/2)
  await page.locator('.city-stage[data-room-view="skill"][data-focus-skill="skill-01"][data-card-focus-framed="true"]').waitFor({timeout:30000})
  const nav=page.getByRole('navigation',{name:'Skill case-file sections'})
  assert.equal(await nav.locator('ol button').count(),8)
  await nav.getByRole('button',{name:/Project evidence/}).click()
  await page.getByRole('complementary',{name:'Skill description'}).getByText(/Agent Property/).first().waitFor()
  await page.screenshot({path:screenshotPath('skills-focus-browser.png')})
  await page.getByRole('button',{name:/Back to gallery/}).click()
  await page.locator('.city-stage[data-room-view="main"]').waitFor()
  assert.equal(await page.locator('.city-stage').getAttribute('data-room-walk-frame'),savedStation,'Focus must retain the player route')
  await page.getByRole('button',{name:'Show menu'}).click()
  assert.equal(await page.locator('.room-index-button').count(),10,'Nine real skill areas plus the AT-AT')
  for (let i=0;i<9;i++) {
    await page.locator('.room-index-button').nth(i).click()
    await page.locator('.city-stage[data-room-view="skill"][data-card-focus-framed="true"]').waitFor({timeout:30000})
    if (i===7) {
      assert.ok(!/Kafka|gateways?/i.test((await page.getByRole('complementary',{name:'Skill description'}).textContent())!))
      await page.screenshot({path:screenshotPath('microservices-without-kafka-gateways.png')})
    }
    assert.equal(await page.getByRole('navigation',{name:'Skill case-file sections'}).locator('ol button').count(),8)
    await page.getByRole('button',{name:/Back to gallery/}).click()
    await page.locator('.city-stage[data-room-view="main"]').waitFor()
  }
  await page.locator('.room-index-button').filter({hasText:'Data & AI'}).click()
  await page.getByRole('navigation',{name:'Skill case-file sections'}).getByRole('button',{name:/Learning & scope/}).click()
  await page.getByRole('complementary',{name:'Skill description'}).getByText(/ongoing learning areas/).waitFor()
  await page.keyboard.press('Escape')
  await page.locator('.city-stage[data-room-view="main"]').waitFor()
  await page.locator('.room-index-button').filter({hasText:'AT-AT walker'}).click()
  assert.equal(await page.locator('.city-stage').getAttribute('data-room-view'),'main','AT-AT retains its sculpture workflow')
  await page.getByRole('button',{name:'Open navigation guide'}).click()
  await page.locator('.portfolio-guide[open]').waitFor()
  await page.keyboard.press('Escape')
  await page.locator('.portfolio-guide[open]').waitFor({state:'detached'})
  console.log('PASS desktop: real card pick, all nine focus views, shared v2 panels/evidence, learning scope, saved route, AT-AT and guide')
  await desktop.close()

  const mobile=await browser.newContext({viewport:{width:390,height:844},isMobile:true,hasTouch:true,reducedMotion:'reduce'})
  const phone=await enter(mobile)
  await phone.locator('.room-index-button').filter({hasText:'Databases'}).tap()
  await phone.locator('.city-stage[data-room-view="skill"][data-card-focus-framed="true"]').waitFor({timeout:30000})
  await phone.locator('.project-mobile-dock button').nth(1).tap()
  await phone.getByRole('dialog',{name:'Chapters',exact:true}).getByRole('button',{name:/Project evidence/}).tap()
  await phone.getByRole('complementary',{name:'Skill description'}).getByText(/Pinecone-based RAG/).waitFor()
  await phone.screenshot({path:screenshotPath('skills-focus-mobile.png')})
  await phone.getByRole('button',{name:/Back to gallery/}).tap()
  await phone.locator('.city-stage[data-room-view="main"]').waitFor()
  console.log('PASS mobile: rear-wall card fit, evidence section and gallery return')
  await mobile.close()

  const normal=await browser.newContext({viewport:{width:1440,height:900},reducedMotion:'no-preference'})
  const animated=await enter(normal)
  await animated.getByRole('button',{name:'Start / resume tour',exact:true}).click()
  await animated.locator('.room-index-button').filter({hasText:'Backend & APIs'}).click()
  await animated.locator('.city-stage[data-room-view="skill"][data-card-focus-settled="true"][data-card-focus-framed="true"]').waitFor({timeout:30000})
  const saved=await animated.locator('.city-stage').getAttribute('data-room-walk-frame')
  const frame=await animated.locator('.city-stage').getAttribute('data-room-frame')
  await animated.waitForTimeout(500)
  const count=await animated.evaluate(()=>window.__rafCount)
  await animated.waitForTimeout(1000)
  assert.ok(await animated.evaluate(()=>window.__rafCount)-count<=2,'Focused skill must settle')
  assert.equal(await animated.locator('.city-stage').getAttribute('data-room-walk-frame'),saved)
  assert.equal(await animated.locator('.city-stage').getAttribute('data-room-frame'),frame,'Hidden visitors suspend')
  await animated.getByRole('button',{name:/Back to gallery/}).click()
  await animated.getByRole('button',{name:'Pause tour',exact:true}).waitFor()
  await animated.waitForFunction(value=>Number(document.querySelector<HTMLElement>('.city-stage')!.dataset.roomWalkFrame)>Number(value),saved)
  console.log('PASS normal motion: smooth full-card focus, route/visitor suspension, idle settling and original tour resume')
  await normal.close()
  assert.deepEqual(errors,[])
  console.log('PASS no browser runtime errors')
} finally {
  await browser?.close()
  await new Promise(done=>server.httpServer.close(done))
}
