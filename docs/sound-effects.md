# Click-only interaction sound effects

**Hover and keyboard focus are always silent.** Accepted clicks, taps and discrete keyboard activations use one of two sounds:

| Category | Asset | Original supplied file | Examples |
| --- | --- | --- | --- |
| System / interface | `public/media/audio/effects/system-click.mp3` | `Downloads/click.mp3` (previously `ui-click.mp3`) | Menus, music/effects settings, tour controls, dialogs, detail controls, links |
| Environment / physical item | `public/media/audio/effects/environment-click.mp3` | `Downloads/blip.mp3` (previously `ui-hover.mp3`) | Observer, contact card, exhibit surfaces, AT-AT, timeline picks, elevator floor buttons and return doors/call panels |
| Category portal crossing | `public/media/audio/effects/light-saber.mp3` | Supplied `light-saber.mp3` | Passing the Academic/Personal doorways in Level 03, forward or backward |
| Gate/elevator motion | `public/media/audio/effects/sci-fi-door.mp3` | Supplied `sci-fi-door.mp3` | Main gate opening, lobby R1/cabin door opening, delayed cabin closing on return |

This mapping replaces the earlier hover/click convention at the owner's request. The blip is now an **environment click**, never a hover sound. Canonical originals live in `assets/media/audio/effects/`; `npm run assets:sync` publishes exact-byte browser copies, also automatically before dev and build. Source metadata/hashes are in [the audio asset notes](../assets/media/audio/README.md) and `assets/media/manifest.json`. No Blender/model export change is required.

## Playback and settings

`SoundEffectsProvider` wraps the app and delegates DOM activation; `src/audio/interactionAudio.ts` owns Web Audio buffering/playback. `src/assets/media.ts` resolves the shared manifest's asset URLs using `import.meta.env.BASE_URL` for the `/damien-portfolio/` deployment.

The first visit shows the full-screen **ENTER WITH SOUND?** startup dialog, based on the read-only `Sound Prompt.dc.html` design reference. It uses a blurred/darkened scene backdrop, with the existing city poster as a fallback that fades away once the live scene is loaded, JetBrains Mono, five CSS-animated bars and **YES / MUTED** actions. Enter selects YES from its default focus; M or Escape selects muted. Native button activation and a focus trap remain accessible, and reduced motion stops the bars and fallback transition.

The portfolio loading screen silently buffers music and the four encoded effect files before the sound choice. Fetching bytes does not play either channel, create/resume a Web Audio context or override mute settings. The sound-choice dialog appears after startup scene readiness. YES starts music and unlocks effects directly in the trusted click/keyboard activation. MUTED pauses music and disables effects. The decision is stored under `damien-portfolio:audio-consent`, so refreshing or returning does not repeat the prompt. Remembered enabled music makes one actual automatic playback attempt after scene readiness; `getAutoplayPolicy(audio)` is recorded when available, but the `play()` promise is authoritative. A browser rejection stays **Music ready** and retries on a trusted interaction, without an automatic retry loop. Its hover description explains how to allow browser autoplay, and `data-autoplay-policy` / `data-autoplay-blocked` expose the result for diagnosis. Saved muted music never attempts playback. Effects still create/resume Web Audio only on a real gesture. Synthetic/programmatic clicks cannot enable startup sound. Choices themselves do not play a click effect.

The preferences icon beside Help reopens the same full-screen **ENTER WITH SOUND? / YES / MUTED** interface used on the first visit. YES enables both channels; MUTED/M silences both, saves the choice and closes the prompt. Escape cancels a reopened preferences prompt without changing the saved choice; on the first visit it continues muted. Existing corner Music/SFX controls still allow independent changes. The native dialog traps/restores focus and pauses room input/walking while open. Header tooltips appear on hover and keyboard focus, can be dismissed with Escape, and never request an interaction effect. Help uses the same tooltip behavior; the floor shortcut becomes icon-only on narrow screens to keep all controls visible.

The compact audio panel retains independent Music and SFX toggles after the choice, with a fixed mix rather than volume sliders. Effects use 45% volume, with gain 0.70 for system clicks and 0.45 for the shorter environment blip; music uses its configured level. Preferences remain `{ enabled, volume }` under `damien-portfolio:sound-effects`; music preferences are separate. The explicit startup choice sets both enabled flags; later per-channel changes are remembered independently. Users can enable either channel later after choosing muted.

The music indicator reports playback rather than only the saved enabled flag: **Music ready** waits for activation, **Starting…** covers loading/buffering, **Music on** follows the media `playing` event, **Music off** is explicitly disabled, and **Music unavailable** reports a load/play failure. Its icon, active styling and `aria-pressed` reflect actual playing state. Clicking ready music starts playback rather than toggling an already-enabled preference off.

The bottom-right audio panel sits above any visible `.city-controls` progress bar, including guided-room progress. Without a progress bar, it returns to its normal corner placement. This uses scoped CSS `:has()` rules, without a resize polling or animation loop.

The control row follows `Project Detail v2.dc.html`: four decorative music bars, **MUSIC ON/OFF** and **SFX ON/OFF**, with muted states dimmed. There are no user-facing volume inputs or context-level volume setter. Legacy saved gain values migrate to the fixed mix (music 35%, effects 45%) while enabled/muted choices remain independent. The bars use CSS only and stop when playback pauses; no visualizer timer or Canvas invalidation loop is added. Creator credit remains available below the compact row.

