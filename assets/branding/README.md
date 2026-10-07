# KAJU branding

`kaju_brand.py` is the shared source for the KAJU wordmark and the reference's triangular line logo. Lobby, elevator and billboard generators use the same paths. `kaju-logo.png` is a generated reference preview.

## Focused update

```sh
python assets/branding/prepare_kaju_artwork.py
blender --background assets/kaze-lobby/kaze-lobby-walkthrough.blend --python-exit-code 1 --python assets/branding/apply_kaju_branding.py -- --model lobby
blender --background assets/kaze-elevator/kaze-elevator-journey.blend --python-exit-code 1 --python assets/branding/apply_kaju_branding.py -- --model elevator
blender --background assets/cyber-city/monochrome-city-solid-tower.blend --python-exit-code 1 --python assets/branding/apply_kaju_branding.py -- --model city
blender --background assets/cyber-city/cyber-city-walkthrough.blend --python-exit-code 1 --python assets/branding/apply_kaju_branding.py -- --model original-city
```

The focused authoring update preserves sampled camera/door/actor transforms and checks all FONT bodies. It replaces the lobby/elevator crest curves, updates visible lettering, and repacks the owned brand/fallback posters. The supplied production portrait and other campaign artwork are preserved. Native scene/object IDs and `kaze.png` filenames remain stable integration identifiers; their visible content is KAJU.

Regenerate the affected browser packages and integration copies using the [journey workflow](../journey/WORKFLOW.md). Check the logo curves and exported segments with `verify_kaju_branding.py` after export.
