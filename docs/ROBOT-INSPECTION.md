# Future drone and robot inspections

Design direction, not an implemented diagnostic service.

A scan resolves a module's immutable asset UUID. A robot can then submit a separate
inspection event through a future authenticated service. Module identity, installation
position, cell position and inspection identity must remain distinct. Replacing a
module allocates a new asset UUID; moving a module preserves its UUID and changes its
installation relationship. Preserve uncertainty when a label cannot be read: nearby
GPS coordinates or a guessed row position must not silently establish identity.

Proposed inspection fields:

- `inspection_id`, `asset_id`, capture time and received time in UTC.
- Sensor/robot identity, operator authority, calibration reference and capture modality.
- Original evidence URI, content hash, access policy and original measurement units.
- Layout version and module-local cell coordinates; documented orientation transform
  between sensor image and cell layout, with positional uncertainty.
- Conditions such as irradiance/load/temperature where relevant to interpretation.
- Separate observations, algorithm/version, uncertainty and reviewer decision.

Repeated submissions use the inspection ID for idempotency. Corrections append
superseding events rather than erasing original observations. Raw image/video assets
belong in controlled object storage; this public identity registry must not become
an accidental publication path for private site coordinates or imagery.

Scanning a barcode identifies a record. Diagnosis needs appropriate sensors,
conditions and validated interpretation. Thermal, electroluminescence and other
imaging methods reveal different information; ordinary RGB label scanning cannot
establish every cell defect. Resolution, label placement, glare, viewing angle and
flight/robot access require field trials. GPU processing can assist image analysis
later; it cannot manufacture missing observations or establish authenticity from a
copied label.

Research context:

https://research-hub.nlr.gov/en/publications/from-modules-to-atoms-techniques-and-characterization-for-identif/

https://backend.orbit.dtu.dk/ws/portalfiles/portal/210142648/FINAL_VERSION_1_.pdf
