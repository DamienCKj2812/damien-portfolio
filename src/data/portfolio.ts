import content from './portfolio.json'
import portraitManifest from '../../assets/portrait/image-manifest.json'
import { parsePortfolio, parsePortraitManifest } from '../types/portfolio'
import type { Portfolio } from '../types/portfolio'

// Authored copy is plain shared JSON; generated portrait paths remain manifest-owned.
const data = parsePortfolio(content)
const portraitAsset = parsePortraitManifest(portraitManifest)

export const portfolio: Portfolio = {
  ...data,
  about: {
    ...data.about,
    profile: {
      ...data.about.profile,
      portrait: {
        ...data.about.profile.portrait,
        src: `${portraitAsset.image}?v=${portraitAsset.assetHash}`,
        originalSrc: portraitAsset.originalImage ? `${portraitAsset.originalImage}?v=${portraitAsset.originalAssetHash}` : null,
        cellSize: portraitAsset.cellSize,
      },
    },
  },
}
