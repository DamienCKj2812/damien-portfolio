import assert from 'node:assert/strict'
import { fileURLToPath } from 'node:url'
import { resolve } from 'node:path'
import { preview } from 'vite'
import { chromium, chromeExecutable, installBrowserHelpers, screenshotPath } from './browser_tools.mts'
interface PlayRecord { active: boolean; src: string; failure?: string }
declare global { interface Window {
  audioChecks: { plays: PlayRecord[]; contexts: { active: boolean }[]; resumes: { active: boolean }[] }
  testHidden: boolean
} }

const root = resolve(fileURLToPath(new URL('..', import.meta.url)))
const server = await preview({ root, build: { outDir: process.env.VITE_TEST_OUT_DIR || 'dist' }, preview: { host: '127.0.0.1', port: 5196, strictPort: true } })
let browser
try {
  browser = await chromium.launch({ executablePath: chromeExecutable, headless: true,
    args: ['--no-sandbox', '--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--autoplay-policy=document-user-activation-required'] })
  const errors: string[] = []
  const context = await browser.newContext({ viewport: { width: 1280, height: 800 }, reducedMotion: 'reduce' })
  await installBrowserHelpers(context,() => {
    navigator.getAutoplayPolicy = () => 'disallowed'
    window.audioChecks = { plays: [], contexts: [], resumes: [] }
    const play = HTMLMediaElement.prototype.play
    HTMLMediaElement.prototype.play = function () {
      const record: PlayRecord = { active: navigator.userActivation.isActive, src: this.src }
      window.audioChecks.plays.push(record)
      return play.call(this).catch(error => { record.failure = error.name;throw error })
    }
    const NativeContext = window.AudioContext
    window.AudioContext = new Proxy(NativeContext, {
      construct(target, args) {
        window.audioChecks.contexts.push({ active: navigator.userActivation.isActive })
        const audio = Reflect.construct(target, args) as AudioContext
        const resume = audio.resume.bind(audio)
        audio.resume = () => { window.audioChecks.resumes.push({ active: navigator.userActivation.isActive });return resume() }
        return audio
      },
    })
  })
  const page = await context.newPage()
  page.on('pageerror', error => errors.push(error.message))
  page.on('console', message => {
    if (/autoplay|AudioContext.*(prevented|allowed)|could not start/i.test(message.text())) errors.push(message.text())
  })
  const audioRequests: string[] = []
  page.on('request', request => { if (/\/audio\/.*\.mp3/.test(request.url())) audioRequests.push(request.url()) })
  const visit = async (prompt = true) => {
    await page.goto('http://127.0.0.1:5196/damien-portfolio/')
    await page.locator('.background-music').waitFor()
    if (prompt) await page.getByRole('dialog', { name: 'Enter with sound?' }).waitFor()
    else assert.equal(await page.locator('.audio-consent').count(), 0, 'A remembered choice must skip the prompt')
    await page.waitForTimeout(250)
    const enabled = await page.evaluate(() => (JSON.parse(localStorage.getItem('damien-portfolio:background-music')!) as { enabled: boolean }).enabled)
    if (!prompt && enabled) {
      await page.waitForFunction(() => window.audioChecks.plays[0]?.failure === 'NotAllowedError')
      assert.equal(await page.evaluate(() => window.audioChecks.plays.length), 1, 'Remembered enabled music gets one refresh attempt')
      assert.equal(await page.locator('.background-music').getAttribute('data-autoplay-blocked'), 'true')
    } else assert.deepEqual(await page.evaluate(() => window.audioChecks.plays), [], 'No music autoplay without remembered approval')
    assert.deepEqual(await page.evaluate(() => window.audioChecks.contexts), [], 'No Web Audio context before consent')
    assert.equal(await page.locator('.background-music-toggle').first().getAttribute('aria-pressed'), 'false', 'Paused music must not be announced as on')
    assert.equal(await page.locator('.background-music').getAttribute('data-music-state'), await page.evaluate(() => (JSON.parse(localStorage.getItem('damien-portfolio:background-music')!) as { enabled: boolean }).enabled) ? 'ready' : 'off')
  }
  await visit()
  assert.equal(audioRequests.length, 0, 'Declined/unresolved sound should not fetch audio')
  assert.equal(await page.locator('.audio-consent-bars span').count(), 5)
  assert.equal(await page.locator('.audio-consent-bars span').first().evaluate(bar => getComputedStyle(bar).animationName), 'none', 'Reduced motion stops the sound bars')
  await page.screenshot({ path: screenshotPath('sound-prompt-desktop.png') })
  assert.equal(await page.getByRole('button', { name: 'Enable sound', exact: true }).evaluate(button => button === document.activeElement), true)
  await page.keyboard.press('Tab')
  assert.equal(await page.getByRole('button', { name: 'Continue muted', exact: true }).evaluate(button => button === document.activeElement), true)
  await page.keyboard.press('Tab')
  assert.equal(await page.getByRole('button', { name: 'Enable sound', exact: true }).evaluate(button => button === document.activeElement), true)
  await page.getByRole('button', { name: 'Enable sound', exact: true }).evaluate((button: HTMLButtonElement) => button.click())
  assert.equal(await page.getByRole('dialog', { name: 'Enter with sound?' }).count(), 1, 'Synthetic clicks must not grant sound permission')
  assert.equal(await page.evaluate(() => window.audioChecks.contexts.length), 0)
  await page.locator('.background-music button').evaluateAll((buttons: HTMLButtonElement[]) => buttons.forEach(button => button.click()))
  assert.equal(await page.evaluate(() => window.audioChecks.plays.length), 0, 'Inert background controls cannot bypass startup consent')
  assert.equal(await page.evaluate(() => window.audioChecks.contexts.length), 0)
  await page.getByRole('button', { name: 'Continue muted', exact: true }).click()
  await page.getByRole('dialog', { name: 'Enter with sound?' }).waitFor({ state: 'detached' })
  await page.waitForTimeout(200)
  assert.equal(await page.evaluate(() => document.querySelector<HTMLAudioElement>('#background-music-audio')!.paused), true)
  assert.equal(await page.evaluate(() => window.audioChecks.contexts.length), 0)
  for (const key of ['background-music', 'sound-effects']) {
    assert.equal(await page.evaluate(name => (JSON.parse(localStorage.getItem(`damien-portfolio:${name}`)!) as { enabled: boolean }).enabled, key), false)
  }
  await visit(false)
  assert.equal(await page.evaluate(() => document.querySelector<HTMLAudioElement>('#background-music-audio')!.paused), true)
  assert.equal(await page.getByRole('button', { name: 'Enable interaction sound effects', exact: true }).count(), 1)
  await page.getByRole('button', { name: 'Play background music', exact: true }).click()
  await page.waitForFunction(() => !document.querySelector<HTMLAudioElement>('#background-music-audio')!.paused)
  await page.waitForSelector('.background-music[data-music-state=playing]')
  assert.equal(await page.locator('.background-music-toggle').first().getAttribute('aria-pressed'), 'true')
  assert.equal(await page.evaluate(() => window.audioChecks.contexts.length), 0, 'Music may be enabled independently of effects')
  await page.getByRole('button', { name: 'Pause background music', exact: true }).click()
  await page.getByRole('button', { name: 'Enable interaction sound effects', exact: true }).click()
  await page.waitForFunction(() => window.audioChecks.contexts.length === 1)
  assert.equal(await page.evaluate(() => window.audioChecks.contexts[0].active), true)
  await page.getByRole('button', { name: 'Mute interaction sound effects', exact: true }).click()

  await page.evaluate(() => {
    localStorage.setItem('damien-portfolio:background-music', JSON.stringify({ enabled: true, volume: .27 }))
    localStorage.setItem('damien-portfolio:sound-effects', JSON.stringify({ enabled: true, volume: .33 }))
  })
  await visit(false)
  await page.evaluate(() => document.dispatchEvent(new Event('visibilitychange')))
  assert.equal(await page.evaluate(() => window.audioChecks.plays.length), 1, 'Visibility must not repeat a rejected refresh attempt')
  await page.getByRole('button', { name: 'Open navigation guide', exact: true }).click()
  await page.waitForFunction(() => !document.querySelector<HTMLAudioElement>('#background-music-audio')!.paused)
  assert.equal(await page.evaluate(() => window.audioChecks.contexts.length), 1)
  assert.equal(await page.evaluate(() => window.audioChecks.contexts[0].active), true)
  assert.equal(await page.evaluate(() => window.audioChecks.plays[1].active), true)
  assert.equal(await page.evaluate(() => document.querySelector<HTMLAudioElement>('#background-music-audio')!.volume), .35, 'Music uses the fixed mix, not a legacy saved level')
  assert.equal(await page.evaluate(() => (JSON.parse(localStorage.getItem('damien-portfolio:sound-effects')!) as { volume: number }).volume), .45, 'Effects use the fixed mix')
  assert.equal(await page.locator('.background-music input').count(), 0, 'Toggle-only controls must not expose volume adjustment')
  await page.keyboard.press('Escape')
  await page.locator('.portfolio-guide[open]').waitFor({ state:'detached' })
  assert.equal(await page.getByRole('button', { name: 'Mute interaction sound effects', exact: true }).count(), 1)
  await page.evaluate(() => {
    window.testHidden = true
    Object.defineProperty(document, 'hidden', { configurable: true, get: () => window.testHidden })
    document.dispatchEvent(new Event('visibilitychange'))
  })
  await page.waitForFunction(() => document.querySelector<HTMLAudioElement>('#background-music-audio')!.paused)
  await page.waitForSelector('.background-music[data-music-state=ready]')
  assert.equal(await page.locator('.background-music-toggle').first().getAttribute('aria-pressed'), 'false')
  await page.evaluate(() => { window.testHidden = false;document.dispatchEvent(new Event('visibilitychange')) })
  await page.waitForFunction(() => !document.querySelector<HTMLAudioElement>('#background-music-audio')!.paused)

  await page.setViewportSize({ width: 390, height: 844 })
  await page.evaluate(() => localStorage.removeItem('damien-portfolio:audio-consent'))
  await visit()
  const bounds = await page.getByRole('dialog', { name: 'Enter with sound?' }).boundingBox()
  assert.ok(bounds)
  assert(bounds.x >= 0 && bounds.x + bounds.width <= 390)
  await page.screenshot({ path: screenshotPath('sound-prompt-mobile.png') })
  await page.keyboard.press('Escape')
  await page.getByRole('dialog', { name: 'Enter with sound?' }).waitFor({ state: 'detached' })
  assert.equal(await page.evaluate(() => window.audioChecks.plays.length), 0)
  assert.equal(await page.evaluate(() => window.audioChecks.contexts.length), 0)
  await visit(false)
  assert.equal(await page.evaluate(() => document.querySelector<HTMLAudioElement>('#background-music-audio')!.paused), true)
  assert.equal(await page.getByRole('button', { name: 'Enable interaction sound effects', exact: true }).count(), 1)
  await page.evaluate(() => localStorage.removeItem('damien-portfolio:audio-consent'))
  await visit()
  await page.keyboard.press('Enter')
  await page.getByRole('dialog', { name: 'Enter with sound?' }).waitFor({ state: 'detached' })
  await page.waitForFunction(() => !document.querySelector<HTMLAudioElement>('#background-music-audio')!.paused)
  assert.equal(await page.evaluate(() => window.audioChecks.plays[0].active), true)
  assert.equal(await page.getByRole('button', { name: 'Show sound prompt again', exact: true }).count(), 0, 'No center prompt-reopen button')
  await page.evaluate(() => localStorage.removeItem('damien-portfolio:audio-consent'))
  await visit()
  await page.emulateMedia({ reducedMotion: 'no-preference' })
  assert.equal(await page.locator('.audio-consent-bars span').first().evaluate(bar => getComputedStyle(bar).animationName), 'audio-consent-wave')
  await page.emulateMedia({ reducedMotion: 'reduce' })
  await page.keyboard.press('m')
  await page.getByRole('dialog', { name: 'Enter with sound?' }).waitFor({ state: 'detached' })
  assert.equal(await page.evaluate(() => document.querySelector<HTMLAudioElement>('#background-music-audio')!.paused), true)
  assert.equal(await page.evaluate(() => localStorage.getItem('damien-portfolio:audio-consent')), 'muted')
  await visit(false)

  const preferencesButton = page.getByRole('button', { name: 'Open sound preferences', exact: true })
  const helpButton = page.getByRole('button', { name: 'Open navigation guide', exact: true })
  await preferencesButton.hover()
  await page.getByRole('tooltip', { name: 'Sound preferences', exact: true }).waitFor()
  assert.equal(await page.evaluate(() => window.audioChecks.plays.length), 0, 'Hover is silent')
  await helpButton.hover()
  await page.getByRole('tooltip', { name: 'Navigation guide', exact: true }).waitFor()
  await preferencesButton.focus()
  await page.getByRole('tooltip', { name: 'Sound preferences', exact: true }).waitFor()
  await page.keyboard.press('Escape')
  await page.getByRole('tooltip', { name: 'Sound preferences', exact: true }).waitFor({ state: 'hidden' })
  await preferencesButton.click()
  await page.getByRole('dialog', { name: 'Enter with sound?', exact: true }).waitFor()
  const pausedFrame = await page.locator('.city-stage').getAttribute('data-frame')
  await page.keyboard.press('PageDown')
  assert.equal(await page.locator('.city-stage').getAttribute('data-frame'), pausedFrame, 'Preferences block journey input')
  assert.equal(await page.locator('.audio-consent [role=switch]').count(), 0, 'Preferences reuse the YES/MUTED interface')
  assert.equal(await page.locator('.audio-consent-bars span').count(), 5)
  await page.getByRole('button', { name: 'Enable sound', exact: true }).click()
  await page.getByRole('dialog', { name: 'Enter with sound?', exact: true }).waitFor({ state: 'detached' })
  await page.waitForSelector('.background-music[data-music-state=playing]')
  assert.equal(await page.evaluate(() => (JSON.parse(localStorage.getItem('damien-portfolio:sound-effects')!) as { enabled: boolean }).enabled), true)
  await preferencesButton.click()
  await page.getByRole('dialog', { name: 'Enter with sound?', exact: true }).waitFor()
  await page.keyboard.press('Escape')
  await page.getByRole('dialog', { name: 'Enter with sound?', exact: true }).waitFor({ state: 'detached' })
  assert.equal(await page.evaluate(() => (JSON.parse(localStorage.getItem('damien-portfolio:background-music')!) as { enabled: boolean }).enabled), true, 'Cancelling preferences preserves the choice')
  await preferencesButton.click()
  await page.getByRole('dialog', { name: 'Enter with sound?', exact: true }).waitFor()
  await page.keyboard.press('m')
  await page.getByRole('dialog', { name: 'Enter with sound?', exact: true }).waitFor({ state: 'detached' })
  await page.waitForSelector('.background-music[data-music-state=off]')
  assert.equal(await page.evaluate(() => (JSON.parse(localStorage.getItem('damien-portfolio:sound-effects')!) as { enabled: boolean }).enabled), false)
  assert.equal(await preferencesButton.evaluate(button => button === document.activeElement), true, 'Preferences restore trigger focus')
  await visit(false)

  await page.evaluate(() => {
    localStorage.setItem('damien-portfolio:background-music', JSON.stringify({ enabled: true, volume: .18 }))
    localStorage.setItem('damien-portfolio:sound-effects', JSON.stringify({ enabled: false, volume: .45 }))
  })
  await visit(false)
  const musicButton = page.getByRole('button', { name: 'Play background music', exact: true })
  assert.match((await musicButton.textContent())!, /Music ready/)
  await musicButton.click()
  await page.waitForSelector('.background-music[data-music-state=playing]')
  assert.equal(await page.evaluate(() => document.querySelector<HTMLAudioElement>('#background-music-audio')!.paused), false)
  assert.equal(await page.evaluate(() => (JSON.parse(localStorage.getItem('damien-portfolio:background-music')!) as { enabled: boolean }).enabled), true, 'Clicking ready music must play, not disable the saved preference')
  assert.equal(await page.evaluate(() => window.audioChecks.contexts.length), 0, 'Music starts without enabling muted SFX')
  // Selecting YES again must not pause a track already started by the icon's
  // user gesture, even when it changes the stored consent from muted to enabled.
  await preferencesButton.click()
  await page.getByRole('dialog', { name: 'Enter with sound?', exact: true }).waitFor()
  await page.getByRole('button', { name: 'Enable sound', exact: true }).click()
  await page.getByRole('dialog', { name: 'Enter with sound?', exact: true }).waitFor({ state: 'detached' })
  await page.waitForSelector('.background-music[data-music-state=playing]')
  assert.equal(await page.evaluate(() => document.querySelector<HTMLAudioElement>('#background-music-audio')!.paused), false, 'Updating YES must not clean up existing playback')
  await page.getByRole('button', { name: 'Mute interaction sound effects', exact: true }).click()
  await page.getByRole('button', { name: 'Pause background music', exact: true }).click()
  await page.waitForSelector('.background-music[data-music-state=off]')
  assert.equal(await page.evaluate(() => document.querySelector<HTMLAudioElement>('#background-music-audio')!.paused), true)
  assert.equal(await page.locator('.background-music-toggle').first().getAttribute('aria-pressed'), 'false')

  const checkLayout = async (progress: boolean) => {
    for (const width of [1280, 768, 390]) {
      await page.setViewportSize({ width, height: 844 })
       const audio = await page.locator('.background-music').boundingBox()
       assert.ok(audio)
      assert(audio.x >= 0 && audio.x + audio.width <= width)
       const header = await page.locator('.city-topline-actions').boundingBox()
       assert.ok(header)
      assert(header.x >= 0 && header.x + header.width <= width, 'Header icons must fit narrow viewports')
       assert.equal(await page.locator('.audio-choice-reopen').count(), 0)
      if (progress) {
         const bar = await page.locator('.city-controls:not([hidden])').boundingBox()
         assert.ok(bar)
        assert(audio.y + audio.height <= bar.y - 8, 'Audio panel must sit above the progress control hit area')
      } else {
        assert.equal(await page.locator('.city-controls:not([hidden])').count(), 0)
        assert.equal(await page.locator('.background-music').evaluate(node => getComputedStyle(node).bottom), width <= 600 ? '16px' : '20px', 'Return audio controls to the corner without progress')
      }
    }
  }
  await checkLayout(true)
  const enterRoom = async (number: number) => {
    await page.getByRole('button', { name: /^Choose a floor/ }).click()
    await page.waitForSelector('.city-stage[data-interactive=true][data-elevator-loaded=true]', { timeout: 90000 })
    await page.getByRole('button', { name: new RegExp(`^Select level ${number}:`) }).focus()
    await page.keyboard.press('Enter')
    await page.waitForSelector('.city-stage[data-elevator-status=arrived][data-room-loaded=true]', { timeout: 90000 })
  }
  await enterRoom(1)
  await checkLayout(false)
  await page.locator('#city').focus()
  await page.keyboard.press('Home')
  await page.keyboard.press('PageUp')
  await page.getByRole('button', { name: 'Yes, return to elevator', exact: true }).click()
  await page.waitForSelector('.city-stage[data-elevator-status=idle]', { timeout: 90000 })
  await enterRoom(4)
  await checkLayout(true)
  assert.deepEqual(errors, [])
  await context.close()
  console.log('PASS sound choice/preferences: shared YES/MUTED prompt, saved decisions, blocked-policy readiness, silent tooltips, modal input/focus and responsive layout')
} finally {
  await browser?.close()
  await new Promise(done => server.httpServer.close(done))
}
