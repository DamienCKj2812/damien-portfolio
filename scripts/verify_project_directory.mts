import assert from 'node:assert/strict'
import { journeyFile, sceneFile } from './node_json.mts'
import { chromium, chromeExecutable, installBrowserHelpers, screenshotPath } from './browser_tools.mts'
import { resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { preview } from 'vite'
import { PerspectiveCamera } from 'three'
import { createRoomAlignment } from '../src/components/city/roomJourney.ts'
import { createProjectCardFocus } from '../src/components/city/projectCardFocus.ts'

const root=resolve(fileURLToPath(new URL('..',import.meta.url)))
const manifest=sceneFile(resolve(root,'public/models/rooms/projects/scene.json'),'projects')
const directory=manifest.directory
assert.equal(directory.zoomOnly,true)
assert.equal(directory.projectorPosition,'above')
assert.ok(manifest.groups.some(group=>group.role==='directory'&&group.id==='directory'))
assert.equal(manifest.projects.length,16)
const alignment=createRoomAlignment({manifest},journeyFile(resolve(root,'public/models/journey.json')))
for (const size of [{width:1440,height:900},{width:938,height:986},{width:390,height:844},{width:844,height:390}]) {
  const pose=createProjectCardFocus(directory,alignment,size,false)
  const camera=new PerspectiveCamera(pose.displayFov,size.width/size.height,.01,350)
  camera.position.copy(pose.position);camera.quaternion.copy(pose.quaternion)
  camera.setViewOffset(size.width,size.height,pose.offsetX,pose.offsetY,size.width,size.height);camera.updateMatrixWorld()
  for (const corner of pose.corners) {
    const p=corner.clone().project(camera),x=(p.x+1)*size.width/2,y=(1-p.y)*size.height/2
    assert.ok(x>=pose.rect.left&&x<=pose.rect.right&&y>=pose.rect.top&&y<=pose.rect.bottom)
  }
}
const server=await preview({root,preview:{host:'127.0.0.1',port:5195,strictPort:true}})
let browser
try {
  browser=await chromium.launch({executablePath:chromeExecutable,headless:true,args:['--no-sandbox','--enable-unsafe-swiftshader','--use-gl=angle','--use-angle=swiftshader']})
  const errors: string[]=[]
  const context=await browser.newContext({viewport:{width:1440,height:900},reducedMotion:'reduce'})
  await installBrowserHelpers(context,()=>{
    localStorage.setItem('damien-portfolio:audio-consent','muted')
    localStorage.setItem('damien-portfolio:background-music',JSON.stringify({enabled:false}))
    localStorage.setItem('damien-portfolio:sound-effects',JSON.stringify({enabled:false}))
    localStorage.setItem('damien-portfolio:room-menu:03','expanded')
  })
  const page=await context.newPage();page.on('pageerror',error=>errors.push(error.message))
  await page.goto('http://127.0.0.1:5195/damien-portfolio/')
  await page.locator('.city-stage[data-loaded="true"]').waitFor({timeout:120000})
  await page.getByRole('button',{name:/^Choose a floor/}).click()
  await page.locator('.city-stage[data-elevator-loaded="true"]').waitFor({timeout:120000})
  const floor=page.getByRole('button',{name:'Select level 3: Projects'});await floor.focus();await floor.press('Enter')
  await page.locator('.city-stage[data-elevator-status="arrived"][data-room="projects"]').waitFor({timeout:120000})
  await page.locator('#room-progress').evaluate(input=>{
    Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value')!.set!.call(input,'-.2')
    input.dispatchEvent(new Event('input',{bubbles:true}));input.dispatchEvent(new Event('change',{bubbles:true}))
  })
  await page.waitForFunction(()=>document.querySelector<HTMLElement>('.city-stage')!.dataset.roomY==='-0.200')
  const more=page.locator('.room-more-controls');await more.locator('summary').click()
  await more.getByRole('button',{name:'Look left'}).click();await more.getByRole('button',{name:'Look left'}).click()
  await page.getByRole('button',{name:'Hide menu'}).click()
  const canvas=page.locator('canvas').first(),bounds=await canvas.boundingBox()
  assert.ok(bounds)
  await page.mouse.click(bounds.x+bounds.width/2,bounds.y+bounds.height/2)
  await page.locator('.city-stage[data-room-view="directory"][data-card-focus-framed="true"]').waitFor({timeout:30000})
  assert.equal(await page.locator('.room-interface,.project-case-description,.project-case-navigation').count(),0,'Directory is zoom-only, without either sidebar')
  await page.screenshot({path:screenshotPath('project-directory-zoom.png')})
  for (const size of [{width:938,height:986},{width:390,height:844}]) {
    await page.setViewportSize(size);await page.waitForTimeout(400)
    assert.equal(await page.locator('.city-stage').getAttribute('data-card-focus-framed'),'true')
    assert.equal(await page.locator('.room-interface,.project-case-description,.project-case-navigation').count(),0)
  }
  await page.keyboard.press('Escape')
  await page.locator('.city-stage[data-room-view="main"]').waitFor()
  await page.waitForFunction(()=>document.querySelector<HTMLElement>('.city-stage')!.dataset.roomY==='-0.200')
  assert.deepEqual(errors,[])
  await context.close()
  console.log('PASS raised directory/top-projector framing, real native card pick, zoom-only UI without sidebars, desktop/mobile resize and saved hallway return')
} finally {await browser?.close();await new Promise(done=>server.httpServer.close(done))}
