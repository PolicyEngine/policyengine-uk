# Firms

PolicyEngine UK has a firm entity beside the person, benefit unit and household entities. Firm-level variables compute the statutory liability of a business to corporation tax, the bank surcharge, the apprenticeship levy, employer National Insurance, business rates and VAT, together with the Employment Allowance and the employer's minimum auto-enrolment pension contribution.

```{note}
Firm-side results are not yet part of the household totals. `household_tax`, `gov_tax`, the budget lists in `programs.yaml` and `fiscal_partition.yaml` leave out every firm variable, so household results are the same with or without firms. The firm aggregates join those totals once a calibrated firm dataset is available.
```

## The firm entity

`Firm` is a root population, not a group of people:

- Each firm has its own identifier (`firm_id`) and weight (`firm_weight`). Firm weights come from business data, not from survey households.
- No person is a member of a firm. A firm variable cannot be mapped to a person, benefit unit or household, and the model raises an error if a formula tries (for example `firm.household` or `map_result` between firms and households).
- A situation or dataset without firms has a firm count of 0, so existing household situations and datasets work unchanged.
- `firm_weight` is the number of firms in the population that a record represents. It defaults to 1, so each firm in a situation counts once. Weighted firm sums, such as `sim.calculate("firm_paybill", 2025).sum()`, use `firm_weight`, never a household weight.
- Firm variables are left out of per-person data exports.

Since per-employee pay is not linked to firms yet, employee data is held at firm level: the paybill (`firm_paybill`), the number of employees (`firm_employees`) and earnings that carry a zero rate of employer National Insurance (`firm_zero_rated_class_1_earnings`).

### Firms in a situation

A situation takes an optional `firms` entry that maps each firm's name to its inputs. Firms have no `members` list.

```python
from policyengine_uk import Simulation

situation = {
    "people": {"adult": {"age": {2025: 40}, "employment_income": {2025: 45_000}}},
    "benunits": {"benunit": {"members": ["adult"]}},
    "households": {"household": {"members": ["adult"]}},
    "firms": {
        "manufacturer": {
            "firm_paybill": {2025: 4_000_000},
            "firm_employees": {2025: 100},
            "firm_taxable_trading_profit": {2025: 600_000},
            "firm_turnover": {2025: 12_000_000},
            "firm_standard_rated_supplies": {2025: 12_000_000},
        },
        "corner_shop": {
            "firm_legal_form": "SOLE_TRADER",
            "firm_paybill": 40_000,
            "firm_employees": 2,
        },
    },
}

sim = Simulation(situation=situation)
sim.calculate("corporation_tax", 2025)  # [150_000, 0]
sim.calculate("firm_employer_ni", 2025)  # [514_500, 0]
sim.calculate("employment_allowance", 2025)  # [10_500, 4_500]
```

The manufacturer pays corporation tax at the 25% main rate on £600,000 of profit. Its employer National Insurance is 15% of the £3.5 million of pay above the £5,000 secondary threshold for each of its 100 employees, less the £10,500 Employment Allowance. The corner shop is a sole trader, so it pays no corporation tax, and its £4,500 of employer National Insurance is covered by the Employment Allowance.

A situation of firms alone (`{"firms": {...}}`) has no people. Firm variables compute in it, but household variables do not, since it has no benefit units.

### Firms in a dataset

`UKSingleYearDataset` and `UKMultiYearDataset` take an optional `firm=` table with one row per firm. A table without a `firm_id` column numbers its firms 0, 1, 2 and so on, in the order it gives them. Each year of a multi-year dataset must give the same firms.

```python
import pandas as pd
from policyengine_uk import Microsimulation
from policyengine_uk.data import UKSingleYearDataset

dataset = UKSingleYearDataset(
    person=pd.DataFrame(
        {
            "person_id": [1],
            "person_benunit_id": [1],
            "person_household_id": [1],
            "age": [40],
            "employment_income": [45_000.0],
        }
    ),
    benunit=pd.DataFrame({"benunit_id": [1]}),
    household=pd.DataFrame(
        {
            "household_id": [1],
            "household_weight": [1_000.0],
            "region": "LONDON",
            "rent": 0.0,
            "tenure_type": "OWNED_OUTRIGHT",
            "council_tax": 0.0,
        }
    ),
    firm=pd.DataFrame(
        {
            "firm_id": [1, 2],
            "firm_weight": [100.0, 2_000.0],
            "firm_paybill": [4_000_000.0, 40_000.0],
            "firm_employees": [100, 2],
        }
    ),
    fiscal_year=2025,
)

sim = Microsimulation(dataset=dataset)
sim.calculate("firm_employer_ni", 2025).sum()  # £51.45 million: 100 × £514,500
```

The firm table is kept out of the dataset's `tables`, so uprating and household subsetting work as before. `subsample` raises `NotImplementedError` when a dataset has firms. The dataset loaders also read an optional firm table from an H5 file.

## Programmes

Every firm variable uses `entity = Firm` and a yearly period. Each parameter cites legislation or GOV.UK guidance, and values that could not be verified carry `# UNVERIFIED` comments in their YAML files.

