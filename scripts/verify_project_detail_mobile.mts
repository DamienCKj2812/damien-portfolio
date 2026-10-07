import assert from 'node:assert/strict'
import { preview } from 'vite'
import { chromium, chromeExecutable, installBrowserHelpers, screenshotPath } from './browser_tools.mts'

const server = await preview({ preview: { host: '127.0.0.1', port: 0 } })
const level = process.env.DETAIL_TEST_LEVEL || '3'
const room = level === '2' ? 'skills' : level === '4' ? 'experience' : 'projects'
const back = level === '2' ? 'Back to gallery' : level === '4' ? 'Back to observatory' : 'Back to hallway'
let browser
try {
  browser = await chromium.launch({ executablePath: chromeExecutable, headless: true, args: ['--no-sandbox', '--enable-unsafe-swiftshader', '--use-gl=angle', '--use-angle=swiftshader'] })
  const context = await browser.newContext({ viewport: { width: 390, height: 844 }, reducedMotion: 'reduce' })
  await installBrowserHelpers(context, () => {
    localStorage.setItem('damien-portfolio:audio-consent', 'muted')
    localStorage.setItem('damien-portfolio:room-menu:03', 'expanded')
    localStorage.setItem('damien-portfolio:room-menu:02', 'expanded')
    localStorage.setItem('damien-portfolio:room-menu:04', 'expanded')
  })
  const page = await context.newPage()
  const errors: string[] = []
  page.on('pageerror', error => errors.push(error.message))
  const address = server.httpServer.address()
  assert.ok(address && typeof address !== 'string')
  await page.goto(`http://127.0.0.1:${address.port}/damien-portfolio/`)
  await page.locator('.city-stage[data-loaded="true"]').waitFor({ timeout: 120000 })
  await page.getByRole('button', { name: /^Choose a floor/ }).click()
  await page.locator('.city-stage[data-elevator-loaded="true"]').waitFor({ timeout: 120000 })
  const floor = page.getByRole('button', { name: new RegExp(`^Select level ${level}:`) })
  await floor.focus()
  await floor.press('Enter')
  await page.locator(`.city-stage[data-elevator-status="arrived"][data-room="${room}"]`).waitFor({ timeout: 120000 })
  if (level === '3') await page.locator('.room-index-button').filter({ hasText: 'Agent Property' }).click()
  else await page.locator('.room-index-button').first().click()
  await page.locator('.project-mobile-header').waitFor()
  await page.locator('.city-stage[data-card-focus-framed="true"]').waitFor({ timeout: 30000 })
  const dock = page.locator('.project-mobile-dock')
  assert.equal(await dock.getByRole('button', { name: 'Previous chapter' }).isDisabled(), true)
  await dock.getByRole('button', { name: 'Next chapter' }).click()
  await page.waitForFunction(()=>document.querySelector('.project-mobile-chapter-count')?.textContent?.includes('Chapter 02'))
  await dock.locator('button').nth(1).click()
  const sheet = page.getByRole('dialog', { name: 'Chapters', exact: true })
  const targetTitle = await sheet.locator('li button strong').nth(2).textContent()
  await sheet.locator('li button').nth(2).click()
  assert.equal(await sheet.isVisible(), false)
  assert.ok(targetTitle)
  await page.locator('.project-case-description h3').filter({ hasText: targetTitle }).waitFor()
  await dock.locator('button').nth(1).click()
  await page.keyboard.press('Escape')
  assert.equal(await sheet.isVisible(), false)
  assert.equal(await dock.isVisible(), true, 'Escape closes the sheet without leaving the project')
  for (const viewport of [{ width: 390, height: 844 }, { width: 375, height: 667 }]) {
    await page.setViewportSize(viewport)
    await page.waitForTimeout(350)
    for (const selector of ['.project-mobile-header', '.project-mobile-dock', '.project-case-description']) {
      const box = await page.locator(selector).boundingBox()
      assert.ok(box && box.x >= 0 && box.y >= 0 && box.x + box.width <= viewport.width + 1 && box.y + box.height <= viewport.height + 1)
    }
    const background = await page.locator('.project-mobile-header').evaluate(element => getComputedStyle(element).backgroundColor)
    assert.match(background, /rgba/, 'Header keeps the live scene visible')
  }
  await page.screenshot({ path: screenshotPath(`${room}-detail-mobile.png`) })
  await page.getByRole('button', { name: back, exact: true }).click()
  await page.locator('.city-stage[data-room-view="main"]').waitFor()
  assert.deepEqual(errors, [])
  await context.close()
  console.log(`PASS level ${level} mobile detail: chapters, sheet selection/Escape, translucent header, responsive bounds, saved room return`)
} finally {
  await browser?.close()
  await new Promise<void>(done => server.httpServer.close(() => done()))
}
