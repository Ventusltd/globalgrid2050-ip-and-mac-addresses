# Scaling the registry

The demo serves a small public registry and looks up an exact UUID in its index.
Its architecture and fixtures do not demonstrate billion-record storage,
lookup latency, availability or allocation throughput. Identifier space is not
a measurement of operational capacity.

Growth beyond the static demo requires a durable database with transactions,
unique constraints on IDs and their decimal encodings, and an append-only event
history. Allocate and record an asset atomically; reject conflicting imports.
Keep retirement history through backup, restore, replication and migration.
Do not give a retired identity to another asset.

A future partitioned API should route an exact ID to its responsible partition,
return a bounded record, and paginate history. Publish only explicitly approved
public fields. Keep publisher authentication and authorization separate from
the public read API. API partitioning, durable database storage and this access
control infrastructure are future work, not implemented capacity claims.

UUIDv4 supports allocation without a central counter, but uniqueness enforcement
and collision handling remain necessary. Its random ordering also affects index
locality; choose storage and partitioning from measured workloads. See
[RFC 9562, section 6.7](https://www.rfc-editor.org/rfc/rfc9562.html#section-6.7)
and [section 6.13](https://www.rfc-editor.org/rfc/rfc9562.html#section-6.13).

Before claiming a supported scale, measure ingestion and concurrent exact
lookups against a declared dataset size, including tail latency, storage growth,
backup recovery and partition failure. Report hardware, configuration, failures
and synthetic versus real data. Preserve the same identity and resolver contract
when changing the storage implementation.
