import type { ReactNode } from 'react'

export interface SectionProps {
  id: string
  label: string
  title: string
  description?: string
  children?: ReactNode
}

export default function Section({ id, label, title, description, children }: SectionProps) {
  return (
    <section className="section" id={id} aria-labelledby={`${id}-title`}>
      <p className="eyebrow">{label}</p>
      <h2 id={`${id}-title`}>{title}</h2>
      {description && <p>{description}</p>}
      {children}
    </section>
  )
}
