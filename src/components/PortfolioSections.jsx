import Section from './Section.jsx'

const cardClassName = 'rounded-xl border border-[#292a31] bg-[#191a20] p-6'

function SkillList({ items, label }) {
  return (
    <ul className="mt-4 flex flex-wrap gap-2" aria-label={label}>
      {items.map((item) => (
        <li key={item} className="rounded-full border border-[#35363e] px-3 py-1 text-sm text-[#b4b5be]">{item}</li>
      ))}
    </ul>
  )
}

function ContentLinks({ links }) {
  return (
    <div className="flex flex-wrap gap-6">
      {links.map((link) => {
        const isExternal = /^https?:\/\//.test(link.href)
        return (
          <a
            key={link.id}
            className="text-link"
            href={link.href}
            target={isExternal ? '_blank' : undefined}
            rel={isExternal ? 'noopener noreferrer' : undefined}
          >
            {link.label} <span aria-hidden="true">↗</span>
          </a>
        )
      })}
    </div>
  )
}

export function Hero({ name, hero }) {
  return (
    <section className="hero" aria-labelledby="hero-title">
      <p className="eyebrow">{hero.label}</p>
      <h1 id="hero-title">Hi, I’m {name}.<br /><span>{hero.headline}</span></h1>
      <p className="intro">{hero.introduction}</p>
      <a className="button" href={hero.action.href}>{hero.action.label} <span aria-hidden="true">↗</span></a>
    </section>
  )
}

export function Skills({ data }) {
  return (
    <Section {...data}>
      <div className="mt-7 grid gap-4 sm:grid-cols-2">
        {data.groups.map((group) => (
          <div key={group.id} className={cardClassName}>
            <h3>{group.title}</h3>
            <SkillList items={group.items} label={group.title} />
          </div>
        ))}
      </div>
    </Section>
  )
}

export function Projects({ data }) {
  return (
    <Section {...data}>
      <div className="grid gap-x-4 sm:grid-cols-2">
        {data.items.map((project) => (
          <article key={project.id} className="project-card">
            <span className="tag">{project.status}</span>
            <h3>{project.title}</h3>
            <p>{project.description}</p>
            <SkillList items={project.technologies} label={`${project.title} technologies`} />
            <ContentLinks links={project.links} />
          </article>
        ))}
      </div>
    </Section>
  )
}

export function Journey({ data }) {
  return (
    <Section {...data}>
      <div className="mt-7 grid gap-4 sm:grid-cols-2">
        {data.items.map((entry) => (
          <article key={entry.id} className={cardClassName}>
            <span className="tag">{entry.category}</span>
            <h3>{entry.title}</h3>
            <p className="text-sm text-[#b9f287]">{entry.organization} · {entry.period}</p>
            <p className="mt-3 text-[#b4b5be]">{entry.description}</p>
          </article>
        ))}
      </div>
    </Section>
  )
}

export function Contact({ data }) {
  return <Section {...data}><ContentLinks links={data.links} /></Section>
}
