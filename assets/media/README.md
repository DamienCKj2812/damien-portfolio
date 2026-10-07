# Shared media ownership

`manifest.json` is the canonical inventory of shared source files, byte hashes,
browser destinations and attribution. Originals stay unchanged here:

- `audio/music/`: supplied soundtrack and its credit/licence metadata.
- `audio/effects/`: system/environment clicks and portal/door effects.
- `logos/organisations/`: original APU, LYJ and COS supplied artwork.

`scripts/sync_media_assets.mjs` publishes exact-byte audio copies to
`public/media/audio/{music,effects}/`. `src/assets/media.js` owns BASE_URL-aware
runtime URLs. Production builds run the sync automatically; run
`node scripts/verify_media_assets.mjs --dist` to verify the deployed copies.

Organisation logos are cropped/prepared by
`assets/timeline-observatory/prepare_timeline_logos.py`; generated original-color
textures stay in that model's `logos/` directory and are published by its exporter
to `public/models/rooms/experience/logos/` with the package hash. Source and
browser copies are distinct owned outputs, not accidental duplicates.

Model-specific screenshots, animations, packed `.blend` images, textures and
geometry/route packages remain with their model owners. `assets/branding/`
continues to own KAJU's generated vector artwork/reference preview; portrait
authoring and generated portrait files remain in their existing scoped workflow.

When adding media, place the original in the appropriate source subdirectory,
add its ID/hash/provenance and optional `publicPath` to the manifest, sync, then
reference its registered runtime URL. Do not drop source PNG/MP3 files in the
repository root or hand-copy files into unrelated model/browser packages.
