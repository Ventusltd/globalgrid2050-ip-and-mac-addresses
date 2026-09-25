# First release validation — 25 September 2026

Local results: 19 Python unittest cases passed; 31 Node/jsdom tests passed.
Three persisted demonstration UUIDs map bijectively to their full numeric strings.
The independent ZXing-C++ decoder recovered the exact permanent HTTPS address for
each generated QR label at two raster scales. This is software decoding, not a
field test with a phone, drone or robot.

Registry tests cover immutable identity, duplicate records/events, precision,
update/retirement, rejected writes and event-history tampering against a previous
registry. Interface tests cover search, exact hash resolution, malformed/unknown
IDs, safe links, configuration, missing QR handling and the frame pause control.

jsdom tests exercise DOM logic; they do not establish rendered browser layout or
physical scanning performance. No local Chromium run is claimed for this release.
The GitHub workflow repeats the tests before publishing. `_site/build-receipt.json`
records the output hashes, record/event counts and resolver base.

Next acceptance work: real phone/printed-label scan trials, visual desktop/mobile
checks, authenticated write/event services and measured database scaling. Drone
and cell-level diagnostic plans are in ROBOT-INSPECTION.md, not implemented here.
