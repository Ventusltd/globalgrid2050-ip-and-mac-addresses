# Asset identity contract

This registry gives each asset one permanent UUID and a public resolver record.
It allocates neither IP addresses nor MAC addresses. Its public demo is read-only;
publication and updates require the publisher's Git review and authorization.

## Allocation and representation

Allocate once with Python's standard library `uuid.uuid4()`. UUIDv4 uses random
bits under [RFC 9562, section 5.4](https://www.rfc-editor.org/rfc/rfc9562.html#section-5.4);
see also the [Python UUID API](https://docs.python.org/3/library/uuid.html#uuid.uuid4).
Store the canonical lowercase, hyphenated UUID as `id`.

For an allocated UUID object `u`, `barcode_number = str(u.int).zfill(39)`.
This 39-digit decimal string encodes the same 128-bit ID; it is not a second
allocation or an independently assigned product code. Preserve leading zeroes
and store it as text, including in JSON. Never convert it to a JavaScript Number.
The inverse is `uuid.UUID(int=int(barcode_number))`; it must equal `id`.
The encoding alone does not claim compatibility with a retail barcode standard.

UUIDv4 permits distributed allocation with collision resistance, not an absolute
uniqueness guarantee. Enforce registry uniqueness before accepting an allocation;
retry a collision before publishing. Reject conflicting imported IDs instead of
silently overwriting records. See [RFC 9562, section 6.7](https://www.rfc-editor.org/rfc/rfc9562.html#section-6.7).

## Resolution and lifecycle

The configured HTTPS resolver uses `/#id=<UUID>` under its deployment base path.
Validate the supplied ID and perform an exact lookup in the small registry's
index. A malformed ID, absent record and retired record have distinct outcomes.
Display the record and its links without automatically redirecting visitors.

`id`, `barcode_number` and `created_at` are immutable. Corrections and changes
append events; a current view may be derived from those events. Retirement adds
an event and preserves the record and history. Never delete or reuse an allocated
identity. Moving an asset or changing its description does not allocate a new ID.

Only explicitly public data belongs in the published registry and deployment
configuration. A resolver record is a publisher assertion: Git review does not
provide PKI provenance, prove physical authenticity, or establish ownership.

The example panel, cable and transformer are synthetic demonstration assets.
Use their existing registry allocations when linking to them; reloading,
rebuilding or changing descriptions must not generate replacement IDs.
