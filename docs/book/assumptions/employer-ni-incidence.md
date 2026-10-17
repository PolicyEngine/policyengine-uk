# Employer National Insurance incidence

Employer National Insurance reforms can change wages, tax receipts and household
income through the model's incidence assumptions. The parameters under
`gov.contrib.policyengine.employer_ni` default to:

| Parameter | Default | Implemented role |
|---|---:|---|
| `employee_incidence` | 1 | Scales the computed fixed-employer-cost pay adjustment |
| `consumer_incidence` | 0.5 | Allocates remaining employer-cost changes by consumption shares |
| `capital_incidence` | 0.5 | Allocates remaining employer-cost changes by corporate wealth shares |

These values are adjustable model assumptions. No empirical estimate is claimed
for the defaults, and this page does not select a preferred incidence assumption.

## Wage adjustment and supplied income

The wage channel compares the baseline and reform employer-NI rate, secondary
threshold and employer-pension exemption. For its eligible earnings branch, it
solves for pay holding modeled employer cost fixed, then multiplies the pay change
by `employee_incidence`. At `1`, the full computed adjustment applies in the same
model year. The formula returns zero without a baseline, without a relevant
parameter change, at employee incidence zero, or for prior pay below the baseline
secondary threshold. This describes the implemented calculation, including its
threshold guard; it does not assert a general equilibrium response for every worker.

`employment_income` adds this adjustment to `employment_income_before_lsr` and
other earnings components. An input actually stored in the final
`employment_income` holder overrides its formula. The UK `Simulation` constructor
moves situation inputs named `employment_income` to `employment_income_before_lsr`.
Consequently, putting that field in a constructor situation can still allow the
wage response. The example below demonstrates an override with `set_input` after
construction and before calculation. Dataset and other input routes should be
checked for which earnings holder they populate.

