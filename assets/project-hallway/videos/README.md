# Project video assets

The Projects hallway owns the MyRumawip, MyReport, DWMLight and Fedora Dotfiles recordings.

## Original recordings

Keep local uploads under `originals/`, grouped by project:

```text
assets/project-hallway/videos/originals/
├── myrumawip/
│   ├── myrumawip-full.mp4
│   └── myrumawip-preview.mp4
├── myreport/
│   ├── myreport-full.mp4
│   └── myreport-preview.mp4
├── dwmlight/
│   ├── dwmlight-full.mp4
│   └── dwmlight-preview.mp4
└── fedora-dotfiles/
    └── fedora-dotfiles.mp4
```

These supplied recordings were moved from the repository root without
changing their bytes. Originals remain local, Git-ignored authoring inputs.
They are not required by development, CI or deployment.

## Browser assets

Prepared, tracked assets live in `public/videos/`. Each project has:

- `<project>-preview.mp4`: lightweight preview.
- `<project>-full.mp4`: full walkthrough.
- `<project>-preview-h264.mp4` and `<project>-full-h264.mp4`: compatibility copies.
- `<project>-poster.jpg`: static fallback before a decoded frame is ready.

MyRumawip's prepared full walkthrough and H.264 compatibility copy are trimmed
to exactly **46 seconds**, retaining the first 46 seconds at 1920 × 1080 / 30 FPS.
The local original recording remains unchanged.

Fedora Dotfiles uses one **28.03-second, 1080p / 30 FPS** recording for both
preview and full playback. Both paths point to `videos/fedora-dotfiles.mp4`;
both compatibility paths point to `videos/fedora-dotfiles-h264.mp4`. Its poster
is `videos/fedora-dotfiles-poster.jpg`. The primary clip is losslessly remuxed
for fast-start playback, and the original remains untouched in its local folder.
Shared preview/full clips may use the full-video budget (below 10 MB), while
separate lightweight previews stay below 4 MB; the video verifier checks both.

Vite copies this directory to `dist/videos/` during a production build.
`build_project_catalogue.py` defines the browser paths in `projects.json`;
the room exporter publishes them in `public/models/rooms/projects/scene.json`.
The runtime prefixes those paths with `import.meta.env.BASE_URL`.

When replacing a recording, store its original in the matching local project
folder and prepare the corresponding browser files together. Keep established
browser filenames when replacing bytes; changing a browser path requires
regenerating the catalogue and exported Projects package. Do not put recordings
in the repository root.

Check browser assets with:

```sh
node --import tsx scripts/verify_project_video.mts
npm run build
node --import tsx scripts/verify_project_video_browser.mts
```
