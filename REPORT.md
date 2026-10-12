# UK microsimulation projection horizon

The pre-fix 2031–2032 projections are **partial and inconsistent**. Earnings,
self-employment income, private pensions and weights continue growing through
Core's variable indices, but rent, council tax and reported State Pension
arrays stop growing. Several stored inputs switch to formulas. The fix
projects every dataset year through 2032, using existing assumptions without
adding forecast values. This makes input handling consistent within that
horizon; it does not certify new OBR forecasts or fix existing projection
omissions.

PR: <https://github.com/PolicyEngine/policyengine-uk/pull/2376>.
Tracking issue: <https://github.com/PolicyEngine/policyengine-uk/issues/2378>.
Final head, tests, costs and independent review are recorded below when complete.

## Scope and evidence

Code baseline: `6d89338abf16`, policyengine-uk **2.126.8**, with
policyengine-core **3.32.27** (`uv.lock:1455–1456`, confirmed installed).
The lock's root package version still says 2.125.1; package source version is
2.126.8. These measurements therefore investigate the dispatched main
checkpoint rather than claiming an exact rerun of W4's certified 2.125.1 pair.
No uk-data build or dependency upgrade was performed.

Dataset: cached `enhanced_frs_2024_25.h5`, Hugging Face snapshot
`47bbb58d3f6467aa4a7059bc6110d2bdcf699b29`.
SHA-256 rechecked in this workspace:
`5ba399ea5ab9a6c7d4e9aaf6c623080beb34d9ad5f330f6244dbad72b8d960b6`.

The prior `measure_all.py` process (PID 43401) has exited. Its complete before,
after and rules-only JSON files and decomposition were retained under
`.verification/` in this workspace. Measurements compare the same code and
data, changing only projection end year from 2030 to 2032. The saved script
constructs one Microsimulation at a time. New cost and test runs use compressor
gates, four or fewer numerical-library threads, and a 20 GB RSS monitor.

## Mechanism read in both packages

Installed Core file root inspected:
`/Users/maxghenis/.subfleet/worktrees/20261011-204722-uk-horizon-2032-r5/.venv/lib/python3.13/site-packages/policyengine_core/`.
Line references below are to that installed 3.32.27 code, not inferred behavior.

1. `holders/holder.py:313–351` looks up an exact stored period.
   `simulations/simulation.py:1036–1039` returns an exact-period cached/stored
   array first. `holders/holder.py:704–732` identifies readable input periods,
   excluding derived calculations; it does not itself project datasets.
2. With no exact array, `simulations/simulation.py:1120–1123` runs the formula
   first. `:1415–1437` also evaluates `adds`/`subtracts` formula declarations.
3. If there is no formula result, `:1145–1197` selects the latest earlier
   readable input and multiplies by the requested/source cumulative-index
   ratio when the variable has `uprating`.
4. Otherwise `:1198–1251` carries an earlier readable input or returns the
   variable default. This is enabled in UK at `tax_benefit_system.py:75`.

UK's `simulation.py:342–345` calls `extend_single_year_dataset` without an
explicit end year. `data/economic_assumptions.py:73–91` now defaults to
`PROJECTION_END_YEAR = 2032`; its previous default was 2030. It copies years
and applies mapped annual growth plus custom rent/council-tax/student-loan
routines. UK stores each projected year's inputs at `simulation.py:518–523`
and moves employment income into `employment_income_before_lsr` at `:209–217`.
`simulation.py` was not edited.

Specific boundary behavior:

- Rent (`variables/input/rent.py:4–11`), council tax
  (`variables/input/consumption/property/council_tax.py:4–15`) and Northern
  Ireland domestic rates (`variables/gov/local_authorities/domestic_rates.py:4–17`)
  have neither a formula nor variable `uprating`, so their arrays carry forward.