The [wage formula](https://github.com/PolicyEngine/policyengine-uk/blob/b4dbaf57a4ebb1d1f0ba5f7a384795422828db75/policyengine_uk/variables/contrib/policyengine/employer_ni/employer_ni_fixed_employer_cost_change.py),
[earnings components](https://github.com/PolicyEngine/policyengine-uk/blob/b4dbaf57a4ebb1d1f0ba5f7a384795422828db75/policyengine_uk/variables/input/employment_income.py)
and [constructor remapping](https://github.com/PolicyEngine/policyengine-uk/blob/b4dbaf57a4ebb1d1f0ba5f7a384795422828db75/policyengine_uk/simulation.py#L350)
provide the implementation details.

## Consumer and capital channels

Consumer and capital incidence apply to the remaining change in modeled employer
cost after the wage response. Each is zero when its own parameter is zero or
employee incidence is one. Otherwise, the formulas use person weights and allocate
that change using household consumption or corporate wealth per person. Their
weighted aggregate exposure must be nonzero; they also return zero when the
simulation has no dataset attribute.

An attribute can be present with `dataset=None`, so that guard alone is not a
promise that every household calculation has zero residual incidence. The example
below has no representative dataset or consumption/wealth exposures and returns
zero for both residual channels. It cannot show their population effects.

Setting `employee_incidence` to zero alone leaves the consumer and capital
parameters at `0.5`. Set **all three parameters to zero** to disable these three
employer-NI incidence channels. This does not disable unrelated labor-supply or
other behavioral responses.

The response amounts enter `household_tax`; those same variables are not added to
`gov_tax`. See the [consumer](https://github.com/PolicyEngine/policyengine-uk/blob/b4dbaf57a4ebb1d1f0ba5f7a384795422828db75/policyengine_uk/variables/contrib/policyengine/employer_ni/employer_ni_response_consumer_incidence.py)
and [capital](https://github.com/PolicyEngine/policyengine-uk/blob/b4dbaf57a4ebb1d1f0ba5f7a384795422828db75/policyengine_uk/variables/contrib/policyengine/employer_ni/employer_ni_response_capital_incidence.py)
allocation formulas.

## Measures and aggregation

Report these quantities separately:

- Gross employer-NI liability or its reform change: `ni_employer`, a person amount.
- Net government balance: `gov_balance = gov_tax - gov_spending`, a household amount.
  A positive reform change improves the modeled balance. Wage changes can affect
  income tax, employee NI and benefits, so this is not a gross employer-NI yield.
- Household incidence here: the change in nominal `household_net_income`, defined
  as `household_market_income + household_benefits - household_tax - pension_contributions`.
  A negative change is a household loss under this measure.

The example sums each output over one person or one household, as appropriate.
Population results require the matching person or household weights. Do not sum
household values repeated on person records as if they were distinct households.
These measures do not by themselves establish a representative budget costing.

## Worked household example

For model year 2026, consider one 40-year-old London employee with £40,000 of
pre-response earnings, no pension contributions and no other supplied income.
Raise the employer rate from 15% to 16%, holding the other parameters fixed. Current
main includes the annual secondary-threshold correction: £5,000 rather than the
old rounded-weekly equivalent of £4,992. Each comparison below applies the same
incidence assumptions to its baseline and reform.

Annual changes in pounds, rounded to two decimal places:

| Input and incidence assumptions | Employer NI | Income tax | Employee NI | Gross pay | Government balance | Household net income |
|---|---:|---:|---:|---:|---:|---:|
| Components; employee 1, consumer/capital 0.5 | +301.72 | −60.34 | −24.14 | −301.72 | +217.24 | −217.24 |
| Components; employee 0, consumer/capital 0.5 | +350.00 | 0.00 | 0.00 | 0.00 | +350.00 | 0.00 |
| Components; all three zero | +350.00 | 0.00 | 0.00 | 0.00 | +350.00 | 0.00 |
| Pay set after construction; employee 1 | +350.00 | 0.00 | 0.00 | 0.00 | +350.00 | 0.00 |

At fixed pay, the extra liability is `0.01 × (40,000 − 5,000) = £350`.
With full wage incidence, the baseline employer cost is £45,250. Solving
`pay + 0.16 × (pay − 5,000) = 45,250` gives pay of approximately £39,698.28.
The income-tax and employee-NI changes partly offset the wage fall. The last three
rows coincide in this example; they do not imply identical population incidence.

Run this snippet from a checkout's supported Python environment:

```python
from policyengine_core.reforms import Reform
from policyengine_uk import Simulation

YEAR = 2026
SPAN = "2026-01-01.2026-12-31"
INCIDENCE = "gov.contrib.policyengine.employer_ni."
RATE = "gov.hmrc.national_insurance.class_1.rates.employer"
VARIABLES = [
    "ni_employer", "income_tax", "ni_employee", "employment_income",
    "gov_balance", "household_net_income",
]


def result(employee, consumer, capital, direct_pay=False):
    pay_input = "employment_income" if direct_pay else "employment_income_before_lsr"
    situation = {
        "people": {"worker": {"age": {YEAR: 40}, pay_input: {YEAR: 40_000}}},
        "benunits": {"family": {"members": ["worker"]}},
        "households": {"home": {"members": ["worker"], "region": {YEAR: "LONDON"}}},
    }
    assumptions = {
        INCIDENCE + "employee_incidence": {SPAN: employee},
        INCIDENCE + "consumer_incidence": {SPAN: consumer},
        INCIDENCE + "capital_incidence": {SPAN: capital},
    }
    baseline = Simulation(
        situation=situation,
        reform=Reform.from_dict(assumptions, country_id="uk"),
    )
    reform = Simulation(
        situation=situation,
        reform=Reform.from_dict({**assumptions, RATE: {SPAN: 0.16}}, country_id="uk"),
    )
    if direct_pay:
        # UK construction moves situation earnings to the pre-response input.
        # Explicitly supply the final earnings holder after construction.
        baseline.set_input("employment_income", YEAR, [40_000])
        reform.set_input("employment_income", YEAR, [40_000])
    before = {v: float(baseline.calculate(v, YEAR).sum()) for v in VARIABLES}
    after = {v: float(reform.calculate(v, YEAR).sum()) for v in VARIABLES}
    return {
        "baseline": before, "reform": after,
        "delta": {v: after[v] - before[v] for v in VARIABLES},
        "residual_channels": {
            v: float(reform.calculate(v, YEAR).sum()) for v in (
                "employer_ni_response_consumer_incidence",
                "employer_ni_response_capital_incidence",
            )
        },
    }


rows = {
    "Employee 1; consumer/capital 0.5": result(1, 0.5, 0.5),
    "Employee 0; consumer/capital 0.5": result(0, 0.5, 0.5),
    "All three zero": result(0, 0, 0),
    "Pay set after construction; employee 1": result(1, 0.5, 0.5, direct_pay=True),
}
for label, row in rows.items():
    print(label, {v: round(value, 2) for v, value in row["delta"].items()})
```

The residual-channel outputs are retained in `rows` for inspection. No private
microdata, representative population estimate or empirical calibration is used.

## Comparing an official costing

Match the definition and horizon of the specific official figure before comparing
it with a model result. For example, the
[OBR's October 2024 Economic and fiscal outlook](https://obr.uk/efo/economic-and-fiscal-outlook-october-2024/)
reported £25.7 billion of employer-NICs revenue in 2029–30 before indirect economic
effects (overview paragraph 1.7). Its paragraph 2.14 assumed about 60% of the cost
would pass to employees in the short term, with more adjustment later through
prices and nominal wages. These are dated forecast assumptions, not evidence for
the model's defaults. Other official headlines can use different definitions.
