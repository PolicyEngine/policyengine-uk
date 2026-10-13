# UK microsimulation projection horizon

The pre-fix 2031–2032 projections are **partial and inconsistent**. Earnings,
self-employment income, private pensions and weights continue growing through
Core's variable indices, but rent, council tax and reported State Pension
arrays stop growing. Several stored inputs switch to formulas. The fix
projects every dataset year through 2032, using existing assumptions without
adding forecast values. This makes input handling consistent within that
horizon; it does not certify new OBR forecasts. A compatibility step preserves
Core's growth for unmapped inputs after 2030 without changing historical
projection omissions.

PR: <https://github.com/PolicyEngine/policyengine-uk/pull/2376>.
Tracking issue: <https://github.com/PolicyEngine/policyengine-uk/issues/2378>.
Reviewed implementation head:
`9a8c07a04303e6fdc278322930414c245105ea55`; subsequent commits record evidence.

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
data, initially changing only projection end year from 2030 to 2032. The saved script
constructs one Microsimulation at a time. New cost and test runs use compressor
gates, four or fewer numerical-library threads, and a 20 GB RSS monitor.

The final impact, matched costs and corrected tests had all finished before
the reboot. This resume salvaged them from the interrupted workspace
`20261012-044816-uk-horizon-2032-sol`, checked every table against its JSON,
rechecked the dataset hash and audited mechanism and coverage against source.
No completed simulation was repeated. Production code, tests and durable
documentation there already match the pushed implementation head above;
the remaining uncommitted work was the final evidence update in this report.

## Mechanism read in both packages

Installed Core file root inspected:
`/Users/maxghenis/.subfleet/worktrees/20261012-075210-uk-horizon-2032-r7/.venv/lib/python3.13/site-packages/policyengine_core/`.
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
explicit end year. `data/economic_assumptions.py:100–117` now defaults to
`PROJECTION_END_YEAR = 2032`; its previous default was 2030. It copies years
and applies mapped annual growth plus custom rent/council-tax/student-loan
routines. UK stores each projected year's inputs at `simulation.py:518–523`
and moves employment income into `employment_income_before_lsr` at `:209–217`.
`simulation.py` was not edited.

`data/economic_assumptions.py:87–97,177–201` also preserves variable-index
growth for unmapped stored columns after 2030, using Core's
`_uprating_index_value` (`simulations/simulation.py:81–108`) and the same
missing/zero-index treatment as `:1185–1192`. Mapped/custom projections take
priority; the three energy exclusions in `uprating_indices.yaml:1–23` remain
flat. This closes a regression found by independent review: merely extending
the horizon installed flat arrays where Core previously supplied growth.

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

The final after columns are freshly measured at corrected implementation
head `9a8c07a04303e6fdc278322930414c245105ea55`, on the same dataset hash and
sequential calculation order as the retained before run. All 2030 outputs
are exactly unchanged. Final impact run peak RSS was 3.291 GB, compressor
21.947 GB before construction; the process exited before the cost run began.

All monetary totals below are weighted £bn. The weight row is the **unweighted
sum of household weights**, in millions; calling weighted `.sum()` on the
weight variable itself would incorrectly sum squared weights.

| Input | 2029 | 2030 | 2031 before | 2032 before | 2031 after | 2032 after |
|---|---:|---:|---:|---:|---:|---:|
| Employment income | 1,328.442 | 1,366.190 | 1,417.820 | 1,476.820 | 1,417.814 | 1,476.817 |
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
| Income tax | 369.118 | 387.232 | 411.430 | 405.916 | −5.514 | 433.362 | 427.752 | −5.610 |
| National Insurance | 60.934 | 62.865 | 65.322 | 65.321 | −0.000274 | 68.113 | 68.113 | −0.000155 |
| Universal Credit | 87.590 | 84.523 | 84.960 | 85.773 | +0.813 | 84.853 | 86.431 | +1.578 |
| State Pension | 136.141 | 140.173 | 144.295 | 144.295 | −0.000274 | 149.683 | 149.683 | −0.000168 |
| Household net income | 1,812.661 | 1,849.617 | 1,901.820 | 1,900.753 | −1.067 | 1,960.197 | 1,956.421 | −3.777 |
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

Final compatibility growth (median record ratios, rounding to percentages):
salary-sacrifice contributions 3.320244%/3.709875%, water charges
4.499848%/4.500225%, housing services 2.399692%/3.319662%, and rail usage
0%/0%. These are cumulative-index ratios, including Core's five-decimal index
rounding, rather than independently fabricated growth rates. Energy remains
flat by its documented dataset price basis, verified in synthetic tests;
those three fields were not included in the final survey measurement JSON.

## Why income tax rises by £24bn despite no dataset year

The retained decomposition below uses the earlier horizon-only correction as
its counterfactual. Its individual replacements are cumulative and order
dependent; they are not an additive attribution of the final corrected head.
The final income-tax reduction is £5.514bn/£5.610bn in 2031/2032. Restoring
unmapped growth raises income tax £0.082bn/£0.188bn relative to the earlier
correction, which explains why its old impact figures must not be reused.

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
| `ofwat.water_bills` (unmapped-input compatibility) | 2029 | 4.5% | 4.5% | lines 1194–1202 |
| `obr.lagged_average_earnings` (compatibility) | 2074 generated | 2.4% | 3.32% | `lag_average_earnings.py:14–17`, `lagged_series.py:13–14,29–31` |

