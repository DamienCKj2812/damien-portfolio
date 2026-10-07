# Connected portfolio journey

This directory owns integration copies and browser exporters, not the authored model masters. The connected entry runs city → lobby → cabin, then loads one of four rooms on floor selection.

- [Agent instructions](AGENTS.md)
- [Rebuild/export/verification sequence](WORKFLOW.md)
- [Alignment, geometry clearance and runtime handoffs](DESIGN.md)
- [Runtime architecture](../../docs/architecture.md)

**`portfolio-journey.blend`** is the generated three-area entry preview, stopping at global 1521 for floor choice. **`city-lobby-walkthrough.blend`** is its preceding derived integration stage. Neither replaces a sibling master.

Routing source: **`room-destinations.json`**. Generated browser map: **`public/models/journey.json`**.

| Level | Authored room | Package |
| --- | --- | --- |
| 01 | [About office](../about-office/README.md) | `public/models/rooms/about/` |
| 02 | [Skills gallery](../skills-gallery/README.md) | `public/models/rooms/skills/` |
| 03 | [Project hallway](../project-hallway/README.md) | `public/models/rooms/projects/` |
| 04 | [Timeline observatory](../timeline-observatory/README.md) | `public/models/rooms/experience/` |
