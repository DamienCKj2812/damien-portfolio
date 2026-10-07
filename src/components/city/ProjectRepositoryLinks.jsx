import { isPublicLink } from '../../data/publicLinks.js'

export default function ProjectRepositoryLinks({ project }) {
  const repositories = project.repositories || (project.url ? [{ id: project.id, title: 'View repository', url: project.url }] : [])
  return repositories.filter(repository=>isPublicLink(repository.url)).map(repository => <a key={repository.id} className="room-detail-action" href={repository.url} target="_blank" rel="noreferrer">
    {repository.title} <span aria-hidden="true">↗</span>
  </a>)
}
