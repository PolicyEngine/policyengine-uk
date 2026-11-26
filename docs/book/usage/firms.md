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

Every firm variable uses `entity = Firm` and a yearly period. Each parameter cites legislation or GOV.UK guidance. Values announced but not yet enacted are marked in their YAML files and are kept in the baseline, as for other announced Budget measures: the 12% main writing-down allowance from April 2027, the 50% main-rate first-year allowance from 1 January 2027 and the 6% bank surcharge from 1 January 2027. Finance Bill 2026-27 had not received Royal Assent on 22 November 2026.

| Programme | Main variables | Rules |
|---|---|---|
| Employer National Insurance | `firm_employer_ni`, `firm_employer_ni_before_allowance` | Class 1 secondary contributions with the `gov.hmrc.national_insurance.class_1` rates and thresholds. Pay above the secondary threshold can be an input; by default it is approximated from the paybill and the number of employees, less any staff supplied as paid at or below the secondary threshold (see the pay-distribution inputs below). |
| Employment Allowance | `employment_allowance`, `employment_allowance_eligible` | The amount from 2014 (now £10,500), capped at employer National Insurance liability. Excludes single-director companies and public bodies, and applies the £100,000 prior-year liability limit from 2020-21 to 2024-25. |
| Apprenticeship levy | `apprenticeship_levy` | 0.5% of the paybill (after any National Minimum Wage top-up) less the £15,000 allowance, which connected employers share. |
| Auto-enrolment | `firm_auto_enrolment_employer_contribution`, `firm_auto_enrolment_qualifying_earnings` | The 3% employer minimum contribution on qualifying earnings between £6,240 and £50,270. Qualifying earnings can be an input; by default they are approximated from the paybill and the number of employees, less any staff supplied as paid at or below the earnings trigger or above the upper limit (see the pay-distribution inputs below). |
| Corporation tax | `corporation_tax`, `firm_taxable_profit`, `firm_marginal_relief`, `firm_losses_used` | Main and small profits rates, marginal relief at a 3/200 fraction with limits divided by associated companies, and loss relief with the £5 million deductions allowance. Only companies are liable (`firm_legal_form`). A close investment-holding company or a non-UK-resident company gets no small profits rate or marginal relief (CTA 2010 ss.18A, 18B and 18N): set `firm_small_profits_rate_excluded` (default false). |
| Capital allowances | `firm_capital_allowances` and its components | Full expensing, the 50% special-rate first-year allowance, the annual investment allowance, the main-rate first-year allowance (40% from 1 January 2026), writing-down allowances, the structures and buildings allowance, and balancing charges. A company that disposes of fully expensed main-rate plant pays a balancing charge on the disposal value outside the main pool (`firm_full_expensing_balancing_charge`); the same disposal of special-rate plant that had the 50% allowance, and disposals of super-deduction assets, are not modelled, so `firm_disposal_proceeds_full_expensing` should be 0 before April 2023. The charge applies only while the full expensing rate is above 0, so a reform that sets that rate to 0 also removes the charge on assets fully expensed earlier. New main-rate plant for leasing (`firm_capex_main_pool_new_for_leasing`) gets no full expensing: it takes the annual investment allowance, then the main-rate first-year allowance. New special-rate plant for leasing gets no first-year allowance; enter it as `firm_capex_special_rate_used` so it takes the annual investment allowance and then the special rate pool. |
| R&D relief | `firm_rd_expenditure_credit`, `firm_rd_additional_deduction`, `firm_rd_payable_credit` | The merged-scheme expenditure credit (20%), the SME scheme for every SME before April 2024 and enhanced support for R&D-intensive loss-making SMEs from then. `firm_rd_payable_credit` is paid on the trading loss left after setting it against the same period's non-trading profits (CTA 2009 s.1056(2)(a)), capped at the qualifying expenditure plus the additional deduction. `firm_rdec_excess_payable` is the expenditure credit paid out after it discharges the year's corporation tax, less the notional tax deduction: corporation tax on the credit at the main rate, or at the small profits rate where the company has no profits chargeable at the main rate ignoring the credit. A loss-making company with £1 million of R&D in 2025-26 is paid £200,000 less 19% notional tax, £162,000. The notional tax is not paid in the year. The PAYE and National Insurance cap applies when its inputs are supplied (see below). |
| Bank surcharge | `bank_surcharge` | 8% above a £25 million allowance from 2016, and 3% above £100 million from April 2023. The 6% rate announced for 1 January 2027 to 31 March 2028 is marked as not yet enacted. Surcharge profits leave out the R&D expenditure credit, and `firm_bank_surcharge_allowance_share` (default 1) gives a bank in a group its share of the allowance. |
| Business rates (England, Wales, Scotland) | `firm_business_rates` and its reliefs | England: multipliers for 2023-24 to 2027-28, including the 2026 retail, hospitality and leisure (RHL) and high-value multipliers; small business rate relief, charitable relief, RHL relief to 2025-26, pubs and live music venues relief, and empty property relief. Wales and Scotland: multipliers or poundage, the small business scheme and mandatory charitable relief (80%), 2023-24 to 2026-27. In Wales a charity gets charitable relief instead of SBRR; in Scotland it gets the larger of SBBS and charitable relief. |
| Employer Class 1A NIC | `firm_class_1a_ni` | Class 1A percentage times `firm_class_1a_benefits`, the cash equivalent of benefits in kind. |
| VAT | `firm_vat`, `firm_vat_registered`, `firm_output_vat` | The registration threshold (£85,000, then £90,000 from April 2024), output VAT less recoverable input VAT with the partial exemption standard method (percentage rounded up, reg 101(5)), and the flat rate scheme with the 16.5% limited cost trader rate. Uses the existing `gov.hmrc.vat` rate parameters. |

