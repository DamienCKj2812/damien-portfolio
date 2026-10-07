import assert from 'node:assert/strict'
import { fileURLToPath } from 'node:url'
import { resolve } from 'node:path'
import { preview } from 'vite'

const root=resolve(fileURLToPath(new URL('..',import.meta.url)))
const { chromium }=await import(process.env.PLAYWRIGHT_MODULE || '/tmp/opencode/browser-check/node_modules/playwright/index.mjs')
const server=await preview({root,preview:{host:'127.0.0.1',port:5198,strictPort:true}})
let browser
try {
  browser=await chromium.launch({executablePath:'/usr/bin/google-chrome',headless:true,args:['--no-sandbox','--enable-unsafe-swiftshader','--use-gl=angle','--use-angle=swiftshader']})
  const errors=[]
  const context=await browser.newContext({viewport:{width:1440,height:900},reducedMotion:'reduce'})
  await context.addInitScript(()=>{
    localStorage.setItem('damien-portfolio:audio-consent','muted')
    localStorage.setItem('damien-portfolio:background-music',JSON.stringify({enabled:false,volume:.99}))
    localStorage.setItem('damien-portfolio:sound-effects',JSON.stringify({enabled:false,volume:.99}))
    localStorage.setItem('damien-portfolio:room-menu:03','expanded')
  })
  const page=await context.newPage()
  page.on('pageerror',error=>errors.push(error.message))
  await page.goto('http://127.0.0.1:5198/damien-portfolio/')
  await page.locator('.city-stage[data-loaded="true"]').waitFor({timeout:120000})
  assert.equal(await page.locator('.background-music input').count(),0)
  assert.equal(await page.evaluate(()=>document.getElementById('background-music-audio').volume),.35)
  assert.equal(await page.evaluate(()=>JSON.parse(localStorage.getItem('damien-portfolio:sound-effects')).volume),.45)
  await page.getByRole('button',{name:'Play background music',exact:true}).click()
  await page.waitForFunction(()=>!document.getElementById('background-music-audio').paused)
  await page.getByRole('button',{name:'Pause background music',exact:true}).click()
  await page.getByRole('button',{name:'Enable interaction sound effects',exact:true}).click()
  await page.getByRole('button',{name:'Mute interaction sound effects',exact:true}).click()
  await page.getByRole('button',{name:/^Choose a floor/}).click()
  await page.locator('.city-stage[data-elevator-loaded="true"]').waitFor({timeout:120000})
  const floor=page.getByRole('button',{name:'Select level 3: Projects'})
  await floor.focus();await floor.press('Enter')
  await page.locator('.city-stage[data-elevator-status="arrived"][data-room="projects"]').waitFor({timeout:120000})
  await page.locator('.room-index-button').filter({hasText:'Agent Property'}).click()
  await page.locator('.city-stage[data-project-exploring="true"][data-card-focus-framed="true"]').waitFor({timeout:30000})
  const description=page.getByRole('complementary',{name:'Project description'})
  const nav=page.getByRole('navigation',{name:'Project case-file sections'})
  assert.equal(await nav.locator('ol button').count(),10)
  assert.equal(await page.getByRole('button',{name:'Previous project section'}).isDisabled(),true)
  await page.getByRole('button',{name:'Next project section'}).click()
  await description.locator('h3').filter({hasText:'Problem & purpose'}).waitFor()
  assert.equal(await page.getByRole('button',{name:'Previous project section'}).isDisabled(),false)
  await nav.getByRole('button',{name:/Key features/}).click()
  assert.ok(await description.locator('.project-case-row').count()>=4,'Features use numbered rows')
  assert.equal(await page.locator('.project-case-progress > span').evaluate(span=>span.style.height),'40%')
  await nav.getByRole('button',{name:/Architecture & workflow/}).click()
  await page.screenshot({path:resolve(root,'assets/project-hallway/project-detail-v2-browser.png')})
  for (const [selector,width,direction] of [['.project-case-sidefade-left',489.6,'90deg'],['.project-case-sidefade-right',432,'270deg']]) {
    const style=await page.locator(selector).evaluate(element=>({width:element.getBoundingClientRect().width,gradient:getComputedStyle(element).backgroundImage}))
    assert.ok(Math.abs(style.width-width)<1)
    assert.ok(style.gradient.includes(direction)&&style.gradient.includes('rgba'))
  }
  assert.equal(await description.locator('.project-case-scroll').evaluate(element=>getComputedStyle(element).overflowY),'auto')
  assert.match(await description.locator('.project-case-meta').textContent(),/Sole developer/)
  await nav.getByRole('button',{name:/Links/}).click()
  assert.equal(await page.getByRole('button',{name:'Next project section'}).isDisabled(),true)
  await page.keyboard.press('ArrowDown')
  assert.match(await description.locator('h3').textContent(),/10 \/ Links/,'Section navigation does not wrap at End')
  for (const viewport of [{width:938,height:986},{width:844,height:390},{width:390,height:844}]) {
    await page.setViewportSize(viewport)
    await page.waitForTimeout(350)
    assert.equal(await page.locator('.city-stage').getAttribute('data-card-focus-framed'),'true')
    const box=await description.boundingBox()
    assert.ok(box.x>=0&&box.y>=0&&box.x+box.width<=viewport.width+1&&box.y+box.height<=viewport.height+1)
    if (viewport.height<680) assert.equal(await description.locator('.project-case-meta').isVisible(),false)
    if (viewport.width<=600) {
      await page.getByRole('combobox',{name:'Project case-file section'}).selectOption('My role and contribution')
      await description.locator('h3').filter({hasText:'Your role'}).waitFor()
      await page.screenshot({path:resolve(root,'assets/project-hallway/project-detail-v2-mobile.png')})
    }
    assert.equal(await page.locator('.background-music input').count(),0)
  }
  await page.getByRole('button',{name:/Back to hallway/}).click()
  await page.locator('.city-stage[data-room-view="main"]').waitFor()
  assert.deepEqual(errors,[])
  await context.close()
  console.log('PASS v2 Explore: panel dimensions/fades, fixed header and scroll body, numbered rows, previous/next boundaries, progress rail, responsive full card, Back and fixed toggle-only audio')
} finally {
  await browser?.close()
  await new Promise(done=>server.httpServer.close(done))
}
