# Employer NI incidence

These parameters describe how the model allocates a change in employer National
Insurance costs. Their defaults, unchanged from 2010, are employee incidence `1`,
consumer incidence `0.5` and capital incidence `0.5`. They are adjustable modeling
assumptions; no empirical estimate is claimed for the defaults.

For eligible earnings computed from components, employee incidence `1` applies the
computed fixed-employer-cost pay adjustment in the same model year. This changes
income tax and employee NI as well as gross pay. A supplied final
`employment_income` holder overrides that formula. The UK `Simulation` constructor
moves situation earnings into `employment_income_before_lsr`, so a constructor
field alone does not demonstrate that override.

Setting employee incidence to `0` leaves the consumer and capital channels active
where population weights and exposure totals support them. Set all three incidence
parameters to `0` to disable these three channels. Other labor-supply responses
have separate controls.

Report employer-NI liability, net `gov_balance` and household income effects
separately. The [assumptions page](../../../../../../docs/book/assumptions/employer-ni-incidence.md)
explains the implemented guards, aggregation, current worked example and a dated
OBR comparison. A single-household example does not establish population incidence.