Six optional inputs describe how a firm's pay is spread, so the employer National Insurance and auto-enrolment approximations need not assume every employee earns the firm's average pay. Each pair is a headcount and the total pay of those employees, and all default to 0:

- `firm_employees_below_secondary_threshold` and `firm_paybill_below_secondary_threshold`: staff paid at or below the annual secondary threshold, who pay no secondary contributions.
- `firm_employees_below_auto_enrolment_earnings_trigger` and `firm_paybill_below_auto_enrolment_earnings_trigger`: staff paid at or below the £10,000 earnings trigger, who need not be enrolled.
- `firm_employees_above_auto_enrolment_upper_limit` and `firm_paybill_above_auto_enrolment_upper_limit`: staff paid above the qualifying earnings upper limit, who each contribute the full band.

The formulas clip inconsistent values silently: negative values count as 0, a headcount is capped at the employees left, and a paybill at the paybill left (and, at or below the secondary threshold, at that headcount times the threshold). If the paybill above the upper limit is less than that headcount times the limit, those staff are treated as part of the remaining group. With the defaults, every employee is enrolled at the firm's average pay, so the £10,000 earnings trigger is not applied.

`policyengine_uk/programs.yaml` lists these programmes with the years their parameters and tests cover.

### National Minimum Wage

Two optional inputs describe the firm's low-paid workers as one block: `firm_low_paid_hours`, their annual hours, and `firm_low_paid_paybill`, the pay for those hours (part of `firm_paybill`). Both default to 0. `firm_minimum_wage_cost` is the extra pay needed to bring the block up to the adult rate (the national living wage): the rate times the hours, less their pay, floored at zero. The rate is the top age band of `gov.hmrc.minimum_wage.non_apprentice`, read at 30 April like other yearly parameters, so 2026 uses the £12.71 rate from April 2026.

`firm_paybill_after_minimum_wage` is `firm_paybill` plus that cost. The apprenticeship levy and the default employer National Insurance and auto-enrolment approximations read it, so they rise with the floor. A supplied `firm_class_1_earnings_above_secondary_threshold` or `firm_auto_enrolment_qualifying_earnings` is used as given. With the pay-distribution inputs supplied, the extra pay falls in the remaining group, which overstates the base if the low-paid staff are at or below the secondary threshold or the earnings trigger. The cost is a firm cost, not a tax, so it is not a term of `firm_tax` or `firm_only_tax`. Where pay already meets the rate the cost is 0 and every result is unchanged.

The block is treated as paid its average hourly wage, so the cost is understated where pay within it varies: hours paid above the rate offset hours paid below it. Negative inputs count as 0. The model's rates start in October 2010, so the cost is 0 for 2010 and earlier. The younger-worker and apprentice rates are not modelled. `firm_taxable_trading_profit` is an input, so the extra pay, though deductible, does not reduce the firm's taxable profit or corporation tax; reduce that input yourself if you want the deduction.

## Aggregates and incidence

Four variables combine the firm-level results:

