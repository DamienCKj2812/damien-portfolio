import assert from 'node:assert/strict'
import fs from 'node:fs'
import { resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { preview } from 'vite'

const root = resolve(fileURLToPath(new URL('..', import.meta.url)))
const bytes = fs.statSync(resolve(root, 'public/media/audio/effects/sci-fi-door.mp3')).size
const { chromium } = await import(process.env.PLAYWRIGHT_MODULE || '/tmp/opencode/browser-check/node_modules/playwright/index.mjs')
const server = await preview({ root, build: { outDir: process.env.VITE_TEST_OUT_DIR || 'dist' }, preview: { host: '127.0.0.1', port: 5201, strictPort: true } })
let browser
try {
  browser = await chromium.launch({ executablePath: '/usr/bin/google-chrome', headless: true,
    args: ['--no-sandbox', '--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] })
  const page = await browser.newPage({ viewport: { width: 1280, height: 800 }, reducedMotion: 'reduce' })
  const errors = []
  page.on('pageerror', error => errors.push(error.message))
  await page.addInitScript(bytes => {
    localStorage.setItem('damien-portfolio:audio-consent', 'enabled')
    localStorage.setItem('damien-portfolio:background-music', JSON.stringify({ enabled: false, volume: .35 }))
    localStorage.setItem('damien-portfolio:sound-effects', JSON.stringify({ enabled: true, volume: .45 }))
    window.doorStarts = []
    const NativeContext = window.AudioContext
    window.AudioContext = new Proxy(NativeContext, { construct(target, args) {
      const context = Reflect.construct(target, args), decode = context.decodeAudioData.bind(context)
      context.decodeAudioData = data => { const door = data.byteLength === bytes;return decode(data).then(buffer => { if (door) buffer.doorEffect = true;return buffer }) }
      const create = context.createBufferSource.bind(context)
      context.createBufferSource = () => { const source = create(), start = source.start.bind(source);source.start = (...args) => { if (source.buffer?.doorEffect) window.doorStarts.push(performance.now());return start(...args) };return source }
      return context
    } })
  }, bytes)
  await page.goto('http://127.0.0.1:5201/damien-portfolio/')
  await page.waitForSelector('.city-stage[data-loaded=true]', { timeout: 90000 })
  await page.mouse.click(20, 400)
  const seek = async frame => {
    await page.locator('#city-timeline').evaluate((input, value) => {
      Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set.call(input, String(value))
      input.dispatchEvent(new Event('input', { bubbles: true }));input.dispatchEvent(new Event('change', { bubbles: true }))
    }, frame)
    await page.waitForFunction(value => Math.abs(Number(document.querySelector('.city-stage').dataset.renderedFrame) - value) < 1, frame, { timeout: 90000 })
  }
  await seek(245)
  assert.equal(await page.evaluate(() => window.doorStarts.length), 0)
  await seek(260);await page.waitForFunction(() => window.doorStarts.length === 1)
  await seek(280);await page.waitForTimeout(100);assert.equal(await page.evaluate(() => window.doorStarts.length), 1)
  await seek(1283)
  await seek(1300);await page.waitForFunction(() => window.doorStarts.length === 2)
  await page.getByRole('button', { name: 'Choose a floor', exact: true }).click()
  await page.waitForSelector('.city-stage[data-interactive=true][data-elevator-loaded=true]', { timeout: 90000 })
  await page.getByRole('button', { name: /^Select level 1:/ }).focus();await page.keyboard.press('Enter')
  await page.waitForSelector('.city-stage[data-room=about][data-elevator-status=arrived]', { timeout: 90000 })
  await page.waitForFunction(() => window.doorStarts.length === 3)
  await page.locator('#city').focus();await page.keyboard.press('Home');await page.keyboard.press('PageUp')
  await page.getByRole('button', { name: 'Yes, return to elevator', exact: true }).click()
  await page.waitForSelector('.city-stage[data-elevator-status=idle]', { timeout: 90000 })
  const completed = await page.evaluate(() => performance.now())
  assert.equal(await page.evaluate(() => window.doorStarts.length), 3, 'Instant return closing must be delayed')
  await page.waitForFunction(() => window.doorStarts.length === 4)
  const last = await page.evaluate(() => window.doorStarts.at(-1))
  assert(last - completed > 100, 'Return cue should occur after cabin arrival, not immediately on return activation')
  await page.getByRole('button', { name: 'Mute interaction sound effects', exact: true }).click()
  await seek(200);await seek(260);await page.waitForTimeout(300)
  assert.equal(await page.evaluate(() => window.doorStarts.length), 4)
  assert.deepEqual(errors, [])
  console.log('PASS browser door audio: actual main gate/R1/departure opening, delayed return close and mute')
} finally { await browser?.close();await new Promise(done => server.httpServer.close(done)) }
