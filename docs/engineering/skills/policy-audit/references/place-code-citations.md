# Place citations in model source

Every proposed policy change must identify where its official sources belong
when the issue is implemented.

- A source supporting one dated parameter value belongs in that value's
  `metadata.reference`.
- A source supporting every member or date in a parameter belongs in the
  closest common parameter metadata.
- A source supporting formula logic, eligibility, or a definition belongs in
  the variable's `reference` attribute.
- When different clauses support different pieces of logic, use multiple
  references and identify the relevant code or documentation location.
- Prefer a specific regulation, schedule, rates document, or official guidance
  section over a general program page.

Each implementation part must include `code_reference_targets`. Every target
contains a parameter or variable source path, a precise YAML or Python
location, and the evidence identifiers to place there. The issue renderer uses
these fields to make citation work an explicit part of implementation.
