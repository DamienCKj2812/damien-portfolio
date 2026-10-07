import manifest from '../../assets/media/manifest.json'

// Browser media URLs are assembled in one place and respect the repository-site
// base path. Authored originals and model-local textures never become imports.
export const mediaPaths=Object.freeze(Object.fromEntries(Object.entries(manifest.files).filter(([,asset])=>asset.publicPath).map(([id,asset])=>[id,asset.publicPath])))
export const mediaUrls=Object.freeze(Object.fromEntries(Object.entries(mediaPaths).map(([id,path])=>[id,`${import.meta.env.BASE_URL}${path}`])))
