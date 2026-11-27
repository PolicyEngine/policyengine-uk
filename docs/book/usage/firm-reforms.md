# Firm reforms

This page runs three static reforms to firm taxes through the Python API. The first two change corporation tax rules for a few firms in a situation. The third changes the Employment Allowance in a small dataset of households and firms, and spreads the change in firm tax over households with non-default incidence shares. The [Firms](firms.md) page describes the firm entity, its inputs and the programmes it models.

```{note}
The figures on this page come from small, made-up firms and households. They show how the model computes a reform; they are not estimates of UK revenue or of household impacts. Population totals need a calibrated firm dataset, which does not exist yet. `firm_tax_incidence` is not yet a term of `household_tax` or `gov_tax`, so these reforms leave household net income unchanged.
```

Every example uses the 2026-27 tax year. `policyengine_uk/tests/test_firm_docs_examples.py` repeats each example and checks every figure below.

## Raise the corporation tax main rate

This reform raises the corporation tax main rate from 25% to 27%. A reform passed to `Simulation` keeps the current law in `sim.baseline`, so one simulation gives both sets of results.

```python
from policyengine_uk import Simulation

firms = {
    "large_company": {"firm_taxable_trading_profit": {2026: 2_000_000}},
    "mid_company": {"firm_taxable_trading_profit": {2026: 150_000}},
    "small_company": {"firm_taxable_trading_profit": {2026: 40_000}},
    "sole_trader": {
        "firm_legal_form": "SOLE_TRADER",
        "firm_taxable_trading_profit": {2026: 80_000},
    },
}
reform = {"gov.hmrc.corporation_tax.main_rate": {"2026-01-01.2100-12-31": 0.27}}

sim = Simulation(situation={"firms": firms}, reform=reform)
sim.baseline.calculate("corporation_tax", 2026)  # [500_000, 36_000, 7_600, 0]
sim.calculate("corporation_tax", 2026)  # [540_000, 39_000, 7_600, 0]
```

| Firm | Taxable profit | Current law | Reform | Change |
|---|---|---|---|---|
| Large company | £2,000,000 | £500,000 | £540,000 | +£40,000 |
| Mid-sized company | £150,000 | £36,000 | £39,000 | +£3,000 |
| Small company | £40,000 | £7,600 | £7,600 | £0 |
| Sole trader | £80,000 | £0 | £0 | £0 |

- The large company's profit exceeds the £250,000 upper limit, so it pays the main rate on all of it: 27% × £2,000,000 = £540,000.
- The mid-sized company's profit falls between the £50,000 lower limit and the upper limit. It pays the main rate less marginal relief of 3/200 × (£250,000 − £150,000) = £1,500. The reform leaves the relief unchanged and raises the tax from 25% × £150,000 − £1,500 = £36,000 to 27% × £150,000 − £1,500 = £39,000.
- The small company's profit is below the lower limit, so it pays the 19% small profits rate under both systems: 19% × £40,000 = £7,600.
- Only companies pay corporation tax, so the sole trader pays none under either system.

## Change the main-pool writing-down allowance

Companies deduct a writing-down allowance on the reducing balance of their main pool of plant and machinery. The rate is `gov.hmrc.corporation_tax.capital_allowances.writing_down_allowance.main_rate`, which is 14% for 2026-27. This reform raises it to 18%.

```python
firms = {
    "manufacturer": {
        "firm_taxable_trading_profit": {2026: 1_000_000},
        "firm_main_pool_brought_forward": {2026: 500_000},
    },
    "workshop": {
        "firm_taxable_trading_profit": {2026: 100_000},
        "firm_main_pool_brought_forward": {2026: 200_000},
    },
}
reform = {
    "gov.hmrc.corporation_tax.capital_allowances.writing_down_allowance.main_rate": {
        "2026-01-01.2100-12-31": 0.18
    }
}

sim = Simulation(situation={"firms": firms}, reform=reform)
sim.calculate("firm_main_pool_writing_down_allowance", 2026)  # [90_000, 36_000]
sim.calculate("firm_taxable_profit", 2026)  # [910_000, 64_000]
sim.calculate("corporation_tax", 2026)  # [227_500, 13_210]
```

| | Manufacturer, current law | Manufacturer, reform | Workshop, current law | Workshop, reform |
|---|---|---|---|---|
| Writing-down allowance | £70,000 | £90,000 | £28,000 | £36,000 |
| Taxable profit | £930,000 | £910,000 | £72,000 | £64,000 |
| Corporation tax | £232,500 | £227,500 | £15,330 | £13,210 |
| Main pool carried forward | £430,000 | £410,000 | £172,000 | £164,000 |

The reform raises the manufacturer's allowance by 4% × £500,000 = £20,000. Its taxable profit is above the upper limit, so its corporation tax falls by 25% × £20,000 = £5,000.

The workshop's allowance rises by 4% × £200,000 = £8,000. Its taxable profit stays in the marginal relief band, where each pound of profit carries tax of 25% + 3/200 = 26.5%. Its corporation tax falls by 26.5% × £8,000 = £2,120:

- Current law: 25% × £72,000 − 3/200 × (£250,000 − £72,000) = £18,000 − £2,670 = £15,330.
- Reform: 25% × £64,000 − 3/200 × (£250,000 − £64,000) = £16,000 − £2,790 = £13,210.

