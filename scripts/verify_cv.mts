import assert from 'node:assert/strict'
import fs from 'node:fs'
import { parseCv } from '../src/types/cv.ts'
import { jsonFile } from './node_json.mts'

// Uploaded CVs are deployed unchanged; cv.json must name exactly the files in public/cv/.
const cv = parseCv(jsonFile(new URL('../src/data/cv.json', import.meta.url)))
const directory = new URL('../public/cv/', import.meta.url)
const listed = [cv.primary, ...cv.alternates]
const uploaded = fs.existsSync(directory) ? fs.readdirSync(directory).filter(name => !name.startsWith('.')) : []
assert.deepEqual([...uploaded].sort(), listed.map(item => item.file).sort(),
  `public/cv/ must contain exactly the files listed in src/data/cv.json "files" (uploaded: ${uploaded.join(', ') || 'none'})`)
const signatures = { pdf: [0x25, 0x50, 0x44, 0x46], docx: [0x50, 0x4b, 0x03, 0x04], doc: [0xd0, 0xcf, 0x11, 0xe0] }
for (const item of listed) {
  const bytes = fs.readFileSync(new URL(item.file, directory))
  assert.ok(signatures[item.extension].every((byte, index) => bytes[index] === byte), `${item.file} is not a valid .${item.extension} file`)
}
console.log(`PASS CV downloads: ${listed.map(item => `${item.file} (${item.format})`).join(', ')}`)