- `variables/gov/dwp/state_pension_reported.py:11–12` explicitly returns the
  previous year's value. The dataset stores this reported input and does not
  store `state_pension`. The State Pension output instead uses base-data-year
  reported pension and current rates (`new_state_pension.py:17–26,40–56`,
  `basic_state_pension.py:18–24,39–57`, `additional_state_pension.py:16–21,53–64`,
  under `variables/gov/dwp/`).
- `variables/gov/dwp/pension_credit/pension_credit_reported_capital.py:30–31`
  reads `benunit_reported_capital`, which defaults to −1
  (`variables/household/wealth/benunit_reported_capital.py:25`). The H5 stores
  programme capital but lacks the shared input, so −1 replaces its observation
  after the last dataset year and selects household proxy capital.
- `variables/gov/hmrc/income_tax/bases/savings_income/tax_free_savings_income.py:11`
  adds ISA interest. The H5 stores the tax-free exemption but lacks
  `individual_savings_account_interest_income`, whose default is zero
  (`ISA_interest_income.py:4–13` in the same directory). Its formula therefore
  replaces the exemption with zero after the horizon. Taxable savings then
  subtract zero (`taxable_savings_interest_income.py:15–20`).

## Measured inputs and outputs

All monetary totals below are weighted £bn. The weight row is the **unweighted
sum of household weights**, in millions; calling weighted `.sum()` on the
weight variable itself would incorrectly sum squared weights.

| Input | 2029 | 2030 | 2031 before | 2032 before | 2031 after | 2032 after |
|---|---:|---:|---:|---:|---:|---:|
| Employment income | 1,328.442 | 1,366.190 | 1,417.820 | 1,476.820 | 1,417.260 | 1,475.613 |
| Self-employment income | 134.428 | 139.908 | 145.582 | 151.471 | 145.582 | 151.471 |
| Private pension income | 150.569 | 155.633 | 159.897 | 164.261 | 159.897 | 164.262 |
| Reported State Pension | 135.549 | 138.882 | 139.479 | 140.065 | 142.268 | 145.723 |
| Rent | 148.669 | 152.997 | 153.655 | 154.300 | 157.421 | 161.959 |
| Council tax | 63.247 | 67.017 | 67.306 | 67.588 | 71.001 | 75.217 |
| Household weights, millions | 31.744877 | 31.887730 | 32.024908 | 32.159387 | 32.024847 | 32.159351 |

Employment income is an output of the labour-supply response formula; its
underlying `employment_income_before_lsr` grows by average earnings in both
runs. Small differences in otherwise identically indexed inputs/weights come
from Core's cumulative-index rounding versus direct annual dataset growth.

| Output | 2029 | 2030, both | 2031 before | 2031 after | Change | 2032 before | 2032 after | Change |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Income tax | 369.118 | 387.232 | 411.430 | 405.833 | −5.596 | 433.362 | 427.565 | −5.797 |
| National Insurance | 60.934 | 62.865 | 65.322 | 65.308 | −0.014 | 68.113 | 68.083 | −0.030 |
| Universal Credit | 87.590 | 84.523 | 84.960 | 85.773 | +0.813 | 84.853 | 86.431 | +1.578 |
| State Pension | 136.141 | 140.173 | 144.295 | 144.295 | −0.000274 | 149.683 | 149.683 | −0.000168 |
| Household net income | 1,812.661 | 1,849.617 | 1,901.820 | 1,900.849 | −0.971 | 1,960.197 | 1,956.639 | −3.558 |
| Pension Credit | 7.228 | 7.359 | 6.707 | 7.457 | +0.749 | 6.735 | 7.449 | +0.713 |
| Housing Benefit | 9.134 | 9.370 | 7.909 | 9.636 | +1.727 | 7.894 | 9.910 | +2.016 |
| Council tax reduction | 2.324 | 2.390 | 2.146 | 2.448 | +0.302 | 2.145 | 2.508 | +0.363 |

Per-record growth confirms that flat arrays and changing weighted totals must
be distinguished. Ratios exclude zero-valued records.

