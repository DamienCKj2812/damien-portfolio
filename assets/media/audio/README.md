# Audio source assets

Canonical originals live here in `music/` and `effects/`. Browser copies are generated at `public/media/audio/` by `scripts/sync_media_assets.mjs`. Paths and immutable byte hashes are registered in [`../manifest.json`](../manifest.json); original supplied audio is never re-encoded during deployment.

## Interaction effects

Supplied by the portfolio owner, copied from Downloads without modifying the originals:

| File | Source filename | Duration | Format | SHA-256 |
| --- | --- | --- | --- | --- |
| `environment-click.mp3` | `blip.mp3` | 0.313 s | MP3 / 44.1 kHz / stereo | `381dd8c3fc8618a5d827c17da8b07b06a89f311d07dd0d60bad85be4e63bbb86` |
| `system-click.mp3` | `click.mp3` | 0.575 s | MP3 / 44.1 kHz / stereo | `2af7e83b752fa57461e9d266cd56f1c478f6f1c1f52c40de0ed4f29b83c7f2ab` |
| `effects/light-saber.mp3` | Supplied `light-saber.mp3` | 0.768 s | MP3 / 48 kHz / stereo | `24691c12597588c3788813a85007165dbd52fb2508f0e9c9472fb852c098eb0e` |
| `effects/sci-fi-door.mp3` | Supplied `sci-fi-door.mp3` | 1.896 s | MP3 / 24 kHz / stereo | `774c7c09c6182251989eddf58b1aa7e43dab8ff2c6546b761aaeb07e5826655b` |

Hover/focus playback was retired at the owner's request. The former `ui-hover.mp3` is now `environment-click.mp3` and plays only when activating an environment item (Observer, exhibit, physical elevator switch). The former `ui-click.mp3` is now `system-click.mp3` for system menus, audio/settings and other UI controls. Renaming preserves the original bytes/hashes.

Use the shared sound-effects provider for every new interactive item, including all levels and elevator controls. Implementation and extension rules: [Interaction sounds](../../../docs/sound-effects.md).

The lightsaber clip is a discrete Level 03 category-portal crossing effect, played once when passing each Academic/Personal threshold in either direction. It uses the SFX setting, not the music setting. The supplied original is preserved under `effects/`; only its exact-byte browser copy is deployed.

The sci-fi door clip plays on the main gate and elevator opening motions. On returning to the cabin it is reused with a 250 ms delay after closing begins; reduced-motion returns defer the cue until after arrival. It follows the same SFX mute/volume settings and is cancelled when a trip is cancelled, the page hides or audio is muted/disposed. The source MP3 is copied unchanged.

## Background music

- Track: **Cyberpunk Suspense**
- Creator: **leberch**
- Source: https://pixabay.com/music/ambient-cyberpunk-suspense-375260/
- License information: https://pixabay.com/service/license-summary/
- File: `music/leberch-cyberpunk-suspense-375260.mp3`, supplied by the portfolio owner and originally moved from Downloads.
- SHA-256: `e99a8da8dd104a26f8b92de5948081029075d52a05ddbc5e8cd8b3dbff7aef01`

The website credits the track beside its music controls. This is a background-music asset, not a standalone music download offering. Keep any Pixabay download/license certificate with the owner's records.
