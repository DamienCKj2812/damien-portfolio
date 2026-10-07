# Damien's immersive portfolio

React + Vite + React Three Fiber/Three.js. The full-viewport experience connects a monochrome city, KAJU lobby, interactive elevator, and four portfolio rooms. Navigation and content stay inside the 3D journey.

```sh
npm ci
npm run dev
```

Open **http://localhost:5173/damien-portfolio/** (use the port Vite reports).

## Guides

- [Development, checks, deployment](docs/development.md)
- [App architecture, loading, and interactions](docs/architecture.md)
- [Interaction sound effects and future-control convention](docs/sound-effects.md)
- [Shared media ownership, originals and browser copies](assets/media/README.md)
- [Planned video banners and complete preloading](docs/roadmap.md)
- [Project catalogue: client, academic and personal work](docs/project-catalogue.md)
- [Agent entrypoint](AGENTS.md) and [asset-wide rules](assets/AGENTS.md)
- [Integration/export workflow](assets/journey/WORKFLOW.md)

## Authored models

| Area | Main file | Local documentation |
| --- | --- | --- |
| City | `assets/cyber-city/monochrome-city-solid-tower.blend` (production); `cyber-city-walkthrough.blend` (architecture/motion source) | [City](assets/cyber-city/README.md) |
| Lobby | `assets/kaze-lobby/kaze-lobby-walkthrough.blend` | [Lobby](assets/kaze-lobby/README.md) |
| Elevator | `assets/kaze-elevator/kaze-elevator-journey.blend` | [Elevator](assets/kaze-elevator/README.md) |
| 01 / About | `assets/about-office/about-office.blend` | [Office](assets/about-office/README.md) |
| About profile photo | `assets/portrait/build_pixel_portrait.py` | [Pixel-grid portrait](assets/portrait/README.md) |
| 02 / Skills | `assets/skills-gallery/skills-gallery.blend` | [Gallery](assets/skills-gallery/README.md) |
| 03 / Projects | `assets/project-hallway/project-hallway.blend` | [Hallway](assets/project-hallway/README.md) |
| 04 / Experience & Education | `assets/timeline-observatory/timeline-observatory.blend` | [Observatory](assets/timeline-observatory/README.md) |

Each model directory has scoped `AGENTS.md` and model-specific authoring documentation. Integration previews in `assets/journey/` are derived outputs; browser packages in `public/models/` are generated independently of the authored masters.

Edit shared identity, Observer, and contact content in `src/data/portfolio.js`. Project exhibits use `assets/project-hallway/projects.json`; timeline exhibits use `assets/timeline-observatory/milestones.json`. Development sample records are labelled as samples.
