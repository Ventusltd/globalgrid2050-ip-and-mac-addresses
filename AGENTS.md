# Identity registry rules

Read README.md, DATA_SOURCES.md and docs/IDENTITY-CONTRACT.md before changes.
Never regenerate published IDs or rewrite prior events. Use registry.py and compare
against the previous published registry. Retired IDs stay reserved. Numeric IDs are
strings, not JavaScript numbers. UUID identity is not IP/MAC allocation or proof of
ownership. Do not publish private asset details. Keep search at the top and QR pixels
stationary, including the quiet zone. Test label decoding independently of encoding.
Read the existing GPU evidence before GPU proposals: UUID issuance needs secure
randomness and persistent uniqueness checks, not a CuPy pseudorandom generator.
No scheduled collectors, no mass issuance without actual records, no claim of
billion-scale operation from this small static implementation.
