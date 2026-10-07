# Elevator workflow

## Full rebuild

```sh
blender --background --factory-startup --python-exit-code 1 --python assets/kaze-elevator/rebuild_elevator.py
```

The entrypoint runs `build_elevator.py`, `build_entrance.py`, `build_dialogs.py`, `build_journey.py`, then the final `update_floor_panel.py` design refresh. It verifies the final camera and absence of linked libraries before deleting known intermediate `.blend` files/backups. Failure leaves stages for diagnosis; individual stages require their preceding input.

## Panel-only authoring edit

```sh
blender --background assets/kaze-elevator/kaze-elevator-journey.blend --python-exit-code 1 --python assets/kaze-elevator/update_floor_panel.py
```

This saves the master and retains one prior save. It compares sampled camera/door transforms before and after updating the panel, floor metadata, and embedded controls. `floor_panel_design.py` authors the clipped-corner button faces and rims, left floor-number compartment/divider, tracked captions, right chevrons, dash display, and circular alarm/footer. It differs from the read-only exporter.

## Browser and integration

```sh
blender --background assets/kaze-elevator/kaze-elevator-journey.blend --python-exit-code 1 --python assets/journey/export_browser_elevator.py
blender --background assets/journey/city-lobby-walkthrough.blend --python-exit-code 1 --python assets/journey/build_elevator_handoff.py
blender --background assets/journey/portfolio-journey.blend --python-exit-code 1 --python assets/journey/verify_elevator_handoff.py
node assets/journey/verify_rooms.mjs
```

The city/lobby integration must exist first; see [the full order](../journey/WORKFLOW.md). Export creates cabin groups, stride-12 motion and button metadata without saving the authored master. Approximately 7,400 stipple shapes become GPU points rather than tiny solid triangles.

Verify all four 3D/keyboard/touch switches, hover/press/release/drag-off, selected latch, cancel reset, doorway coverage, panel portrait framing and idle demand-render settling. Source controllers and local GLBs are review artifacts; web transitions use generated geometry/animation and React state.