| Input/index | 2031 before | 2032 before | 2031 after | 2032 after |
|---|---:|---:|---:|---:|
| Employment before response / average earnings | 3.32% | 3.71% | 3.32% | 3.71% |
| Self-employment / per-capita mixed income | 3.61% | 3.61% | 3.61% | 3.61% |
| Private pensions / private-pension index | 2.30% | 2.30% | 2.30% | 2.30% |
| Reported State Pension / CPI | 0% | 0% | 2% | 2% |
| Household weight / population | 0.43% | 0.42% | 0.43% | 0.42% |
| Private rent / inferred private-rent series | 0% | 0% | 2.213617% | 2.213617% |
| Social rent / social-rent series | 0% | 0% | 3% | 3% |
| Council tax / England; Scotland; Wales | 0% | 0% | 5.50%; 3.84%; 7.43% | 5.50%; 3.84%; 7.43% |

Before the fix, 100% of nonzero rent, council-tax and reported-State-Pension
records have ratio 1 after 2030. Northern Ireland council tax remains zero;
domestic rates have their separate growth mapping.

## Why income tax rises by £24bn despite no dataset year

Before-fix income tax rises from £387.232bn in 2030 to £411.430bn in 2031,
**£24.197bn**. Storing unchanged 2030 inputs explicitly in 2031 gives
£383.747bn, a **£3.486bn decrease** from parameter changes. The remaining
**£27.683bn** is served-input growth and fallback behavior, rather than a
hidden projected dataset year.

The cumulative 2031 decomposition replaces new inputs with old served inputs
one group at a time. Dropping the savings exemption alone at its step adds
£5.604bn income tax; the total old-minus-new difference is £5.596bn. That
attribution is order-dependent, not an independent sum of causal effects.
Other steps confirm the capital-sentinel effect (Pension Credit −£0.750bn,
Housing Benefit −£1.483bn) and flat rent/council-tax effect (UC −£0.759bn).
The last step reproduces the recorded old 2031 level.

## Growth-series coverage

Paths are relative to `gov.economic_assumptions.yoy_growth`. "Source end" is
the last explicit raw or generated date, not evidence of an EFO forecast.
Short series acquire processed dates through 2041 through fiscal conversion;
their later rates still derive from their final source scalar.

| Projection series | Source end | 2031 | 2032 | Source in `yoy_growth.yaml` or generator |
|---|---:|---:|---:|---|
| `finance_ni.domestic_rates` | 2030 | 4.33% | 4.33% | lines 1247–1261 |
| `obr.average_earnings` | 2073 | 3.32% | 3.71% | lines 141–145,186 |
| `obr.consumer_price_index` | 2073 | 2% | 2% | lines 221–225,266 |
| `obr.diesel_spending_litre_proxy` | 2073 | −0.428159% | −0.418243% | lines 425–428,469 |
| `obr.petrol_spending_litre_proxy` | 2073 | −0.428159% | −0.418243% | lines 358–361,402 |
| `obr.mortgage_interest` | 2030 | 5.53% | 5.53% | lines 751–758 |
| `obr.per_capita.gdp` | 2030 | 3.15% | 3.15% | lines 663–670 |
| `obr.per_capita.mixed_income` | 2030 | 3.61% | 3.61% | lines 685–692 |
| `obr.private_pension_index` | 2034 generated | 2.30% | 2.30% | `gov/contrib/create_private_pension_uprating.py:6,13–20` |
| `ons.population` | 2073 | 0.43% | 0.42% | lines 828–831,872 |
| `obr.council_tax.england` | 2030 | 5.50% | 5.50% | lines 605–611 |
| `obr.council_tax.scotland` | 2030 | 3.84% | 3.84% | lines 623–629 |
| `obr.council_tax.wales` | 2030 | 7.43% | 7.43% | lines 641–647 |
| `obr.social_rent` | 2030 | 3% | 3% | lines 760–793 |
| All 14 `ons.private_rental_prices.*` children | 2030 | 2.213617% | 2.213617% | lines 904–1189 |

