/* Browser regression: restored orbital sky, recessed door seal and passage. */
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import { fileURLToPath } from 'node:url'
import { resolve } from 'node:path'
import { preview } from 'vite'

const root = resolve(fileURLToPath(new URL('../..', import.meta.url)))
const { chromium } = await import(process.env.PLAYWRIGHT_MODULE || '/tmp/opencode/browser-check/node_modules/playwright/index.mjs')
const manifest = JSON.parse(await readFile(resolve(root, 'public/models/city/scene.json'), 'utf8'))
assert.equal(manifest.orbitalSky.planets, 2)
assert.equal(manifest.orbitalSky.visibleLabels, 0)
assert(manifest.groups.some(group => group.role === 'sky-shine'))
assert.equal(manifest.actors.filter(actor => actor.style === 'walking_npc' && actor.walk).length, 10)
const server = await preview({ root, preview: { host: '127.0.0.1', port: 5193, strictPort: true } })
let browser
try {
  browser = await chromium.launch({ executablePath: '/usr/bin/google-chrome', headless: true,
    args: ['--no-sandbox', '--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] })
  const page = await browser.newPage({ viewport: { width: 1798, height: 800 }, reducedMotion: 'reduce' })
  if (process.env.FIXED_APPROACH) {
    await page.route(/\/models\/city\/animation\.bin(?:\?.*)?$/, async route => {
      const response = await route.fetch()
      const bytes = await response.body()
      const values = new Float32Array(bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.length))
      const row = manifest.channelCount * manifest.channelStride
      const pose = values.slice(244 * row, 244 * row + manifest.channelStride)
      for (let i = 0; i < manifest.frameEnd; i++) values.set(pose, i * row)
      await route.fulfill({ response, body: Buffer.from(values.buffer) })
    })
  }
  const errors = []
  page.on('pageerror', error => errors.push(error.message))
  page.on('console', message => {
    if (message.type() === 'error' && !message.text().startsWith('Failed to load resource:')) errors.push(message.text())
  })
  await page.goto('http://127.0.0.1:5193/damien-portfolio/')
  await page.getByRole('button', { name: 'Continue muted', exact: true }).click()
  await page.waitForSelector('.city-stage[data-loaded=true]', { timeout: 90000 })
  await page.waitForTimeout(700)
  if (!process.env.FIXED_APPROACH) {
    const hidden = await page.addStyleTag({ content: 'body * { visibility: hidden !important; } canvas { visibility: visible !important; }' })
    await page.screenshot({ path: resolve(root, 'assets/cyber-city/restored-sky-preview.png') })
    await hidden.evaluate(style => style.remove())
  }
  const seek = async frame => {
    await page.locator('#city-timeline').evaluate((input, value) => {
      Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set.call(input, String(value))
      input.dispatchEvent(new Event('input', { bubbles: true }))
      input.dispatchEvent(new Event('change', { bubbles: true }))
    }, frame)
    await page.waitForFunction(value => Math.abs(Number(document.querySelector('.city-stage').dataset.renderedFrame) - value) <= 1,
      frame, { timeout: 90000 })
    await page.waitForTimeout(250)
  }
  for (const frame of [180, 245, 260, 280, 300, 310, 350, 380, 400, 450]) {
    await seek(frame)
    await page.screenshot({ path: `/tmp/opencode/entrance-frame-${frame}.png` })
    if (frame === 180 && !process.env.FIXED_APPROACH) {
      await page.screenshot({ path: resolve(root, 'assets/cyber-city/restored-outdoor-npcs.png') })
    }
  }
  for (const frame of [380, 310, 280, 245, 1]) await seek(frame)
  await page.getByRole('button', { name: /^Choose a floor/ }).click()
  await page.waitForSelector('.city-stage[data-interactive=true]', { timeout: 90000 })
  assert.deepEqual(errors, [])
  console.log('PASS restored sky metadata, closed/open/enter/reverse frames and elevator arrival; no browser errors')
} finally {
  await browser?.close()
  await new Promise(done => server.httpServer.close(done))
}