A higher allowance this year leaves a smaller balance to carry forward, so the reform also lowers the allowances available in later years.

## Cut the Employment Allowance and allocate the change to households

`firm_tax_change_total` and `firm_tax_incidence` compare a reform with its baseline across a population, so they need a dataset: in a situation both are 0. This example builds a dataset of two households, each with a weight of 1,000, and three kinds of firm. It cuts the Employment Allowance from £10,500 to £5,000 and sets the incidence shares to 50% capital, 25% consumers and 25% workers in place of the default 100% capital.

```python
import pandas as pd
from policyengine_uk import Microsimulation
from policyengine_uk.data import UKSingleYearDataset

dataset = UKSingleYearDataset(
    person=pd.DataFrame(
        {
            "person_id": [1, 2],
            "person_benunit_id": [1, 2],
            "person_household_id": [1, 2],
            "age": [30, 50],
            "employment_income": [25_000.0, 75_000.0],
        }
    ),
    benunit=pd.DataFrame({"benunit_id": [1, 2]}),
    household=pd.DataFrame(
        {
            "household_id": [1, 2],
            "household_weight": [1_000.0, 1_000.0],
            "region": "LONDON",
            "rent": 0.0,
            "tenure_type": "OWNED_OUTRIGHT",
            "council_tax": 0.0,
            "corporate_sector_wealth": [0.0, 100_000.0],
            "consumption": [20_000.0, 30_000.0],
        }
    ),
    firm=pd.DataFrame(
        {
            "firm_id": [1, 2, 3],
            "firm_weight": [100.0, 300.0, 50.0],
            "firm_paybill": [2_000_000.0, 150_000.0, 60_000.0],
            "firm_employees": [40.0, 5.0, 2.0],
        }
    ),
    fiscal_year=2026,
)
reform = {
    "gov.hmrc.national_insurance.employment_allowance.amount": {
        "2026-01-01.2100-12-31": 5_000
    },
    "gov.contrib.policyengine.firm_incidence.capital": {"2026-01-01.2100-12-31": 0.5},
    "gov.contrib.policyengine.firm_incidence.consumer": {"2026-01-01.2100-12-31": 0.25},
    "gov.contrib.policyengine.firm_incidence.labour": {"2026-01-01.2100-12-31": 0.25},
}

sim = Microsimulation(dataset=dataset, reform=reform)
sim.baseline.calculate("employment_allowance", 2026)  # [10_500, 10_500, 7_500]
sim.calculate("employment_allowance", 2026)  # [5_000, 5_000, 5_000]
sim.calculate("firm_tax_change_total", 2026)  # [2_325_000, 2_325_000]
sim.calculate("firm_tax_incidence", 2026)  # [377.81, 1_947.19]
```

### Firm tax change

Each firm's employer National Insurance before the allowance is 15% of its pay above £5,000 per employee. The allowance covers that liability up to the allowance amount.

| Firm | Weight | Employer NI before allowance | Allowance, current law | Allowance, reform | Extra tax per firm |
|---|---|---|---|---|---|
| 1 | 100 | £270,000 | £10,500 | £5,000 | £5,500 |
| 2 | 300 | £18,750 | £10,500 | £5,000 | £5,500 |
| 3 | 50 | £7,500 | £7,500 | £5,000 | £2,500 |

`firm_tax_change_total` weights each firm's extra tax by `firm_weight`: 100 × £5,500 + 300 × £5,500 + 50 × £2,500 = £2,325,000. Every household carries the same total.

### Household incidence

`firm_tax_incidence` gives each household a share of the total. The share combines three keys, weighted by the incidence parameters:

| Key | Household 1 | Household 2 | Incidence share |
|---|---|---|---|
| Capital: `shareholding` | 0 | 0.001 | 50% |
| Consumers: `consumption_shareholding` | 0.0004 | 0.0006 | 25% |
| Workers: share of weighted employment income | 0.00025 | 0.00075 | 25% |

Household 2 holds all of the corporate sector wealth: £100,000 out of a weighted total of 1,000 × £100,000, a share of 0.001. Consumption shares are £20,000 and £30,000 out of 1,000 × £50,000. Employment income shares are £25,000 and £75,000 out of 1,000 × £100,000.

- Household 1: £2,325,000 × (50% × 0 + 25% × 0.0004 + 25% × 0.00025) = £377.81.
- Household 2: £2,325,000 × (50% × 0.001 + 25% × 0.0006 + 25% × 0.00075) = £1,947.19.

Weighted by household, the incidence adds back to the firm total: 1,000 × (£377.81 + £1,947.19) = £2,325,000. The reform leaves `household_tax` and `gov_tax` unchanged for both households, since `firm_tax_incidence` is not yet a term of either.

Household `ni_employer` counts the change in gross employer National Insurance, so `firm_tax_change_total` subtracts the full change in the Employment Allowance, each simulation computing it on its own liabilities. Together they count the change in what firms pay after the allowance. A firm that stays under the allowance after a rate rise nets to zero: its gross liability and its allowance rise by the same amount, so the household side adds the rise and the firm side takes it off. The firm-side total is then negative, and with the default incidence it is spread by shareholding rather than to the workers whose gross National Insurance rose. That is acceptable only while `firm_tax_incidence` stays out of `household_tax`.
