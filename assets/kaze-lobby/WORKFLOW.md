# Lobby workflow

Normal modeling edits belong in the main file. Full generation replaces manual edits; one previous save is retained.

```sh
blender --background --factory-startup --python-exit-code 1 --python assets/kaze-lobby/rebuild_lobby.py -- --render
```

Omit `-- --render` to skip previews. For a separate output directory:

```sh
blender --background --factory-startup --python-exit-code 1 --python assets/kaze-lobby/rebuild_lobby.py -- --output-dir /tmp/opencode/lobby-check
```

The entrypoint builds architecture and navigation in memory and saves only `kaze-lobby-walkthrough.blend`. Edit `ROUTE`, `LOOK`, `LENS` and timing in `add_navigation.py` before intentional regeneration. Earlier one-off design patches are construction history, not a safe update sequence for the finished rig.

The full rebuild also installs `fish_motion.py`: a shared body/head sway, nested tail swish and individual fin flutter. Point membranes, silhouettes and fin rays use the same native part rig. The browser samples each closest animated ancestor's world pose on the visible-lobby clock, independently of scroll; projection hardware and halos are static. Validate the native rig and generated package with:

```sh
blender --background assets/kaze-lobby/kaze-lobby-walkthrough.blend --python-exit-code 1 --python assets/kaze-lobby/verify_fish_motion.py
node assets/kaze-lobby/verify_fish_motion.mjs
```

For an animated fixed-camera preview: `blender --background assets/kaze-lobby/kaze-lobby-walkthrough.blend --python-exit-code 1 --python assets/kaze-lobby/render_fish_preview.py`. It writes `holographic-fish-swimming.gif` without saving the master.

## Browser package

To remove the goldfish exhibit's sub-ceiling from an existing master, run `blender --background assets/kaze-lobby/kaze-lobby-walkthrough.blend --python-exit-code 1 --python assets/kaze-lobby/remove_fish_canopy.py`, then re-export below. This removes the canopy slab, its feature edges and its front light; full generation also omits them. The fish rig and projection halos remain as authored.

For role-based NPC behavior updates without rebuilding architecture:

```sh
blender --background assets/kaze-lobby/kaze-lobby-walkthrough.blend --python-exit-code 1 --python assets/kaze-lobby/add_npc_motion.py
blender --background assets/kaze-lobby/kaze-lobby-walkthrough.blend --python-exit-code 1 --python assets/kaze-lobby/verify_npc_motion.py
```

The installer gives all 17 people staggered activity loops and preserves sampled camera/door transforms. Seated visitors gesture or nod, reception waves/types, and other visitors use phone, conversation or looking actions. Phones/books/cups follow the hand motion. The existing visible-lobby clock plays NPCs and accessories independently of scroll; offscreen/hidden/reduced-motion playback suspends. Re-export the lobby package below after installing.

To remove the legacy escalator rider from an existing master, run `blender --background assets/kaze-lobby/kaze-lobby-walkthrough.blend --python-exit-code 1 --python assets/kaze-lobby/remove_escalator_npc.py`, then re-export below. Full generation omits this NPC.

For the focused pillar-to-ceiling line-weight correction, run:

```sh
blender --background assets/kaze-lobby/kaze-lobby-walkthrough.blend --python-exit-code 1 --python assets/kaze-lobby/refine_pillar_fillets.py
```

This matches the two curved attachments to the fine silver structural edges at a 4 mm radius, removing their glow classification. It preserves the joint coordinates and checks sampled animated transforms before saving the master. Full generation uses the same material and radius. Re-export the lobby package after this correction.

For the focused landing-status alignment correction, run:

```sh
blender --background assets/kaze-lobby/kaze-lobby-walkthrough.blend --python-exit-code 1 --python assets/kaze-lobby/align_elevator_displays.py
```

This saves the four floor indicators at the shared Z=9.40 baseline and checks that camera and R1 leaf motion are unchanged. Full architecture/navigation generation uses the same baseline. Re-export the lobby and refresh the derived integration after this correction.

```sh
blender --background assets/kaze-lobby/kaze-lobby-walkthrough.blend --python-exit-code 1 --python assets/journey/export_browser_lobby.py
node assets/kaze-lobby/verify_browser_npcs.mjs
node assets/journey/verify_rooms.mjs
```

The exporter writes `public/models/lobby/` without saving the master. It fits the R1 aperture/doors and removes the placeholder in memory. Rebuild the connected preview when doorway/shell/alignment changes; see [journey workflow](../journey/WORKFLOW.md).

## Standalone interior handoff

At frame 1020, R1 is open. Use `navigation-handoff.json` for the final camera quaternion/lens and door positions. Entrance into the cabin is +Y; threshold Y=23.75 and upper floor Z=6.12.

When authoring a native interior connection, remove **Lobby • Navigation / R1 interior handoff / black backing** and carve/replace the R1 wall surround/rear wall as needed. Preserve leaves, parented outline curves, pockets, portal and end pose. For the browser, this aperture work is already handled by the read-only integration/export scripts.
