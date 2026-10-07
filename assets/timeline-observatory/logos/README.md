# Timeline board logos

`prepare_timeline_logos.py` reads the owner-supplied root APU, LYJ and COS PNGs without modifying them. Generated original-color RGBA copies retain proportional framing and transparency where supplied, with no grayscale filter or color tint. `logo-manifest.json` records source/output hashes and dimensions.

Blender packs these images onto separate UV logo quads; the read-only room exporter publishes the same PNGs and hashes with the Experience package. The original procedural symbols remain hidden for recovery on replaced boards. Run preparation before focused content updates or a full room build.
