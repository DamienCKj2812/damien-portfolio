import manifest from '../../assets/media/manifest.json'
import { parseMediaManifest } from '../types/portfolio'

// Browser media URLs are assembled in one place and respect the repository-site
// base path. Authored originals and model-local textures never become imports.
const files=parseMediaManifest(manifest).files
export const mediaPaths: Readonly<Record<string,string>>=Object.freeze(Object.fromEntries(Object.entries(files).flatMap(([id,asset])=>asset.publicPath?[[id,asset.publicPath]]:[])))
export const mediaUrls: Readonly<Record<string,string>>=Object.freeze(Object.fromEntries(Object.entries(mediaPaths).map(([id,path])=>[id,`${import.meta.env.BASE_URL}${path}`])))
