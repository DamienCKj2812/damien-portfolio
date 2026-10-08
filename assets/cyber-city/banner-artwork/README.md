# Custom city banner artwork

## Geographic Earth hologram

`natural-earth-land-110m.geojson` is the unchanged Natural Earth 1:110m land dataset, retrieved from `nvkelso/natural-earth-vector/geojson/ne_110m_land.geojson`. Natural Earth data is public domain ([terms](https://www.naturalearthdata.com/about/terms-of-use/)). `prepare_earth_detail.py` uses it to generate the separate monochrome `reference-earth.jpg` surface map, with coastline, cloud and reflective-glass shading detail. `earth-detail.json` records the source URL, hashes, output dimensions and front-facing longitude. The map is packed into the authored sphere and exported with the city package.

## Shaping a Brighter Tomorrow / NEXUS curved banner

`shaping-a-brighter-tomorrow-source.png` is the owner's supplied `Downloads/shaping-a-brighter-tomorrow.png`, copied unchanged. It replaces **NEXUS / BETTER TOGETHER** on `Hero display • Curved LED • nexus`.

`prepare_nexus_banner.py` fills the panel edge-to-edge using a proportional center crop matched to the curved surface aspect ratio (radius 2.91 m, span 2.1 radians, height 8 m). The owner requested removing the initial black side padding; the updated fit trims the top/bottom rather than stretching the image. It writes a 1173 × 1536 quality-92 grayscale progressive JPEG to `../textures-monochrome/shaping-a-brighter-tomorrow.jpg`. Crop coordinates, dimensions, sizes and hashes are recorded in `shaping-a-brighter-tomorrow-banner.json`.

`replace_nexus_banner.py` packs the JPEG into production, verifies unchanged geometry/UVs and all object/camera/actor poses at five route frames, and preserves the previous custom banners. Full ad/tower generation retains the override.

## SANCTUM long banner / current cylindrical A bay

`long-banner-source.png` is the owner's supplied `long-banner.png`, moved unchanged into this model-owned folder. The full source retains **HUMANITY WAS A BUG. WE FIXED IT.**, the moon, and **SANCTUM / A CLEANER TOMORROW** lettering.

`prepare_long_banner.py` maps the full image to the combined curved A-bay span, then slices it into the existing upper `logo` and lower `portrait` UV surfaces by their metre-scale heights. It retains the existing physical gap and all source borders/lettering, adding no captions or padding. Outputs are `../textures-monochrome/reference-logo.jpg` and `reference-portrait.jpg`; `../reference-tower-artwork.json` records original bytes/hash, dimensions, canvas rows, panel heights and output hashes. Its CLI updates only these outputs and merges the unchanged right-bay/Earth records.

`replace_long_banner.py` packs the two prepared images into the production master and checks unchanged geometry/UVs, camera and all object/actor poses/visibility/actions at five route frames. `prepare_reference_tower_artwork.py` uses the same preparation during a full rebuild. Publish from the regenerated city/lobby copy, retaining all other displays, sky, crowd and entrance connections. See [the current tower workflow](../WORKFLOW.md#current-reference-based-main-tower).

The scattered glitch-block border on the long banner's right edge is removed
through `remove_long_banner_glitch.py` and omitted by full tower generation.
The thin frame, LED lighting and artwork's own line/square details remain intact.

## Retained cyborg portrait source / earlier layout

The previous cyborg source and single-panel preparation remain as earlier-layout authoring assets. They are no longer the active cylindrical A-bay campaign.

`portrait-source.png` is the owner's supplied **cyborg-long-banner.png**, copied from Downloads without modifying the original. It replaces the previous female glitch portrait on the largest KAJU facade display, `Hero display • KAZE • cyborg campaign • LED display`.

`prepare_portrait_banner.py` center-crops to the existing 5.6 × 28.5 m display aspect ratio (no face stretching), caps height at 2048 pixels, and writes a grayscale progressive JPEG at quality 92 to `../textures-monochrome/portrait.jpg`. `portrait-banner.json` records the source/output hashes, dimensions, crop and sizes.

`replace_portrait_banner.py` is the focused production-master update. It packs the new image and verifies unchanged geometry, UVs, camera and scene/actor poses at five route frames. The architecture/original-motion master retains its original artwork. The monochrome-ad generator and solid-tower generator preserve this custom production override during a full rebuild. See [the city workflow](../WORKFLOW.md).

## Selangor curved banner

`selangor-source.png` is the owner's supplied `Downloads/Selangor.png`, copied unchanged. It replaces the **NEW HORIZONS** artwork on `Hero display • Curved LED • landscape`.

`prepare_selangor_banner.py` trims the source's outer black background around its glowing frame, then fills the curved panel edge-to-edge with a proportional center crop (radius 2.91 m, span 2.1 radians, height 5 m). This replaces the initial padded fit at the owner's request. It writes quality-92 grayscale JPEG `../textures-monochrome/selangor.jpg` at 1252 × 1024, with trim/crop bounds, hashes and sizes recorded in `selangor-banner.json`.

`replace_selangor_banner.py` packs the JPEG into the production master and verifies unchanged geometry, UVs and all camera/actor/object poses at five route frames. The full monochrome-ad/solid-tower generators preserve this override.

## Black-hole / Synthetic Realities curved banner

`black-hole-source.png` is the owner's supplied `Downloads/black-hole.png`, copied unchanged. It replaces the original ring illustration on `Hero display • Curved LED • portal` / **SYNTHETIC REALITIES**.

`prepare_black_hole_banner.py` fits the full image and caption to the panel's surface aspect ratio (radius 2.91 m, span 2.1 radians, height 5.3 m) with black side padding. It writes quality-92 grayscale progressive JPEG `../textures-monochrome/black-hole.jpg` at 1181 × 1024. Source/output dimensions, sizes and hashes are recorded in `black-hole-banner.json`.

`replace_black_hole_banner.py` packs the JPEG into production and verifies unchanged geometry, UVs and object/camera/actor poses at five route frames. The full ad/tower generators preserve this override.

## Drive the Next Horizon banner

`drive-the-next-horizon-source.png` is the owner's supplied `Downloads/drive-the-next-horizon.png`, copied unchanged. It replaces **DRIVE A CLEANER TOMORROW** on `Hero display • Clean mobility campaign • LED display`.

`prepare_drive_banner.py` fills the existing 8.4 × 6.5 m wide panel with a proportional cover crop biased toward the headline/logo (`centering=(0.5,0.9)`), with no padding or stretching. This replaces the initial full-image padded fit at the owner's request. It writes a 1323 × 1024 quality-92 grayscale progressive JPEG to `../textures-monochrome/drive-the-next-horizon.jpg`, with crop coordinates, hashes and sizes recorded in `drive-the-next-horizon-banner.json`.

`replace_drive_banner.py` packs it into production, verifies unchanged geometry/UVs and all scene/camera/actor poses, and retains the earlier portrait, Selangor and black-hole replacements. The full ad/tower generators preserve the override. The connected integration's existing 4 m banner lift above the entrance remains unchanged.
