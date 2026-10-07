import { useLayoutEffect } from 'react'
import { hallwayCategoryAt } from './hallwayCategories.js'
import './hallwayCategories.css'

export default function HallwayCategoryLabel({ navigation, navigationRef, labelRef }) {
  const initial = navigation.categories[0]
  useLayoutEffect(() => {
    const category = hallwayCategoryAt(navigation, navigationRef.current.cameraPosition?.[1] ?? navigationRef.current.position?.[1] ?? navigationRef.current.y)
    if (category && labelRef.current) {
      labelRef.current.textContent = `${String(category.number).padStart(2,'0')} / ${category.title}`
      labelRef.current.dataset.category = category.id
    }
  }, [navigation, navigationRef, labelRef])
  return <aside className="hallway-category-label" aria-label="Current project category" role="status" aria-live="polite">
    <span className="hallway-category-eyebrow">Current category</span>
    <span ref={labelRef} id="hallway-current-category" data-category={initial.id}>{String(initial.number).padStart(2,'0')} / {initial.title}</span>
  </aside>
}
