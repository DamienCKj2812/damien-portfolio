import { listValue, objectValue, stringValue } from './portfolio'

// CV files are uploaded to public/cv/ as-is; cv.json only names them, primary download first.
// At least one PDF is required: the 3D office printer prints it.
const formats = { pdf: 'PDF', docx: 'Word', doc: 'Word' } as const
type Extension = keyof typeof formats

export function parseCv(value: unknown) {
  const data = objectValue(value, 'cv')
  const files = listValue(data.files, 'cv.files', (value, path) => {
    const file = stringValue(value, path)
    if (/[/\\]/.test(file)) throw new Error(`${path}: give only the file name inside public/cv/`)
    const extension = file.slice(file.lastIndexOf('.') + 1).toLowerCase()
    if (!(extension in formats)) throw new Error(`${path}: expected a .pdf, .docx or .doc file`)
    return { file, extension: extension as Extension, format: formats[extension as Extension] }
  })
  const [primary, ...alternates] = files
  if (!primary) throw new Error('cv.files: list at least one file')
  if (new Set(files.map(item => item.file)).size !== files.length) throw new Error('cv.files: duplicate file names')
  const pdf = files.find(item => item.extension === 'pdf')
  if (!pdf) throw new Error('cv.files: include a .pdf (Word: File > Save As > PDF); printing uses it')
  return { primary, alternates, pdf }
}

export type CvFile = ReturnType<typeof parseCv>['primary']