The private-rent children, each ending in 2030, are `UNITED_KINGDOM`, `ENGLAND`,
`WALES`, `SCOTLAND`, `NORTHERN_IRELAND`, `NORTH_EAST`, `NORTH_WEST`, `YORKSHIRE`,
`EAST_MIDLANDS`, `WEST_MIDLANDS`, `EAST_OF_ENGLAND`, `LONDON`, `SOUTH_EAST`, and
`SOUTH_WEST`. Their final dates are on lines 920,940,960,980,1000,1020,1040,
1062,1082,1102,1122,1142,1162,1182 respectively. Forecast private rents are
inferred from OBR aggregate rent, not public regional forecasts (lines 905–908).
Student-loan cohort projection consumes no growth series.

RPI and CPIH, used indirectly for pension/other uprating, also end in 2073;
their 2031/2032 rates are 2.30%/2.37%. No missing 2031–2032 EFO values were
invented. Existing long-run assumptions or terminal-rate extrapolation are
used; these should be refreshed when the next EFO supplies source values.

Core scalar parameter lookup (`parameters/parameter.py:223–227`) selects the
latest dated value at or before the requested instant. A non-null terminal
value persists; an explicit terminal null returns `None`. Thus a raw growth
parameter repeats its last **rate**, whereas a cumulative index repeats its
last **level**. UK `utils/parameters.py:102–119` materialises fiscal values
through 2040, and Core `Parameter.update` restores a boundary value in 2041
(`parameter.py:175–192`). Generated economic cumulative indices only compound
through 2039 (`create_economic_assumption_indices.py:38–47`) and stop growing
afterward. Do not equate those generated dates with forecast coverage.

## Tax and benefit parameters in 2031–2032

| Parameter | 2030 | 2031 | 2032 |
|---|---:|---:|---:|
| Personal allowance, annual £ | 12,570 | 12,830 | 13,090 |
| Basic-rate limit, annual £ | 37,700 | 38,500 | 39,300 |
| Additional-rate threshold, annual £ | 125,140 | 125,140 | 125,140 |
| NIC primary threshold, weekly £ | 241.73 | 246.73 | 251.73 |
| NIC upper earnings limit, weekly £ | 966.73 | 987.12 | 1,007.50 |
| New State Pension, weekly £ | 269.988903 | 276.738293 | 285.870760 |
| UC standard allowance, single 25+, monthly £ | 461.275000 | 470.500659 | 479.910989 |
| Pension Credit minimum guarantee, single, weekly £ | 258.374794 | 263.542379 | 268.813404 |

`gov/hmrc/create_threshold_indexation.py:104–121,142–198,243–258` generates
personal-allowance/basic-rate-limit values after explicit April 2030 values,
using September CPI with statutory upward rounding. NIC alignment is a model
assumption documented at `:24–46`; the additional-rate threshold/rates retain
their final scalars. Core metadata uprating generates benefit amounts by an
index ratio (`parameters/operations/uprate_parameters.py:339–374`). UC follows
`gov.benefit_uprating_cpi`, itself lagged CPI; State Pension follows triple-lock
effective growth (2.5% in 2031 and 3.3% in 2032), generated at
`gov/dwp/state_pension/triple_lock/create_triple_lock.py:89–115`. Stored
reported State Pension is CPI-projected, a separate concept from that output.

## Fix, tests, cost and review

The production change only sets the dataset projection default to 2032.
Retaining a finite horizon avoids copying datasets out to 2073 and crossing
the generated economic-index horizon. The changelog fragment is
`changelog.d/fix-projection-horizon-obr.fixed.md`. Tests use synthetic tables,
cover every dataset year, per-index annual growth, a Hypothesis growth-ratio
property, rent/council-tax projections and the documented after-horizon
formula/index/carry behavior. Added tests specifically reproduce the legacy
capital and savings-input boundary cases and check reported State Pension.

New cost pair (same package, explicit 2030 override only for before; one
fresh process per case):