- **`firm_tax`** (firm): the firm's total statutory liability to corporation tax, the bank surcharge, the apprenticeship levy, employer National Insurance after the Employment Allowance, business rates and VAT, less R&D tax credits paid out to the firm.
- **`firm_only_tax`** (firm): the liability set by rules that only the firm side models: corporation tax, the bank surcharge, the apprenticeship levy and business rates, less R&D tax credits paid out. It leaves out employer National Insurance, whose rates and thresholds reach households through `ni_employer`, and VAT, whose rates reach households through `vat`. It also leaves out the Employment Allowance.
- **`firm_tax_change_total`** (household): the reform's `firm_only_tax` less the baseline's, summed over firms with `firm_weight`, less the change in the weighted Employment Allowance, each simulation computing it on its own employer National Insurance liabilities. Household `ni_employer` counts the gross change, so together they count the change in what firms pay after the allowance; a firm that stays under the allowance after a rate rise nets to zero. It also adds the change in weighted `firm_vat` from VAT rules other than the rates (the registration threshold, the flat rate scheme and partial exemption), with the rates held at baseline, since household `vat` already carries rate changes. A firm whose registration flips counts its full liability at baseline rates, with no behavioural response. A reform that changes both the rates and those rules drops their interaction, and with the default incidence a VAT rule change falls on shareholders. Without a supplied prior-year input, the 2020-21 to 2024-25 prior-year limit reads this year's liabilities under each simulation's own rules, so a rate rise can take a firm over it. Every household carries the same total. It is 0 without a baseline, in a simulation built from a situation, and where the simulation has no firms.
- **`firm_tax_incidence`** (household): each household's share of `firm_tax_change_total`, split between capital (by `shareholding`), consumers (by `consumption_shareholding`) and workers (by the household's share of weighted employment income). The shares are the `gov.contrib.policyengine.firm_incidence` parameters `capital`, `consumer` and `labour`, which default to 1, 0 and 0.

`firm_tax` is a receipts measure. Summed over firms it must not be added to `gov_tax`, whose household terms already count employer National Insurance, VAT and business rates as incidence. None of the four variables is a term of `gov_tax` or `household_tax` yet.

Worked examples of firm reforms, including incidence, are in [Firm reforms](firm-reforms.md).

## Known simplifications

