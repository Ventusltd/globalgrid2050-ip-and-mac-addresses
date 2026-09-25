# GlobalGrid identity registry

Permanent asset identities and scannable record addresses for GlobalGrid2050.

AI READ FIRST: follow the [data discipline manual](https://github.com/Ventusltd/globalgrid2050-homepage/blob/main/docs/DATA_DISCIPLINE_MANUAL.md). This repository owns identity mappings, not engineering datasets. Never publish confidential project records here.

UUID identities are not allocated network IP addresses or hardware MAC addresses.

Website: https://ventusltd.github.io/globalgrid2050-ip-and-mac-addresses/

## What works

- Immutable UUID4 identities, generated using Python's operating-system-backed UUID implementation.
- A 39-digit numeric representation of the same UUID, stored as text to preserve every digit.
- Search by title, UUID or number; a stable `#id=<UUID>` address resolves an exact record without automatically following its external link.
- Static QR labels encode that address. Their white scanning area stays still; only the surrounding frame animates, with pause and reduced-motion support.
- Append-only registration, update and retirement events. Retirement retains the ID. Previous published event history is compared during push/PR validation.
- Three explicit demonstration records: a solar panel, a cable and a transformer. No real equipment is being tracked by these examples.
- A generated identity index for a future Kuiper reader: `data/kuiper-index.json`. See [inspection handoff](docs/KUIPER-INSPECTION-LINKS.md); no EL instrument or Kuiper reader is connected yet.

## Run and maintain

Requires Python 3.12+ and Node 22+ for the website tests.

```sh
python -m pip install -r requirements.txt -r requirements-test.txt
npm ci --ignore-scripts
python -m unittest discover -s tests -v
npm test
python registry.py validate
python build.py
python -m http.server 8000 --directory _site --bind 127.0.0.1
```

Open http://127.0.0.1:8000 . Serve the built directory so QR labels are available.

Register public information (use `--demo` for examples):

```sh
python registry.py register --title "Example panel" --kind solar-panel --url "https://example.com/panel" --demo --public
python registry.py update YOUR-UUID --title "New display name"
python registry.py retire YOUR-UUID --reason "Removed from service"
python registry.py validate --previous previous-registry.json
```

The register command prints the new UUID; save it, then use that UUID for later updates. Review and commit registry changes; the one unscheduled workflow validates and publishes the static site. Existing workflows in other repositories remain untouched.

## Scope and ownership

Grain: one current record per UUID, one event per event UUID. `data/registry.json` is the authority for these mappings; linked engineering datasets remain with their owners. `config.json` supplies the resolver base. Keep that deployed address durable or maintain redirects when moving the service. Local clients cannot globally reserve a short sequential number: the full numeric UUID encoding avoids introducing a second allocator.

This first release loads the small public registry in the browser. It is not a billion-record database, an authenticated write API, a signed ownership register, or continuous location tracking. Git-reviewed publication is the current write authority. A QR code can be copied; it does not authenticate equipment. Network IP/MAC values, if later recorded, must be separate attributes rather than substitutes for asset identity.

Read [identity rules](docs/IDENTITY-CONTRACT.md), [scaling plan](docs/SCALING.md), [sources](DATA_SOURCES.md) and [changes](CHANGELOG.md). Core software is MIT licensed; qrcodegen, Pillow, ZXing-C++ and jsdom retain their respective upstream licences. No confidential drawings, serial numbers or site details belong in this public registry without explicit public-release authority.
