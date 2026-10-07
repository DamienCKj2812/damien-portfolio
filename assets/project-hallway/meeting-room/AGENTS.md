# Project meeting-room guidance

- This is an archived authoring asset, not a website scene. Its View more controls and browser package were removed. Never add it to elevator floor destinations.
- Master: `project-meeting-room.blend`. Rebuild with `blender --background --python-exit-code 1 --python assets/project-hallway/meeting-room/build_meeting_room.py -- --no-render`; omit `--no-render` for the preview.
- `room.json` retains historical export/camera configuration. Do not regenerate `public/models/rooms/project-meeting/` for deployment; website verification requires that retired package to be absent. Coordinates remain Blender Z-up.
- The screen is a native UV quad tagged `meeting_screen`; its former dynamic browser presentation has been removed. Do not invent project achievements or duplicate hallway content.
- Keep the authored model static, with no visitors or spotlight fixtures. Chairs, conference table, glazed skyline wall and ceiling light outlines follow the black-and-white reference.
