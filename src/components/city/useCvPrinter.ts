import { useCallback } from 'react'
import { cvDownload } from '../../data/cv'

/** Let the browser's native PDF viewer own viewing, downloading and printing. */
export default function useCvPrinter() {
  return useCallback(() => {
    window.open(cvDownload.pdf, '_blank', 'noopener,noreferrer')
  }, [])
}
