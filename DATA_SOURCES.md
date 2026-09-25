# Data sources and publication

The panel, cable and transformer examples are synthetic demonstration records.
They are not imported manufacturer inventory, live network discovery, certified
equipment provenance or evidence of physical ownership. Their UUID allocations
identify the demo records and must remain stable between builds.

The project defines its own asset fields, lifecycle rules, decimal ID encoding
and resolver route. The identity standards and implementation references are:

- [RFC 9562](https://www.rfc-editor.org/rfc/rfc9562.html): UUID format, UUIDv4,
  collision resistance and database considerations.
- [Python standard-library UUID documentation](https://docs.python.org/3/library/uuid.html):
  `uuid.uuid4()`, the integer representation and parsing.

These references support identifier handling. They do not certify the example
assets or endorse this registry. No IP or MAC address allocation dataset is used.

Publish only explicitly public data and public configuration. Review proposed
records and updates through Git under the publisher's authorization process.
Keep credentials, private network details and sensitive asset locations out of
the public source tree and generated site. Published Git history can retain old
values; review data before committing it.

For future imported data, document the source URL or dataset, publisher,
retrieval date, licence or permission, transformations, and verification limits
before publication. Preserve corrections as events. A source citation or Git
review is not cryptographic proof that a physical asset is authentic.
