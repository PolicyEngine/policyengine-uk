# Define bounded program context

Generate context with:

```bash
policy-audit context UNIT_ID --version VERSION
```

The output separates four concepts:

- **Owning program:** the program whose rule the target primarily encodes.
- **Component:** the narrower subject within that program.
- **Calculation slice:** the target, its direct calculation inputs, and the
  shortest source paths to the registered headline result.
- **External consumers:** calculations owned by other programs that use the
  target.

Treat `programs.yaml` as the initial registry, not as sufficient evidence for
broad agency-level prefixes. The tool may return `provisional` or
`program_mapping_required`. Resolve that state with a curated override before
making program-wide claims.

Releases created before `programs.yaml` existed have no automatic ownership
mapping. Their inventory is still valid, but context generation returns
`program_mapping_required` until a reviewed override supplies the owner.

## Scope rules

- For a parameter, inspect every direct variable reader and the variables that
  select its breakdown keys.
- For a variable, inspect its direct parameters and variable inputs.
- Follow the shortest downstream paths to the headline program variable.
- Read directly relevant tests and nearby program documentation.
- List cross-program readers separately; dependency does not transfer
  ownership.
- Do not load an entire program directory merely because the target belongs to
  that program.
- Expand the slice only when the official rule couples the target to another
  component, and explain the expansion in the review.

Example: the Universal Credit standard-allowance parameter includes all four
claimant-type amounts, `uc_standard_allowance`, the claimant-type selection,
and the path into the final award. It does not automatically include childcare,
housing costs, or every eligibility condition.

Example: the UK income-tax rate scale includes its complete brackets, the
earned-income calculations that consume them, jurisdiction routing between UK
and Scottish rates, and other direct consumers. This does not certify the
complete savings, pension, Gift Aid, or Scottish income-tax implementations.
