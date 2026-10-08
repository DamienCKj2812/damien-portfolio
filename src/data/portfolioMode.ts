export type PortfolioMode = 'entry' | '2d' | '3d'
export const MODE_KEY = 'damienckj-entry-mode'

export function rememberedMode(): '2d' | '3d' | null {
  try {
    const value = localStorage.getItem(MODE_KEY)
    return value === '2d' || value === '3d' ? value : null
  } catch { return null }
}

export function initialMode(): PortfolioMode {
  const value = new URL(window.location.href).searchParams.get('mode')
  return value === 'entry' || value === '2d' || value === '3d' ? value : rememberedMode() ?? 'entry'
}

export function saveMode(mode: PortfolioMode, remember: boolean) {
  try {
    if (remember && mode !== 'entry') localStorage.setItem(MODE_KEY, mode)
    else localStorage.removeItem(MODE_KEY)
  } catch { /* The current visit still works when storage is unavailable. */ }
}
