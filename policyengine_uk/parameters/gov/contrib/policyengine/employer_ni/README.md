# Employer NI incidence

These parameters describe how the model allocates a change in employer National
Insurance costs. Their defaults, unchanged from 2010, are employee incidence `1`,
consumer incidence `0.5` and capital incidence `0.5`. They are adjustable modeling
assumptions; no empirical estimate is claimed for the defaults.

Secondary Class 1 and Class 1A on benefits in kind use these same parameters.
Modeled employer cost includes the actual Class 1A liability, while leaving out
the benefits' tax valuation as a resource cost. This applies to the default
`company_car_tax_rise_2030` scenario as well as employer-rate changes. Set all
three shares to zero in both baseline and reform for a static comparison;
the statutory Class 1A calculation is unchanged.

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
