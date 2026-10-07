import assert from 'node:assert/strict'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { createHash } from 'node:crypto'

const root=path.resolve(fileURLToPath(new URL('..',import.meta.url)))
const manifest=JSON.parse(fs.readFileSync(path.join(root,'assets/media/manifest.json')))
const digest=file=>createHash('sha256').update(fs.readFileSync(file)).digest('hex')
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
const portfolio=fs.readFileSync(path.join(root,'src/data/portfolio.js'),'utf8')
assert.ok(portfolio.includes(`src: '${manifest.files.music.publicPath}'`),'Music must use the canonical browser path')
const logos=JSON.parse(fs.readFileSync(path.join(root,'assets/timeline-observatory/logos/logo-manifest.json')))
for (const [id,key] of [['apu','apuLogo'],['lyj','lyjLogo'],['cos','cosLogo']]) {
  assert.equal(logos[id].source,manifest.files[key].source)
  assert.equal(logos[id].sourceSha256,manifest.files[key].sha256)
  assert.equal(digest(path.join(root,'assets/timeline-observatory',logos[id].texture)),logos[id].outputSha256)
  assert.equal(digest(path.join(root,'public/models/rooms/experience',logos[id].texture)),logos[id].outputSha256)
}
console.log(`PASS ${Object.keys(manifest.files).length} centrally catalogued media files (${bytes} source bytes), exact-byte audio copies, organised logo provenance and no root/legacy media${process.argv.includes('--dist')?' / production output verified':''}`)
