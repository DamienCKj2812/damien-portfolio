# Main-tower monochrome displays

Generated from the original billboard artwork by `make_monochrome_ads.py`.
These grayscale images are used on the solid hero tower only.

`shaping-a-brighter-tomorrow.jpg` replaces `nexus.png` on the curved NEXUS panel. `prepare_nexus_banner.py` fills the panel edge-to-edge with a proportional center crop (no side padding), and `replace_nexus_banner.py` packs it into production. Full ad/tower generation preserves the override.

`drive-the-next-horizon.jpg` replaces `drive.png` on the clean-mobility banner. `prepare_drive_banner.py` fills the panel with a proportional crop biased toward the headline/logo, without padding, and `replace_drive_banner.py` packs it into production. Full ad/tower generation preserves the override.

`black-hole.jpg` replaces `portal.png` on the SYNTHETIC REALITIES curved panel. `prepare_black_hole_banner.py` fits the full supplied image/caption with black side padding; `replace_black_hole_banner.py` packs it into production. Full ad/tower generation preserves the override.

`selangor.jpg` replaces the NEW HORIZONS/`landscape.png` artwork on the curved landscape display. `prepare_selangor_banner.py` trims the source's outer black background and fills the panel edge-to-edge with a proportional crop, without padding. The monochrome-ad and solid-tower generators preserve the override.

`portrait.jpg` is the owner's custom cyborg long portrait, prepared by `prepare_portrait_banner.py` from `../banner-artwork/portrait-source.png`. It replaces `portrait.png` on the largest production display. The source image is retained separately; the original generated PNG remains available for the original artwork/fallback. Full monochrome-ad generation prepares the custom JPEG when its source is present.
