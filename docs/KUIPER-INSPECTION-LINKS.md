# Connect inspection evidence through a shared module identity

An EL machine, factory quality system, laboratory, drone or robot can refer to the
module UUID issued here. Its measurements remain in its own authorised evidence
system. Kuiper can consume identity references and show the linked evidence in the
context of modules, strings, inverters and sites.

Available now: a generated, read-only identity index at
https://ventusltd.github.io/globalgrid2050-ip-and-mac-addresses/data/kuiper-index.json

Schema: `globalgrid.kuiper.identity-index.v1`. Each entry supplies immutable `id`,
title, kind, status, demonstration flag, permanent resolver URL and linked record
URL. It is derived from the registry, not a second identity authority. It currently
contains three demonstration identities. Kuiper's reader is not implemented here.

Proposed inspection handoff (separate from the currently supported registry schema):

```json
{
  "schema": "globalgrid.inspection-reference.proposal.v1",
  "inspection_id": "<new inspection UUID>",
  "asset_id": "<existing module UUID>",
  "modality": "electroluminescence",
  "captured_at": "<UTC timestamp>",
  "issuer": "<inspection organisation identifier>",
  "evidence_url": "<authorised HTTPS inspection record>",
  "evidence_sha256": "<hash of an identified immutable evidence artifact>",
  "layout_ref": "<module layout version and cell coordinate convention>",
  "method_ref": "<procedure and instrument calibration references>",
  "review_state": "unreviewed"
}
```

The example is a proposed field contract, not a fabricated completed inspection.
An actual adapter must validate IDs, authenticate the issuer, respect evidence
access controls, verify hashes where it has access, and distinguish an observed
feature from a confirmed defect. An unreadable serial/barcode creates an unresolved
identity case; it must not silently attach evidence to a guessed module. Existing
manufacturer serial numbers can be mapped as scoped aliases in a later schema.

Two factories may use the same serial string, so an alias needs its issuer. A
retest creates a new inspection ID for the same module. A replacement module gets
a new asset ID. Images and measurements are not uploaded into this public identity
repository merely because their references appear in Kuiper.
