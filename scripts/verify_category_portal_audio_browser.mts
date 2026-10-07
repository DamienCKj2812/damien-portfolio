import assert from 'node:assert/strict'
import fs from 'node:fs'
import { resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { preview } from 'vite'
import { chromium, chromeExecutable, installBrowserHelpers } from './browser_tools.mts'
import { sceneFile } from './node_json.mts'
declare global { interface Window { portalStarts: number } }
type PortalBuffer = AudioBuffer & { portalEffect?: boolean }

const root = resolve(fileURLToPath(new URL('..', import.meta.url)))
const portalBytes = fs.statSync(resolve(root, 'public/media/audio/effects/light-saber.mp3')).size
const manifest = sceneFile(resolve(root, 'public/models/rooms/projects/scene.json'), 'projects')
const portals = manifest.navigation.categories.filter(category => category.door)
const server = await preview({ root, build: { outDir: process.env.VITE_TEST_OUT_DIR || 'dist' }, preview: { host: '127.0.0.1', port: 5199, strictPort: true } })
let browser
try {
  browser = await chromium.launch({ executablePath: chromeExecutable, headless: true,
    args: ['--no-sandbox', '--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] })
  const page = await browser.newPage({ viewport: { width: 1280, height: 800 }, reducedMotion: 'reduce' })
  const errors: string[] = []
  page.on('pageerror', error => errors.push(error.message))
  await installBrowserHelpers(page,bytes => {
    localStorage.setItem('damien-portfolio:audio-consent', 'enabled')
    localStorage.setItem('damien-portfolio:background-music', JSON.stringify({ enabled: false, volume: .35 }))
    localStorage.setItem('damien-portfolio:sound-effects', JSON.stringify({ enabled: true, volume: .45 }))
    window.portalStarts = 0
    const NativeContext = window.AudioContext
    window.AudioContext = new Proxy(NativeContext, { construct(target, args) {
      const context = Reflect.construct(target, args) as AudioContext
      const decode = context.decodeAudioData.bind(context)
      context.decodeAudioData = (data: ArrayBuffer) => {
        const portal = data.byteLength === bytes
        return decode(data).then(buffer => { if (portal) (buffer as PortalBuffer).portalEffect = true;return buffer })
      }
      const createSource = context.createBufferSource.bind(context)
      context.createBufferSource = () => {
        const source = createSource(), start = source.start.bind(source)
        source.start = (...args: Parameters<AudioBufferSourceNode['start']>) => { if ((source.buffer as PortalBuffer | null)?.portalEffect) window.portalStarts++;return start(...args) }
        return source
      }
      return context
    } })
  }, portalBytes)
  await page.goto('http://127.0.0.1:5199/damien-portfolio/')
  await page.getByRole('button', { name: 'Choose a floor', exact: true }).click()
  await page.waitForSelector('.city-stage[data-interactive=true][data-elevator-loaded=true]', { timeout: 90000 })
  await page.getByRole('button', { name: /^Select level 3:/ }).focus()
  await page.keyboard.press('Enter')
  await page.waitForSelector('.city-stage[data-room=projects][data-elevator-status=arrived]', { timeout: 90000 })
  const seek = async (y: number) => {
    await page.locator('#room-progress').evaluate((input, value) => {
      Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')!.set!.call(input, String(value))
      input.dispatchEvent(new Event('input', { bubbles: true }));input.dispatchEvent(new Event('change', { bubbles: true }))
    }, y)
    await page.waitForFunction(value => Math.abs(Number(document.querySelector<HTMLElement>('.city-stage')!.dataset.roomY) - value) < .03, y)
    await page.waitForTimeout(100)
  }
  const scroll = async (pixels: number) => {
    await page.locator('canvas').hover({ position: { x: 640, y: 400 } })
    await page.mouse.wheel(0, pixels)
    await page.waitForTimeout(180)
  }
  assert.equal(await page.evaluate(() => window.portalStarts), 0, 'Room arrival is silent')
  for (const category of portals) {
    assert.ok(category.door)
    const count = await page.evaluate(() => window.portalStarts)
    await seek(category.door.y - 1)
    assert.equal(await page.evaluate(() => window.portalStarts), count, 'Progress seeking is silent')
    await scroll(200)
    await page.waitForFunction(expected => window.portalStarts === expected, count + 1)
    await scroll(-200)
    await page.waitForFunction(expected => window.portalStarts === expected, count + 2)
    await page.waitForTimeout(200)
    assert.equal(await page.evaluate(() => window.portalStarts), count + 2, 'Idle frames must not repeat portal effects')
  }
  await page.getByRole('button', { name: 'Mute interaction sound effects', exact: true }).click()
  const count = await page.evaluate(() => window.portalStarts)
  assert.ok(portals[0].door)
  await seek(portals[0].door.y - 1);await scroll(200);await scroll(-200)
  assert.equal(await page.evaluate(() => window.portalStarts), count, 'SFX mute suppresses both directions')
  assert.deepEqual(errors, [])
  console.log('PASS browser category portal audio: actual scroll entry/exit through both doors, silent arrival/progress seek/idle, and mute')
} finally {
  await browser?.close()
  await new Promise(done => server.httpServer.close(done))
}
