import assert from 'node:assert/strict'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { createHash } from 'node:crypto'
import { objectValue, parseMediaManifest, parsePortfolio, stringValue } from '../src/types/portfolio.ts'

const root=path.resolve(fileURLToPath(new URL('..',import.meta.url)))
const manifest=parseMediaManifest(JSON.parse(fs.readFileSync(path.join(root,'assets/media/manifest.json'),'utf8')) as unknown)
const digest=(file: string)=>createHash('sha256').update(fs.readFileSync(file)).digest('hex')
assert.equal(manifest.version,1)
let bytes=0
for (const [id,asset] of Object.entries(manifest.files)) {
  assert.ok(asset.source.startsWith('assets/media/'))
  const original=path.join(root,asset.source)
  assert.equal(digest(original),asset.sha256,`${id}: original changed`)
  bytes+=fs.statSync(original).size
  if (asset.publicPath) {
    assert.ok(asset.publicPath.startsWith('media/audio/'))
    assert.equal(digest(path.join(root,'public',asset.publicPath)),asset.sha256,`${id}: browser copy differs`)
    if (process.argv.includes('--dist')) assert.equal(digest(path.join(root,'dist',asset.publicPath)),asset.sha256,`${id}: deployed build copy differs`)
  }
  for (const legacy of asset.legacyPaths) assert.ok(!fs.existsSync(path.join(root,legacy)),`Stray legacy media: ${legacy}`)
}
const portfolio=parsePortfolio(JSON.parse(fs.readFileSync(path.join(root,'src/data/portfolio.json'),'utf8')) as unknown)
const music=manifest.files.music
assert.ok(music,'Missing canonical music')
assert.equal(portfolio.music.src,music.publicPath,'Music must use the canonical browser path')
const logos=objectValue(JSON.parse(fs.readFileSync(path.join(root,'assets/timeline-observatory/logos/logo-manifest.json'),'utf8')) as unknown,'logo manifest')
for (const [id,key] of [['apu','apuLogo'],['lyj','lyjLogo'],['cos','cosLogo']] as const) {
  const logo=objectValue(logos[id],`logo manifest.${id}`)
  const asset=manifest.files[key]
  assert.ok(asset,`Missing canonical logo: ${key}`)
  assert.equal(stringValue(logo.source,`${id}.source`),asset.source)
  assert.equal(stringValue(logo.sourceSha256,`${id}.sourceSha256`),asset.sha256)
  const texture=stringValue(logo.texture,`${id}.texture`)
  const outputSha256=stringValue(logo.outputSha256,`${id}.outputSha256`)
  assert.equal(digest(path.join(root,'assets/timeline-observatory',texture)),outputSha256)
  assert.equal(digest(path.join(root,'public/models/rooms/experience',texture)),outputSha256)
}
console.log(`PASS ${Object.keys(manifest.files).length} centrally catalogued media files (${bytes} source bytes), exact-byte audio copies, organised logo provenance and no root/legacy media${process.argv.includes('--dist')?' / production output verified':''}`)