| Programme | Main variables | Rules |
|---|---|---|
| Employer National Insurance | `firm_employer_ni`, `firm_employer_ni_before_allowance` | Class 1 secondary contributions with the `gov.hmrc.national_insurance.class_1` rates and thresholds. Pay above the secondary threshold can be an input; by default it is approximated from the paybill and the number of employees. |
| Employment Allowance | `employment_allowance`, `employment_allowance_eligible` | The amount from 2014 (now £10,500), capped at employer National Insurance liability. Excludes single-director companies and public bodies, and applies the £100,000 prior-year liability limit from 2020-21 to 2024-25. |
| Apprenticeship levy | `apprenticeship_levy` | 0.5% of the paybill less the £15,000 allowance, which connected employers share. |
| Auto-enrolment | `firm_auto_enrolment_employer_contribution` | The 3% employer minimum contribution on qualifying earnings between £6,240 and £50,270. |
| Corporation tax | `corporation_tax`, `firm_taxable_profit`, `firm_marginal_relief`, `firm_losses_used` | Main and small profits rates, marginal relief at a 3/200 fraction with limits divided by associated companies, and loss relief with the £5 million deductions allowance. Only companies are liable (`firm_legal_form`). |
| Capital allowances | `firm_capital_allowances` and its components | Full expensing, the 50% special-rate first-year allowance, the annual investment allowance, the main-rate first-year allowance (40% from 1 January 2026), writing-down allowances, the structures and buildings allowance, and balancing charges. |
| R&D relief | `firm_rd_expenditure_credit`, `firm_rd_additional_deduction`, `firm_rd_payable_credit` | The merged-scheme expenditure credit (20%) and enhanced support for R&D-intensive loss-making SMEs. |
| Bank surcharge | `bank_surcharge` | 8% above a £25 million allowance from 2016, and 3% above £100 million from April 2023. The 6% rate announced for 1 January 2027 to 31 March 2028 is marked as not yet enacted. |
| Business rates (England) | `firm_business_rates` and its reliefs | Multipliers for 2023-24 to 2027-28, including the 2026 retail, hospitality and leisure (RHL) and high-value multipliers. Small business rate relief, charitable relief, RHL relief to 2025-26, pubs and live music venues relief, and empty property relief. |
| VAT | `firm_vat`, `firm_vat_registered`, `firm_output_vat` | The registration threshold (£85,000, then £90,000 from April 2024), output VAT less recoverable input VAT with partial exemption, and the flat rate scheme with the 16.5% limited cost trader rate. Uses the existing `gov.hmrc.vat` rate parameters. |

`policyengine_uk/programs.yaml` lists these programmes with the years their parameters and tests cover.

## Aggregates and incidence

Four variables combine the firm-level results:

- **`firm_tax`** (firm): the firm's total statutory liability to corporation tax, the bank surcharge, the apprenticeship levy, employer National Insurance after the Employment Allowance, business rates and VAT, less R&D tax credits paid out to the firm.
- **`firm_only_tax`** (firm): the liability set by rules that only the firm side models: corporation tax, the bank surcharge, the apprenticeship levy and business rates, less R&D tax credits paid out. It leaves out employer National Insurance and VAT, whose rates and thresholds already reach households through `ni_employer` and `vat`. It also leaves out the Employment Allowance.
- **`firm_tax_change_total`** (household): the reform's `firm_only_tax` less the baseline's, summed over firms with `firm_weight`, less the change in the Employment Allowance from a change in its own rules (amount and eligibility), with each firm's employer National Insurance liability held at its baseline value. Every household carries the same total. It is 0 without a baseline, in a simulation built from a situation, and where the simulation has no firms.
- **`firm_tax_incidence`** (household): each household's share of `firm_tax_change_total`, split between capital (by `shareholding`), consumers (by `consumption_shareholding`) and workers (by the household's share of weighted employment income). The shares are the `gov.contrib.policyengine.firm_incidence` parameters `capital`, `consumer` and `labour`, which default to 1, 0 and 0.

`firm_tax` is a receipts measure. Summed over firms it must not be added to `gov_tax`, whose household terms already count employer National Insurance, VAT and business rates as incidence. None of the four variables is a term of `gov_tax` or `household_tax` yet.

## Known simplifications

- Every firm has an April to March financial year.
- Yearly parameters are read at 30 April, so changes dated 1 January are not apportioned. This affects the 40% and 50% main-rate first-year allowances and the 6% bank surcharge for January to March 2027.
- Employer National Insurance and auto-enrolment use firm-level approximations, since there is no per-employee pay yet.
- Business rates assume one aggregate property per firm, cover England only and have no transitional relief.
- Corporation tax has no group relief, Patent Box or quarterly instalment payments.
- VAT registration is tested on annual turnover, not a rolling 12 months, and there is no cash or annual accounting.
- Freeport employer National Insurance relief enters through `firm_zero_rated_class_1_earnings`.
- In a simulation of firms alone, household variables cannot be computed, since there are no benefit units.
