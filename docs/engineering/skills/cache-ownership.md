# Cache ownership

Read this before changing simulation initialization, parameter installation,
input provenance, branching, or calculated-result invalidation.

## Core owns storage and provenance

Core's Type D cache contains simulation results and supplied-input metadata.
Supplied inputs are authoritative snapshots, not evictable calculated results.
Core owns their storage, branch visibility, and provenance. UK code must use
`set_input`, `delete_arrays`, `clear_calculated_results`,
`supplied_input_periods`, and `get_supplied_input`; it must not mutate backing
cache dictionaries, input-key sets, or pending invalidations.

Both `Simulation.set_input` and `Holder.set_input` record supplied inputs.
Both public deletion paths remove the matching provenance. Carried values and
formula results never become supplied inputs. No country-specific variable
registration or scan before each calculation is required. The UK
`supplied_input` helper only adds UK neutralization semantics to Core's lookup.

Clones and branches own their indexes, input metadata, and pending invalidations.
Immutable arrays may be shared. A branch is a snapshot: updating a parent input
or clearing its results does not mutate an existing branch or baseline.
An operation intended to update several simulations must name those simulations
explicitly. `reset_calculations` clears only the receiving simulation's computed
results, including results for variables that also have supplied periods; it
does not replay or discard supplied inputs.

`move_values` routes supplied donor periods into the target on the receiving
simulation and its direct branches. It preserves each simulation's visible
input values, removes donor provenance, and keeps existing donor-over-target
precedence at matching periods. It does not turn formula results or carried
periods into new inputs. This prevents a computed total from being written
back as its own pre-response component.

## Construction and parameters

Call Core's normal constructors to initialize systems and simulations. Do not
reimplement their fields or use a cache setter as a substitute for construction.
UK parameter processing remains in `CountryTaxBenefitSystem`: Core must not
automatically run its general country-parameter pipeline or add abolition
parameters to the UK tree.

Install a processed or cloned root using `replace_parameters`. Clear dated
parameter views through `clear_parameter_caches`, not private dictionaries.
The process-local processed-parameter template is cloned before installation;
each system owns its root. The existing UK `reset_parameter_caches` method is
an external compatibility alias, not an internal mutation mechanism.

## Release order

The migration uses three stages and four pull requests:

1. Release preparatory Core with the constructor, parameter ownership, and
   Type D guarantees above, while retaining old compatibility adapters.
2. Release US and UK migrations in separate PRs. Before either country PR
   merges, set its minimum Core dependency to the actual preparatory release,
   regenerate its lockfile, and verify against that released package. Do not
   invent a future version or merge with an older minimum dependency.
3. Release a separate Core cleanup after both country releases. Remove legacy
   mutable cache adapters there; do not defer supported country migrations to
   this stage. Phase 7 remains out of scope.

During development, validate against the local preparatory Core checkout with
an editable install. Do not publish that local path in package metadata.