| Metric | Before | After |
|---|---:|---:|
| Dataset years | 2024–2030 | 2024–2032 |
| Import seconds | 98.0 | 54.6 |
| Microsimulation load seconds | 33.2 | 13.3 |
| Peak RSS after load, decimal GB | 2.220 | 2.646 |
| 2032 net-income calculation seconds | 2.0 | 2.6 |
| Peak RSS through 2032 calculation, decimal GB | 2.529 | 2.921 |

The after-load RSS increases 0.426 GB; overall peak increases 0.392 GB. Wall
times are observed host timings, not a controlled performance claim: host
contention/cache warmth differ. Compressor memory before the simulations was
7.898 GB / 7.850 GB, both below 30 GB. Costs use `resource.ru_maxrss` in bytes
on macOS. The saved prior `cost_before.json` actually reports 1.543 GB RSS and
314s load under heavy contention; its separate 2.466 GB memory-footprint metric
and the prompt's 2.18 GB must not be substituted for RSS. `/usr/bin/time -l`
could not read `kern.clockrate` in this sandbox and exited 1 after the before
Python run completed; both cost JSON results were successfully written.

Validation: changed test file and economic-assumption regressions are running
serially, with gates before each Microsimulation construction. There is no
file named `test_economic_assumptions*` at this checkpoint; the relevant files
are listed in the final test result below.

## Remaining limits and uk-data follow-up

Pension Credit −1 reappears in 2033 for this legacy dataset. Existing
`test_benunit_reported_capital_properties.py:298–311` deliberately expires
direct programme inputs in later years; Core also rejects declaring formula
and uprating together (`variables/variable.py:413–420`). Changing the variable
to carry would violate that contract. A uk-data follow-up should materialise
`benunit_reported_capital` from the survey's underlying benefit-unit capital
observation (such as TOTCAPB4), while retaining distinct countable-capital
programme overrides. Do not blindly copy Pension Credit countable capital
into the generic input. Likewise audit the relationship between the survey
tax-free savings exemption and its ISA-interest source. No uk-data PR or build
was opened; these belong in the hub's d833 batch.

Four preexisting inputs have variable `uprating` but no dataset projection
mapping: `pension_contributions_via_salary_sacrifice`,
`water_and_sewerage_charges`, `housing_service_charges`, and `rail_usage`.
They stay at their 2024 stored values through the horizon; Core applies only
the last-stored-to-requested index ratio afterward. This extension does not
fix those separate omissions.

PR #2274 at `f86bdbbea37fe92892a37f0ea29cd8268ba7014c` replaces the same default
with `None` and derives a cap using `min(2030, scenario_end)`. Reconcile by
keeping the legacy default `PROJECTION_END_YEAR=2032` and capping only explicit
finite CGT scenarios at their supported year, preserving unsupported-span
errors. Its EOT scenario has no 2031+ values; do not invent them. #2274 was not
edited.

Saved full-period impact calculations and an isolated 2032 household-net-income
cost calculation differ: the latter returns £1,959.453bn before, versus
£1,960.197bn in the inherited impact run. The saved before-source Python files
match the checkpoint except for the horizon change; calculation-order or
runtime details behind this discrepancy remain partly unverified. A concrete
order-sensitive path is `variables/household/demographic/current_education.py:21–26`:
it inherits previous-year education only if that year's array is already
cached; otherwise lines 27–48 infer enrolment from age. Education reaches
household benefits and net income through child/UC eligibility, childcare
grants, bursary funds and Care to Learn. Maintenance-loan formulas also inspect
cached evidence. Thus the sequential run and isolated 2032 run can execute
different branches after the old horizon. This path is confirmed in code, but
the full £0.744bn attribution has not been measured. Both dataset loading
routes encode enums before the same input-setting loop. Reported impact uses
the same calculation order before/after, and cost is a separate metric.
No exact certified-pair reproduction, forthcoming EFO data, uk-data rebuild,
or beyond-horizon full-survey validation is claimed. The known unrelated
`test_dataframe_dataset.py` failure was excluded.
