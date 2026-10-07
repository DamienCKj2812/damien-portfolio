import assert from 'node:assert/strict'
import { resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { preview } from 'vite'
import { musicAutoplayPolicy } from '../src/audio/autoplayPolicy.js'

for (const policy of ['allowed', 'allowed-muted', 'disallowed']) assert.equal(musicAutoplayPolicy({}, { getAutoplayPolicy: () => policy }), policy)
assert.equal(musicAutoplayPolicy({}, {}), 'unknown')
assert.equal(musicAutoplayPolicy({}, { getAutoplayPolicy: () => { throw new Error('Unsupported') } }), 'unknown')
const root = resolve(fileURLToPath(new URL('..', import.meta.url)))
const { chromium } = await import(process.env.PLAYWRIGHT_MODULE || '/tmp/opencode/browser-check/node_modules/playwright/index.mjs')
const server = await preview({ root, build: { outDir: process.env.VITE_TEST_OUT_DIR || 'dist' }, preview: { host: '127.0.0.1', port: 5197, strictPort: true } })
try {
  for (const mode of ['allowed', 'allowed-muted', 'disallowed', 'unknown', 'muted']) {
    const browser = await chromium.launch({ executablePath: '/usr/bin/google-chrome', headless: true,
      args: ['--no-sandbox', '--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', `--autoplay-policy=${mode === 'allowed' ? 'no-user-gesture-required' : 'document-user-activation-required'}`] })
    try {
      const page = await browser.newPage({ reducedMotion: 'reduce' })
      const errors = []
      page.on('pageerror', error => errors.push(error.message))
      await page.addInitScript(mode => {
        const enabled = mode !== 'muted'
        localStorage.setItem('damien-portfolio:audio-consent', enabled ? 'enabled' : 'muted')
        localStorage.setItem('damien-portfolio:background-music', JSON.stringify({ enabled, volume: .35 }))
        localStorage.setItem('damien-portfolio:sound-effects', JSON.stringify({ enabled: false, volume: .45 }))
        if (mode === 'unknown') navigator.getAutoplayPolicy = undefined
        else navigator.getAutoplayPolicy = () => mode === 'muted' ? 'allowed' : mode
        window.musicChecks = { plays: [], contexts: 0 }
        const play = HTMLMediaElement.prototype.play
        HTMLMediaElement.prototype.play = function () {
          const record = { active: navigator.userActivation.isActive }
          window.musicChecks.plays.push(record)
          return play.call(this).catch(error => { record.failure = error.name;throw error })
        }
        const NativeContext = window.AudioContext
        window.AudioContext = new Proxy(NativeContext, { construct(target, args) { window.musicChecks.contexts++;return Reflect.construct(target, args) } })
      }, mode)
      await page.goto('http://127.0.0.1:5197/damien-portfolio/')
      await page.locator('.background-music').waitFor()
      assert.equal(await page.locator('.audio-consent').count(), 0)
      if (mode === 'allowed') {
        await page.waitForSelector('.background-music[data-music-state=playing]')
        assert.equal(await page.evaluate(() => window.musicChecks.plays[0].active), false, 'Browser-approved music should play without a new gesture')
        assert.equal(await page.evaluate(() => document.querySelector('#background-music-audio').volume), .35)
        await page.reload()
        await page.waitForSelector('.background-music[data-music-state=playing]')
        assert.equal(await page.evaluate(() => window.musicChecks.plays.length), 1)
      } else if (mode !== 'muted') {
        await page.waitForFunction(() => window.musicChecks.plays[0]?.failure === 'NotAllowedError')
        await page.waitForSelector('.background-music[data-music-state=ready]')
        await page.evaluate(() => document.dispatchEvent(new Event('visibilitychange')))
        assert.equal(await page.evaluate(() => window.musicChecks.plays.length), 1, 'A blocked automatic probe must not loop')
        await page.getByRole('button', { name: 'Play background music', exact: true }).click()
        await page.waitForSelector('.background-music[data-music-state=playing]')
        assert.equal(await page.evaluate(() => window.musicChecks.plays[1].active), true)
      } else {
        await page.waitForSelector(`.background-music[data-music-state=${mode === 'muted' ? 'off' : 'ready'}]`)
        await page.waitForTimeout(200)
        assert.equal(await page.evaluate(() => window.musicChecks.plays.length), 0, 'A saved mute must never attempt playback')
      }
      assert.equal(await page.evaluate(() => window.musicChecks.contexts), 0, 'Automatic music must not create a Web Audio effects context')
      assert.deepEqual(errors, [])
      console.log(`PASS music autoplay ${mode}: browser result, remembered choice and truthful status`)
    } finally { await browser.close() }
  }
} finally { await new Promise(done => server.httpServer.close(done)) }
