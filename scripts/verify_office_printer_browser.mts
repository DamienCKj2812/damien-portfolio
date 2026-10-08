import assert from 'node:assert/strict'
import { PerspectiveCamera, Vector3 } from 'three'
import { preview } from 'vite'
import { jsonFile, sceneFile } from './node_json.mts'
import { parseCv } from '../src/types/cv.ts'
import { chromium, chromeExecutable, installBrowserHelpers, screenshotPath } from './browser_tools.mts'

const manifest = sceneFile(new URL('../public/models/rooms/about/scene.json', import.meta.url), 'about')
const cvContent = parseCv(jsonFile(new URL('../src/data/cv.json', import.meta.url)))
const printer = manifest.groups.filter(item => item.role === 'printer')
assert.deepEqual(new Set(printer.map(item => item.kind)), new Set(['solid', 'lines']))
assert.ok(printer.every(item => item.actor === 0 && item.id === 'printer'))
const server = await preview({ preview: { host: '127.0.0.1', port: 0 } })
let browser
try {
  browser = await chromium.launch({ executablePath: chromeExecutable, headless: true, args: ['--no-sandbox', '--enable-unsafe-swiftshader', '--use-gl=angle', '--use-angle=swiftshader'] })
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 }, reducedMotion: 'reduce' })
  await installBrowserHelpers(context, () => {
    if (location.pathname === '/damien-portfolio/') {
      localStorage.setItem('damien-portfolio:audio-consent', 'muted')
      localStorage.setItem('damien-portfolio:room-menu:01', 'expanded')
    }
  })
  const page = await context.newPage()
  const errors: string[] = []
  page.on('pageerror', error => errors.push(error.message))
  const address = server.httpServer.address()
  assert.ok(address && typeof address !== 'string')
  await page.goto(`http://127.0.0.1:${address.port}/damien-portfolio/?mode=3d`)
  await page.locator('.city-stage[data-loaded="true"]').waitFor({ timeout: 120000 })
  await page.getByRole('button', { name: /^Choose a floor/ }).click()
  await page.locator('.city-stage[data-elevator-loaded="true"]').waitFor({ timeout: 120000 })
  const floor = page.getByRole('button', { name: /^Select level 1:/ })
  await floor.focus();await floor.press('Enter')
  await page.locator('.city-stage[data-elevator-status="arrived"][data-room="about"]').waitFor({ timeout: 120000 })
  const pdfUrl = new URL(`cv/${encodeURIComponent(cvContent.pdf.file)}`, page.url()).href
  const cv = await page.request.get(pdfUrl)
  assert.equal(cv.status(), 200)
  assert.equal((await cv.body()).subarray(0, 5).toString(), '%PDF-')
  const canvas = page.locator('canvas').first()
  await page.waitForFunction(() => Boolean(document.querySelector('canvas')?.dataset.roomFov))
  const box = await canvas.boundingBox()
  assert.ok(box)
  const camera = new PerspectiveCamera(Number(await canvas.getAttribute('data-room-fov')), box.width / box.height, .01, 350)
  camera.position.fromArray(manifest.cameras.main.position)
  camera.quaternion.setFromAxisAngle(new Vector3(1, 0, 0), Math.PI / 2 + (manifest.navigation.initialPitch ?? .02))
  camera.updateMatrixWorld()
  const point = new Vector3(2.35, .68, 1.14).project(camera)
  const x = box.x + (point.x + 1) * box.width / 2, y = box.y + (1 - point.y) * box.height / 2
  await page.mouse.move(10, 10)
  await page.screenshot({ path: screenshotPath('office-printer-idle.png') })
  await page.mouse.move(x, y)
  await page.locator('.about-target-label[data-target="printer"]').waitFor()
  assert.equal(await page.evaluate(() => document.body.style.cursor), 'pointer')
  assert.equal(context.pages().length, 1, 'Hover never opens a document or starts printing')
  await page.screenshot({ path: screenshotPath('office-printer-hover.png') })
  const previewOpened = page.waitForEvent('popup')
  await page.mouse.click(x, y)
  const preview = await previewOpened
  preview.on('pageerror', error => errors.push(error.message))
  await preview.waitForURL(pdfUrl)
  assert.equal(preview.url(), pdfUrl, 'The new tab opens the PDF URL directly')
  assert.equal(await preview.evaluate(() => window.opener), null, 'The PDF tab cannot control the portfolio opener')
  assert.equal(await preview.evaluate(() => document.contentType), 'application/pdf', 'The new tab loads the real CV PDF')
  assert.equal(await preview.locator('header, iframe[data-cv-print]').count(), 0, 'No custom preview header or wrapper remains')
  assert.equal(await page.locator('.city-stage').getAttribute('data-room-view'), 'main', 'Opening the CV preserves the office camera/view')
  const nativeViewer = preview.frames().find(frame => frame.url().startsWith('chrome-extension://'))
  assert.ok(nativeViewer, 'Chromium mounts its actual PDF viewer')
  await nativeViewer.getByRole('button', { name: 'Print', exact: true }).waitFor({ state: 'visible' })
  await preview.screenshot({ path: screenshotPath('office-cv-real-pdf.png') })
  await preview.close()
  await page.mouse.move(x, y);await page.mouse.down();await page.mouse.move(x + 50, y + 10, { steps: 8 });await page.mouse.up()
  assert.equal(context.pages().length, 1, 'Dragging over the printer never opens the PDF')
  const printButton = page.locator('.room-action').filter({ hasText: /^Print CV$/ })
  const keyboardOpened = page.waitForEvent('popup')
  await printButton.focus();await printButton.press('Enter')
  const keyboardPreview = await keyboardOpened
  await keyboardPreview.waitForURL(pdfUrl)
  assert.equal(await keyboardPreview.evaluate(() => document.contentType), 'application/pdf')
  await keyboardPreview.close()
  await page.locator('#observer-profile-trigger').click()
  await page.getByRole('dialog', { name: /Chong Kah Jun/ }).waitFor()
  assert.equal(await page.locator('.about-target-label[data-target="printer"]').count(), 0, 'Profile modal blocks printer hints')
  await page.keyboard.press('Escape')
  await page.setViewportSize({ width: 390, height: 844 })
  const mobileOpened = page.waitForEvent('popup')
  await printButton.click()
  const mobilePreview = await mobileOpened
  await mobilePreview.setViewportSize({ width: 390, height: 844 })
  await mobilePreview.waitForURL(pdfUrl)
  assert.equal(await mobilePreview.evaluate(() => document.contentType), 'application/pdf')
  assert.equal(await mobilePreview.locator('header, iframe[data-cv-print]').count(), 0)
  await mobilePreview.close()
  assert.deepEqual(errors, [])
  await context.close()
  console.log('PASS office printer: real 3D hover/pick, direct CV PDF in a new tab with native browser controls, no custom wrapper, drag rejection, keyboard/mobile action and modal blocking')
} finally {
  await browser?.close()
  await new Promise<void>(done => server.httpServer.close(() => done()))
}
