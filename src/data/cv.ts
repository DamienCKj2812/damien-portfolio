import content from './cv.json'
import { parseCv } from '../types/cv'
import type { CvFile } from '../types/cv'

const cv = parseCv(content)
const download = (file: CvFile) => ({ ...file, href: `${import.meta.env.BASE_URL}cv/${encodeURIComponent(file.file)}` })

export const cvDownload = { primary: download(cv.primary), alternates: cv.alternates.map(download), pdf: download(cv.pdf).href }