- Every firm has an April to March financial year.
- Most yearly parameters are read at 30 April, so changes dated 1 January are not apportioned. This affects the 40% and 50% main-rate first-year allowances. The annual investment allowance limit and the bank surcharge rate are day-weighted over 6 April to 5 April instead: 2026-27 has a surcharge rate of (270 × 3% + 95 × 6%) / 365 ≈ 3.78%. Because the window starts on 6 April, a change dated 1 April counts for 5 days of the year before, so 2027-28 has a surcharge rate of about 5.96% and 2022-23 about 7.93%.
- Employer National Insurance and auto-enrolment use firm-level approximations, since there is no per-employee pay yet. They treat the employees outside the optional pay-distribution inputs as all paid the same, and apply thresholds annually rather than per pay period. Without the auto-enrolment inputs the £10,000 earnings trigger is not applied, and the age conditions, opt-outs and opt-ins are not modelled.
- The National Minimum Wage floor treats the low-paid workers as one block paid its average hourly wage and applies only the adult rate (see above).
- Business rates assume one aggregate property per firm and have no transitional relief. Northern Ireland rates are not modelled (0).
- Firm amounts are stored in single precision (float32), as for every policyengine-core variable. A firm with £10 million to £50 million of turnover can show rounding of about £1, so tests use small absolute margins.
- **Business rates in Wales and Scotland.** The nation comes from `firm_region`; a Welsh, Scottish or Northern Irish region overrides `firm_in_england`, and the English reliefs apply only where `firm_rates_in_england` is true. Wales uses one multiplier to 2025-26 (0.535, 0.562, 0.568), and in 2026-27 a standard multiplier of 0.502, a retail multiplier of 0.350 for shops, kiosks, pharmacies and post offices below £51,000 (`firm_is_wales_retail_property`), and a higher multiplier of 0.515 above £100,000, except for the 19 public-service descriptions in WSI 2025/1163 reg 4, such as hospitals and schools (`firm_is_wales_higher_multiplier_excluded`). Welsh small business rates relief is 100% at £6,000 or less, tapering in a straight line to 0% at £12,000, for occupied property of a firm with at most two properties. Scotland charges the basic property rate (49.8p to 2025-26, 48.1p in 2026-27), plus the intermediate supplement above £51,000 up to £100,000 and the higher supplement above £100,000. The Small Business Bonus Scheme gives single-property firms 100% relief at £12,000 or less, tapering to 25% at £15,000 and to 0% at £20,000. Not modelled: Welsh childcare and post office relief, SBBS for several properties, and empty property, hospitality and transitional reliefs in Wales and Scotland. From 1 April 2027 WSI 2026/133 renames the Welsh retail multiplier the lower multiplier, widens it to about 37 descriptions (including pubs, restaurants, hotels and leisure) and raises the higher multiplier to 1.042 times the standard; this is not modelled. Central-list properties (WSI 2025/1163 reg 5) are not distinguished. Values for 2027-28 onwards carry forward the 2026-27 ones, and years before 2023-24 reuse the 2023-24 values, which are not verified for those years. Empty property relief applies in England only; property with rateable value below £2,900 is exempt for as long as it is empty. In England the RHL multipliers apply to occupied property only, and before 2024-25 unoccupied and charity property paid the standard multiplier whatever its rateable value (SI 2024/111 extended the small business multiplier to them). The independent school exclusions from charitable relief are not modelled, nor is SSI 2026/68 reg 6(5).
- **R&D expenditure credit PAYE and NIC cap.** After the notional tax deduction, the payable credit is capped. Under the merged scheme (from April 2024) the cap is £20,000 plus three times the company's relevant PAYE and Class 1 NIC liabilities, for all employees adjusted for connected-company workers (CTA 2009 s.1042I step 3, ss.1112B–1112D); supply them as `firm_relevant_paye_nic_liabilities`. Before April 2024 the cap was the PAYE and NIC on staff directly engaged in R&D, with no fixed amount (s.104N step 3, s.104P); supply it as `firm_rd_staff_paye_nic`. The cap applies only when `firm_rdec_paye_nic_cap_supplied` is true (default false). The excess is carried to the next period's credit (s.1042J), which is not modelled, nor are the short-period reduction of the £20,000 and the s.1112E exemption. The same flag and `firm_relevant_paye_nic_liabilities` cap the SME payable credit `firm_rd_payable_credit` for accounting periods beginning on or after 1 April 2021, at £20,000 plus three times the company's PAYE and Class 1 NIC on all employees (s.1058(1A) and ss.1058A–1058C, from April 2024 s.1112B). The exemption for companies creating or managing their own intellectual property (s.1058D, from April 2024 s.1112E) is not tested: leave the flag false for such a company.
- **Pubs and live music venues relief.** 15% in 2026-27, rising to 35% in 2027-28 and 2028-29 (BRIL 8/2026). The 15% rate is kept only for live music venues with rateable value of £1m or more; pubs get 35% at any rateable value. Set `firm_is_live_music_venue` as well as `firm_is_pub_or_live_music_venue` to mark a live music venue.
- **Small business rate relief taper (England).** Under LGFA 1988 Sch 4ZA para 4(1) and SI 2023/1250 reg 3, the bill in the taper is the gross bill divided by E = 3,000 / (rateable value − £12,000), calculated to three decimal places, so relief is the gross bill less the gross bill divided by E. At £14,999, E rounds to 1.000 and no relief is given. The model rounds to the nearest third decimal (the regulation does not say whether to round or truncate). For qualifying RHL properties in 2027-28 and 2028-29 the model assumes the same form with £18,000 and £21,000; the amending regulations are not yet made.
- Corporation tax has no group relief, Patent Box or quarterly instalment payments.
- Not modelled at all: Northern Ireland business rates (they need a district for each firm), the bank levy, the energy profits levy, the electricity generator levy, the residential property developer tax, the digital services tax, the diverted profits tax, the plastic packaging tax and the soft drinks industry levy.
- VAT registration is tested on annual turnover, not a rolling 12 months, and there is no cash or annual accounting.
- Freeport employer National Insurance relief enters through `firm_zero_rated_class_1_earnings`, and so does investment zone relief; `firm_in_freeport` on its own changes nothing. Veterans relief enters the same way: earnings of a veteran in the first year of civilian employment up to the veterans upper secondary threshold (£50,270 in 2026-27) carry a 0% secondary rate, in tax years 2022-23 to 2027-28 (National Insurance Contributions Act 2022 s.6(4)). The apprenticeship levy is UK-wide and does not depend on `firm_region`.
- Class 1A National Insurance (`firm_class_1a_ni`) is the Class 1A percentage times `firm_class_1a_benefits` (SSCBA 1992 s.10). The percentage equals the secondary Class 1 rate read at 30 April (13.8%, then 15% from 2025-26), except 14.53% in 2022-23. There is no threshold and the Employment Allowance cannot be set against it. It is part of `firm_tax` but not `firm_only_tax`, because households already carry Class 1A through `ni_class_1a` in `ni_employer`.
- In a simulation of firms alone, household variables cannot be computed, since there are no benefit units.
