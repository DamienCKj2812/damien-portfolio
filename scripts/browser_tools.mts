import { mkdirSync, mkdtempSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join, resolve } from 'node:path'
import type { BrowserContext } from 'playwright'

// Keep overrides typed against the installed SDK rather than dynamic-import any.
const sdk: typeof import('playwright') = process.env.PLAYWRIGHT_MODULE
  ? await import(process.env.PLAYWRIGHT_MODULE) as typeof import('playwright')
  : await import('playwright')
export const chromium = sdk.chromium
export const chromeExecutable = process.env.CHROME_EXECUTABLE || '/usr/bin/google-chrome'

export function installBrowserHelpers<Arg>(target: Pick<BrowserContext, 'addInitScript'>, callback?: (arg: Arg) => void, arg?: Arg) {
  // tsx preserves nested function names with __name. Playwright serializes
  // callbacks without their module scope, so provide that transform helper
  // before any serialized instrumentation runs. A string avoids transforming
  // the helper's own callback and needing __name before it exists.
  // Put instrumentation in this same script: Playwright does not guarantee
  // ordering between independently registered page/context init scripts.
  const content = "globalThis.__name = (target, name) => Object.defineProperty(target, 'name', { value: name, configurable: true });"
    + (callback ? `\n(${callback.toString()})(${JSON.stringify(arg) ?? 'undefined'});` : '')
  return target.addInitScript({ content })
}

let outputDirectory: string | undefined
export function screenshotPath(name: string): string {
  if (!outputDirectory) {
    outputDirectory = process.env.VERIFY_OUTPUT_DIR
      ? resolve(process.env.VERIFY_OUTPUT_DIR)
      : mkdtempSync(join(tmpdir(), 'portfolio-verify-'))
    mkdirSync(outputDirectory, { recursive: true })
    console.log(`Browser artifacts: ${outputDirectory}`)
  }
  return join(outputDirectory, name)
}
