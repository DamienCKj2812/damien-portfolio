import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { createHash } from 'node:crypto'

const root=path.resolve(fileURLToPath(new URL('..',import.meta.url)))
const manifest=JSON.parse(fs.readFileSync(path.join(root,'assets/media/manifest.json')))
const migrate=process.argv.includes('--migrate-legacy')
const hash=file=>createHash('sha256').update(fs.readFileSync(file)).digest('hex')
const resolve=relative=>{
  const file=path.resolve(root,relative)
  if (!file.startsWith(`${root}${path.sep}`)) throw new Error(`Media path escapes repository: ${relative}`)
  return file
}
// Validate every available source/legacy file before any legacy deletion.
for (const [id,asset] of Object.entries(manifest.files)) {
  const source=resolve(asset.source)
  if (!fs.existsSync(source)) {
    if (!migrate) throw new Error(`Missing canonical media source: ${asset.source}`)
    const legacy=asset.legacyPaths.map(resolve).find(file=>fs.existsSync(file))
    if (!legacy || hash(legacy)!==asset.sha256) throw new Error(`Missing/changed migration source: ${id}`)
    fs.mkdirSync(path.dirname(source),{recursive:true});fs.copyFileSync(legacy,source)
  }
  if (hash(source)!==asset.sha256) throw new Error(`Source media bytes changed: ${asset.source}`)
  if (migrate) for (const relative of asset.legacyPaths) {
    const file=resolve(relative)
    if (fs.existsSync(file)&&hash(file)!==asset.sha256) throw new Error(`Unrecognized legacy file; not removed: ${relative}`)
  }
}
let copied=0
for (const asset of Object.values(manifest.files)) {
  if (!asset.publicPath) continue
  const output=resolve(`public/${asset.publicPath}`)
  fs.mkdirSync(path.dirname(output),{recursive:true})
  if (!fs.existsSync(output)||hash(output)!==asset.sha256) {fs.copyFileSync(resolve(asset.source),output);copied++}
  if (hash(output)!==asset.sha256) throw new Error(`Incomplete deployed media: ${asset.publicPath}`)
}
if (migrate) {
  for (const asset of Object.values(manifest.files)) for (const relative of asset.legacyPaths) {
    const file=resolve(relative)
    if (fs.existsSync(file)) fs.unlinkSync(file)
  }
  const old=resolve('public/audio')
  if (fs.existsSync(old)&&fs.readdirSync(old).length===0) fs.rmdirSync(old)
}
console.log(`PASS shared media: ${Object.keys(manifest.files).length} immutable originals, 5 browser audio files, ${copied} updated copies${migrate?', verified legacy files migrated':''}`)
