import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { isCityManifest, isElevatorManifest, isLobbyManifest, parseJourneyConfig, parseSceneManifest } from '../src/types/sceneValidation.ts'
import type { AboutManifest, CityManifest, ElevatorManifest, ExperienceManifest, LobbyManifest, ProjectsManifest, SkillsManifest } from '../src/types/scene.ts'
import { listValue, numberValue, objectValue, optionalString, parseCaseSections, stringValue } from '../src/types/portfolio.ts'

export function jsonFile(path: string | URL): unknown {
  return JSON.parse(readFileSync(path, 'utf8')) as unknown
}

type SceneManifests = {
  city: CityManifest; lobby: LobbyManifest; elevator: ElevatorManifest
  about: AboutManifest; skills: SkillsManifest; projects: ProjectsManifest; experience: ExperienceManifest
}
type SceneKind = keyof SceneManifests
type ManifestFor<K extends SceneKind> = SceneManifests[K]

export function sceneFile<K extends SceneKind>(path: string | URL, kind: K): ManifestFor<K> {
  const manifest = parseSceneManifest(jsonFile(path))
  if (kind === 'city') assert.ok(isCityManifest(manifest))
  else if (kind === 'lobby') assert.ok(isLobbyManifest(manifest))
  else if (kind === 'elevator') assert.ok(isElevatorManifest(manifest))
  else assert.equal(manifest.level, kind)
  return manifest as ManifestFor<K>
}

export function journeyFile(path: string | URL) { return parseJourneyConfig(jsonFile(path)) }

export function hallwayLayoutFile(path: string | URL) {
  const data = objectValue(jsonFile(path), 'hallway layout')
  const ceiling = objectValue(data.ceiling, 'hallway layout.ceiling')
  return {
    widthMeters: numberValue(data.widthMeters, 'layout.widthMeters'),
    lengthMeters: numberValue(data.lengthMeters, 'layout.lengthMeters'),
    projectBaySpacingMeters: numberValue(data.projectBaySpacingMeters, 'layout.projectBaySpacingMeters'),
    rightDisplayStaggerMeters: numberValue(data.rightDisplayStaggerMeters, 'layout.rightDisplayStaggerMeters'),
    ceiling: {
      ribCount: numberValue(ceiling.ribCount, 'ceiling.ribCount'),
      curvedLightRails: numberValue(ceiling.curvedLightRails, 'ceiling.curvedLightRails'),
      perimeterLightRails: numberValue(ceiling.perimeterLightRails, 'ceiling.perimeterLightRails'),
    },
  }
}

export function categoryContentFile(path: string | URL) {
  const data = objectValue(jsonFile(path), 'project content')
  return {
    catalogueSourceHash: stringValue(data.catalogueSourceHash, 'content.catalogueSourceHash'),
    categories: listValue(data.categories, 'content.categories', (value, path) => {
      const item = objectValue(value, path)
      return { id: stringValue(item.id, `${path}.id`) }
    }),
    projects: listValue(data.projects, 'content.projects', (value, path) => {
      const item = objectValue(value, path)
      assert.ok(item.repositoryLinksRestricted === undefined || typeof item.repositoryLinksRestricted === 'boolean', `${path}.repositoryLinksRestricted: expected boolean`)
      return { ...item, id: stringValue(item.id, `${path}.id`), section: stringValue(item.section, `${path}.section`),
        catalogueSections: parseCaseSections(item.catalogueSections, `${path}.catalogueSections`),
        ...(item.repositoryLinksRestricted === undefined ? {} : { repositoryLinksRestricted: item.repositoryLinksRestricted === true }),
        liveUrl: optionalString(item.liveUrl, `${path}.liveUrl`),
        liveLabel: optionalString(item.liveLabel, `${path}.liveLabel`),
        ...(item.url === undefined ? {} : { url: item.url === null ? null : stringValue(item.url, `${path}.url`) }),
        ...(item.repositories === undefined ? {} : { repositories: listValue(item.repositories, `${path}.repositories`, (value,path)=>{
          const repository=objectValue(value,path)
          return {url:stringValue(repository.url,`${path}.url`)}
        }) }),
        ...(item.siteLinks === undefined ? {} : { siteLinks: listValue(item.siteLinks, `${path}.siteLinks`, (value,path)=>{
          const link=objectValue(value,path)
          return {url:stringValue(link.url,`${path}.url`),label:stringValue(link.label,`${path}.label`)}
        }) }),
      }
    }),
  }
}