Rail usage uses `gov.dft.rail.ridership_index`, a cumulative index rather than
a YoY series. Its last raw value is 1.044 in 2029 (`ridership_index.yaml:20–22`),
so its 2031/2032 ratio is one. Other compatibility fields use earnings,
per-capita GDP or per-capita mixed income, whose coverage appears above.

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
The README and growth-file header now describe the checked-in convergence
rates accurately: their annual steps are not uniform, and the 2031–2032
assumptions directly affect this horizon. Only explanatory text changed;
all parameter values are unchanged.

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

The production change sets the dataset projection default to 2032 and
preserves variable-index growth in added years for unmapped inputs.
Retaining a finite horizon avoids copying datasets out to 2073 and crossing
the generated economic-index horizon. The changelog fragment is
`changelog.d/fix-projection-horizon-obr.fixed.md`. Tests use synthetic tables,
cover every dataset year, per-index annual growth, a Hypothesis growth-ratio
property, rent/council-tax projections and the documented after-horizon
formula/index/carry behavior. Added tests specifically reproduce the legacy
capital and savings-input boundary cases and check reported State Pension.
Additional tests exercise all twelve eligible unmapped fields, legacy values
through 2030, index ratios after 2030, energy exclusions and growth reset.

Final matched cost pair at the corrected implementation (Python 3.13.15,
Core 3.32.27, same H5; explicit 2030 override only for before):

| Metric | Before | After |
|---|---:|---:|
| Dataset years | 2024–2030 | 2024–2032 |
| Import seconds | 108.1 | 120.1 |
| Microsimulation load seconds | 55.5 | 72.1 |
| Peak RSS after load, decimal GB | 2.210 | 2.473 |
| 2032 net-income calculation seconds | 17.4 | 21.8 |
| Peak RSS through 2032 calculation, decimal GB | 2.459 | 2.735 |

The load peak rises 0.263 GB and overall peak 0.276 GB. These are observed
host timings, not a controlled performance claim: contention/cache warmth
vary. Imports were overlapped, while marker files blocked all Microsimulation
construction until the preceding simulation process exited. Compressor
memory immediately before construction was 20.797/20.548 GB; the 20 GB
per-process monitor stayed well below its cap. macOS `resource.ru_maxrss`
reports bytes, converted here to decimal GB. Final isolated after net income
£1,956.421bn agrees with the sequential final-impact result; isolated before
remains £1,959.453bn, with the order-sensitive discrepancy discussed below.

Earlier horizon-only costs (2.529/2.921 GB overall peaks) and the resumed
prompt's 2.18 GB are superseded by this matched pair. The inherited
`cost_before.json` actually reported 1.543 GB RSS and used a separate memory
footprint metric; neither is substituted for the final RSS measurements.

Validation uses the locked workspace environment (Python 3.13.15, Core
3.32.27), serial `pytest -n 0`, four numerical-library threads, compressor
gates and a 20 GB process monitor. The full eight-file run completed with
154 passed, 1 xpassed and one unchanged September-CPI Hypothesis timing flake
in 2750.14s: the first call took 295.04ms against a 200ms deadline, then
0.06ms on replay. No arithmetic assertion failed. Peak RSS was 0.453 GB.

Those full files were `test_projection_horizon.py`,
`test_no_economic_assumptions.py`, `test_rent_uprating.py`,
`test_council_tax_uprating.py`, `test_domestic_rates_uprating.py`,
`test_benunit_reported_capital_properties.py`, `test_threshold_indexation.py`
and `test_triple_lock_statutory_inputs.py`. No file named
`test_economic_assumptions*` exists at this checkpoint. After the compatibility
correction, the entire changed projection file and no-economic-assumptions
file, plus that CPI property, passed **all 16 tests** in 226.07s; peak RSS
0.398 GB. This includes all thirteen projection tests at `9a8c07a`.

Local harness exceptions: optional Hypothesis source-constant mining is
disabled because it stalled collection for 774.77s; explicit strategies and
example counts remain unchanged. Constructors use `system.clone`, the seam
supported by the repository's `cloned_uk_tax_benefit_system` fixture, with
independent state. The final rerun disables the local Hypothesis deadline
without changing source tests or mathematical assertions. Ordinary
unmodified-harness/full-suite CI is not claimed. Full `make format` passed
across 1,363 Python files.

On this resume, `UV_LINK_MODE=clone uv sync --frozen --extra dev` completed
in the assigned workspace, installing UK 2.126.8/Core 3.32.27. Full
`make format` passed again: 1,363 Python files unchanged and Ruff checks passed.
A parsed-YAML comparison confirmed all growth parameter values unchanged,
and the five cited Core implementation files are byte-identical to the
previously audited installation. Completed tests and simulations were reused
because the production implementation and test files are unchanged.

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

Four H5 inputs have variable `uprating` but no dataset projection mapping:
`pension_contributions_via_salary_sacrifice`, `water_and_sewerage_charges`,
`housing_service_charges`, and `rail_usage`. They retain their base-year
stored values through 2030; the final correction restores their former Core
index growth in 2031–2032. Twelve such fields exist in the model registry,
all covered by the compatibility step. Historical omissions remain a follow-up.

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

## Independent review and handoff

Requested `subfleet run --task review --tier hard` completed as
`20261012-072250-uk-horizon-2032-corrected-head-review` at exact implementation
head `9a8c07a04303e6fdc278322930414c245105ea55`: **no blocking findings; the
earlier P2 is resolved**. It saw all sixteen passing tests. Final impact and
cost runs completed after that review; an independent numerical audit checked
refreshed tables against the JSON. Report-only commits follow the reviewed
implementation without changing production code. This report accompanies
the final PR evidence update; no merge is performed. Final PR status, head
SHA and the additional final-head review are recorded in workspace-local
`handoffs.jsonl`, respecting the assigned-workspace restriction. No CI
rerun was requested.