Effects files preload silently during startup; the engine reuses those encoded bytes and its gesture-created decoded buffers. Web Audio unlocks on trusted pointer/keyboard gestures. Duplicate click activations within 50 ms are suppressed across system/environment categories; portal crossings use separate per-door limits. At most four voices overlap. Muting, zero volume, hiding the page or unmounting stop voices and cancel queued sounds. Enabling previously muted effects supplies one system click; disabling immediately silences playback. Sound failures are reported as unavailable during preparation and never block navigation; playback creates no animation/invalidation loop.

### Level 03 portal exception

`hallwayPortalAudio.ts` tracks stable sides of the generated category doorway planes with a 0.3 m dead band. `RoomNavigator` samples the actual main-view camera position on existing demand frames and calls `portalCrossing(id)` once per forward/backward passage. Arrival, card-focus transitions, modals, Home and progress seeks rebaseline silently. Walking/scrolling elsewhere remains silent. The lightsaber cue follows SFX mute/volume and never creates/resumes Web Audio from a render frame; it uses the already gesture-unlocked engine. This is a discrete crossing event, not continuous movement audio.

### Main gate and elevator motion

`doorSoundTiming.ts` follows actual rendered frames for the city gate, lobby R1 and selected cabin opening. Loading holds remain silent until motion starts; standing at an open door does not repeat the cue. Rewinding before the main gate then reopening re-arms it. On return, the closing threshold schedules the same sci-fi clip 250 ms later. Instant reduced-motion returns schedule it after cabin arrival instead. The shared engine owns these finite timers and cancels them/door voices on trip cancellation, new selection, mute, zero volume, hidden page or disposal. No render-frame effect creates or resumes an AudioContext. Normal closing tails can finish after return completes.

## Convention for future interactions

### HTML controls

Enabled buttons, links, summaries, selects, range/checkbox/radio inputs and `[role="button"]` controls get a **system click automatically**, including portal controls and keyboard-generated clicks. Do not also call sound methods in their handlers.

An HTML control representing an environment item must use **`data-sound-effect="environment"`**:

```tsx
<button data-sound-effect="environment" onClick={activateObserver}>
  Open Observer profile
</button>
```

Existing About target labels, room elevator labels and keyboard-accessible floor buttons have this attribute so their audio matches the corresponding 3D object. System menus remain system audio even when they select an exhibit. Use `data-interaction-sound="off"` to opt out; custom actionable DOM targets can opt in with `data-interaction-sound="on"` and must still provide accessible activation behavior. Hidden, inert and disabled controls are silent.

### React Three Fiber picks and shortcuts

For native environment picks, import `useSoundEffects` from `src/audio/useSoundEffects.ts` and use **`environmentClick()` after the click/drag guard**:

```tsx
const { environmentClick } = useSoundEffects()
onClick={event => {
  event.stopPropagation()
  if (event.delta > 5 || navigationRef.current.dragDistance > 5) return
  environmentClick()
  activateItem()
}}
```

**Existing room exhibit picks already play centrally** in `CityWalkthrough.interactWithRoom` after drag rejection. New exhibits following this shared path need no additional sound call. HTML target labels pass `source='label'` and use delegation, avoiding double playback. Native elevator switches and room elevator door/call-panel picks explicitly play environment clicks.

Discrete system shortcuts use **`click()`** once per accepted non-repeated keypress (menu toggle, tour start/pause, exhibit changes, reset/home, dialog Escape). Continuous walking, scrolling, mouse-look, held-key repeat, pointer hover and focus changes never play sounds. Keep visual hover/focus feedback.

## Verification

```sh
npm run lint && npm run typecheck && npm run build
node --import tsx scripts/verify_interaction_audio.mts
node --import tsx scripts/verify_category_portal_audio.mts
node --import tsx scripts/verify_category_portal_audio_browser.mts
node --import tsx scripts/verify_door_audio.mts
node --import tsx scripts/verify_door_audio_browser.mts
node --import tsx scripts/verify_audio_consent.mts
node --import tsx scripts/verify_music_autoplay.mts
```

`verify_audio_consent.mts` uses Playwright/Chrome with a blocked autoplay policy. It checks no pre-consent music/context/download, remembered enabled/muted choices across refreshes, gesture fallback, Enter/M/Escape, preferences reopening the shared prompt, saved settings, silent hover/focus tooltips, modal focus/input, the fixed mix, hidden-page music pause/resume and reduced motion. It also verifies that selecting YES again does not interrupt an already-playing track. Layout checks cover the city, stationary About room and Level 4 progress at 1280/768/390 px. `verify_music_autoplay.mts` separately checks allowed autoplay/reload, rejected/unknown-policy fallback and remembered mute. Automatic music never constructs an effects AudioContext. Playwright 1.61.1 is installed by `npm ci`; `PLAYWRIGHT_MODULE` remains an external-module override. `CHROME_EXECUTABLE` overrides `/usr/bin/google-chrome`, and `VERIFY_OUTPUT_DIR` overrides the temporary screenshot directory. `VITE_TEST_OUT_DIR` can select an isolated preview build when other builds are running. Build first so preview serves current code. See [development](development.md) for the full `npm run verify` / `npm run verify:browser` groups and shared browser serialization helper.

Browser review: hover/focus silently across both HTML and 3D controls; verify system versus environment click mapping on all four floors, both physical and accessible elevator controls, return door/call-panel/labels, keyboard activation, audio controls, touch, mute/volume persistence, hidden-page cancellation and silent dragging/disabled targets. Each accepted action must play at most one effect.
