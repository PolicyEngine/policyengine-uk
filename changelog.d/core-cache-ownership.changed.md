Use Core constructors and ownership APIs for parameter caches, result
invalidation, and supplied-input provenance. Remove UK provenance scans and
variable registration while preserving branch snapshots and neutralized inputs.
Route only supplied values to pre-response inputs, avoiding carried-value
promotion and preserving each branch's explicit values during initialization.
