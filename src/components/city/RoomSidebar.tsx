import { useCallback, useEffect, useId, useLayoutEffect, useRef, useState } from 'react'
import type { ButtonHTMLAttributes, ReactNode } from 'react'
import useSoundEffects from '../../audio/useSoundEffects'

export interface RoomSidebarProps {
  number: string
  chapter: string
  title: string
  description: string
  status?: ReactNode
  children?: ReactNode
  controls?: ReactNode
  exitHint?: ReactNode
}

export interface RoomIndexItem {
  id: string
  title: string
  buttonId?: string
  locked?: boolean
  dialog?: boolean
  featured?: boolean
}

export interface RoomIndexProps<T extends RoomIndexItem> {
  label: string
  items: readonly T[]
  selected?: string | null
  onSelect: (id: string) => void
  renderDetail?: (item: T) => ReactNode
}

export interface RoomActionProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  shortcut?: string
}

export interface RoomMoreControlsProps {
  children?: ReactNode
}

export default function RoomSidebar(props: RoomSidebarProps) {
  return <PersistentRoomSidebar key={props.number} {...props} />
}

function PersistentRoomSidebar({ number, chapter, title, description, status, children, controls, exitHint }: RoomSidebarProps) {
  const { click: playClick } = useSoundEffects()
  const storageKey = `damien-portfolio:room-menu:${number}`
  const [collapsed, setCollapsed] = useState(() => {
    try { return window.localStorage.getItem(storageKey) === 'collapsed' }
    catch { return false }
  })
  const toggleRef = useRef<HTMLButtonElement>(null)
  const infoRef = useRef<HTMLButtonElement>(null)
  const focusAfterToggle = useRef(false)
  const bodyId = useId()
  const compactChapter = chapter === 'Experience & education' ? 'Timeline' : chapter === 'About me' ? 'About' : chapter
  const toggle = useCallback(() => {
    focusAfterToggle.current = true
    setCollapsed(current => !current)
  }, [])
  useEffect(() => {
    try { window.localStorage.setItem(storageKey, collapsed ? 'collapsed' : 'expanded') }
    catch { /* Keep the menu usable when browser storage is unavailable. */ }
  }, [storageKey, collapsed])
  useLayoutEffect(() => {
    if (!focusAfterToggle.current) return
    focusAfterToggle.current = false
    const target = collapsed ? infoRef.current : toggleRef.current
    target?.focus({ preventScroll: true })
  }, [collapsed])
  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key.toLowerCase() !== 'm' || event.repeat || event.defaultPrevented || event.ctrlKey || event.metaKey || event.altKey) return
      if (event.target instanceof Element && event.target.closest('input, textarea, select, [contenteditable="true"], [role="dialog"]')) return
      if (document.querySelector('[role="dialog"][aria-modal="true"]')) return
      event.preventDefault()
      playClick()
      toggle()
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [toggle, playClick])
  return <>
  <aside className="room-interface" data-collapsed={collapsed} aria-label={`${chapter} floor menu`} aria-hidden={collapsed} inert={collapsed}>
    <header className="room-sidebar-header">
      <div className="room-sidebar-topline">
        <p className="room-level"><span className="room-level-number">{number}</span><span aria-hidden="true">/</span><span>{chapter}</span></p>
        <button ref={toggleRef} type="button" className="room-menu-toggle" aria-label="Hide menu" aria-expanded={!collapsed} aria-controls={bodyId} aria-keyshortcuts="M" onClick={toggle}>Hide <kbd aria-hidden="true">M</kbd></button>
      </div>
      <h2 id="room-title">{title}</h2>
      <p className="room-intro">{description}</p>
    </header>
    <div id={bodyId} className="room-sidebar-body">
      {status && <div className="room-sidebar-status">{status}</div>}
      <div className="room-sidebar-content">{children}</div>
      <div className="room-sidebar-footer">
        {controls}
        <p className="room-exit-hint"><span aria-hidden="true">↑</span>{exitHint ? <span>{exitHint}</span> : <span>Scroll up past the entrance to return.<br/><span className="room-exit-keyboard">Keyboard: Home, then Page Up.</span><span className="room-exit-touch">Swipe down to move back. Drag sideways to look.</span></span>}</p>
      </div>
    </div>
  </aside>
  <aside className="room-menu-tab" data-visible={collapsed} aria-label={`${chapter} floor information`} aria-hidden={!collapsed} inert={!collapsed}>
    <span className="room-tab-number">{number}</span>
    <span className="room-tab-chapter">{compactChapter}</span>
    <button ref={infoRef} type="button" aria-label="Show menu" aria-expanded={!collapsed} aria-controls={bodyId} aria-keyshortcuts="M" onClick={toggle}>Info <kbd aria-hidden="true">M</kbd></button>
  </aside>
  </>
}

export function RoomIndex<T extends RoomIndexItem>({ label, items, selected, onSelect, renderDetail }: RoomIndexProps<T>) {
  const current = items.findIndex(item => item.id === selected)
  return <section className="room-index" aria-label={label}>
    <div className="room-index-heading"><h3>{label}</h3><span aria-hidden="true">{current < 0 ? '—' : String(current + 1).padStart(2, '0')} / {String(items.length).padStart(2, '0')}</span></div>
    <ol className="room-index-list">
      {items.map((item, index) => <li key={item.id} data-active={item.id === selected}>
        <button type="button" id={item.buttonId} className="room-index-button" disabled={item.locked} aria-haspopup={item.dialog ? 'dialog' : undefined} aria-current={item.id === selected ? 'true' : undefined} onClick={() => onSelect(item.id)}>
          <span className="room-index-number" aria-hidden="true">{String(index + 1).padStart(2, '0')}</span><span>{item.title.replaceAll('\n', ' ')}</span>
          {item.featured && <span className="room-index-featured">Featured FYP</span>}
        </button>
        {renderDetail && <div className="room-index-detail-shell" data-open={item.id === selected} aria-hidden={item.id !== selected} inert={item.id !== selected}><div className="room-index-detail-clip"><div className="room-index-detail">{renderDetail(item)}</div></div></div>}
      </li>)}
    </ol>
  </section>
}

export function RoomAction({ shortcut, children, ...props }: RoomActionProps) {
  return <button type="button" className="room-action" {...props}>{shortcut && <kbd aria-hidden="true">{shortcut}</kbd>}<span>{children}</span></button>
}

export function RoomMoreControls({ children }: RoomMoreControlsProps) {
  return <details className="room-more-controls"><summary>More controls <span aria-hidden="true">+</span></summary><div className="room-more-content">{children}</div></details>
}
