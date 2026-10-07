import type { RepositoryLink } from '../../types/portfolio'
import { isPublicLink } from '../../data/publicLinks'

export interface ProjectRepositoryLinksProps {
  project: { id: string; repositories?: readonly RepositoryLink[]; url?: string | null }
}

export default function ProjectRepositoryLinks({ project }: ProjectRepositoryLinksProps) {
  const repositories = project.repositories || (project.url ? [{ id: project.id, title: 'View repository', url: project.url }] : [])
  return repositories.filter(repository=>isPublicLink(repository.url)).map(repository => <a key={repository.id} className="room-detail-action" href={repository.url} target="_blank" rel="noreferrer">
    {repository.title} <span aria-hidden="true">↗</span>
  </a>)
}
