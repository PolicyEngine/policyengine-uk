# Housing Benefit assessment facts and timing

Housing Benefit calculations use individual policy parameters and the existing
person, benefit-unit and household entities. Additional facts are needed where
annual income, age and household wealth cannot establish statutory eligibility.
These inputs do not change a claimant's circumstances automatically.

## Annual amounts and dated facts

Weekly amounts become annual amounts using the model's 52-week convention.
Ordinary parameters retain the model's 30 April fiscal-year sampling. Preserved
Boolean schedules and `fiscal_year_segments` handle the December 2018 removal
of the under-65 allowance, the two-child restriction and its removal, and
jurisdiction-specific family-premium abolition. Those calculations hold supplied
family facts fixed and apply the rule separately in each segment before averaging.
They do not multiply a Boolean input by an assumed share of a year.

`housing_benefit_assessment_date` defaults to 6 October, matching annual age
inputs. It is the date for reported childcare status, retained capital and pending
non-dependant changes. The resulting point-in-time weekly calculation is
annualised; it is not a reconstruction of every week's actual award. Supply
different dates and factual inputs to examine individual assessments. Do not
interpret the date as a guarantee that policy remains unchanged afterwards.

## Applicable amounts

Child personal allowances use the legacy-benefit child/young-person definition.
During the historical two-child restriction, actual Child Tax Credit individual
element counts can permit more children even if the resulting tax-credit payment
is zero. Continuing-claim protection requires the initial award/count, the
individual children still in the family, and no subsequent new claim.

The family premium is separate. After its GB or NI abolition date, it requires
pre-abolition HB entitlement with a child/young person, a continuously qualifying
family and no new claim. The old higher lone-parent premium requires continuing
April 1998 statutory protection, not just current lone-parent status.

Disabled-child and enhanced-child premiums require listed disability awards,
specified hospital suspensions, blindness or the prescribed post-death Child
Benefit continuation. A general disability indicator is insufficient. These
premiums are not restricted to the first two child personal allowances. Adult
premiums remain in the existing shared premium variables; the HB child additions
do not change Council Tax Reduction or Income Support.

The main-phase ESA age exception tests the claimant personally. A partner's
main-phase award does not on its own satisfy that exception.

## Childcare

Report qualifying charges on each child using
`housing_benefit_childcare_charges_paid`, with the HB-specific provider category
and excluded education/partner/relative-care facts. Unknown provider status
does not establish qualification. The aggregate adult `childcare_expenses`
input alone does not identify the children or provider and is not substituted
for these facts.

Work treatment covers actual or expected paid work, specified sickness/credit
periods after preceding remunerative work, and statutory paid parental leave
with its relevant end dates. Couples need the corresponding partner work,
incapacity, inpatient or custody facts. Child age ends on the relevant first
Monday in September, with actual dates of birth used where supplied.

The capped qualifying charge can offset net earnings after the pre-additional
earnings disregard, plus actual WTC/CTC income, but not unrelated unearned
income. The separate pre-additional calculation avoids a circular dependency.
HB has its own fixed £175/£300 weekly childcare caps, independent of reforms to
the tax-credit parameters.

## Earnings

The £20 special disregard is not a flat allowance for everyone described as
disabled or a carer. Working-age and pension-age grounds differ. Specified
occupation and carer earnings have their own couple aggregation and top-up
rules. Permitted work requires the actual qualifying benefit/credits, authority
acceptance, work category, weekly hours and earnings; couples share one limit.
The higher limit follows the highest adult minimum-wage rate with the statutory
rounding, not the claimant's age-specific minimum wage.

For savings-credit-only HB, use the Secretary of State's net-income assessment
and the earnings disregard already included in it. Supply
`housing_benefit_pension_credit_net_income_assessment` and
`housing_benefit_pension_credit_earnings_disregard_assessment` together when
those figures are known. Only permitted HB modifications are deducted: the
full PC and HB disregards must not both be subtracted.

The fallback reads the model's Pension Credit income. Its disregard adapter
uses `pension_credit_earnings_disregard` when that separate component is
installed; otherwise it returns zero, matching the deduction actually made
by the existing PC-income formula. PR #2019 owns that upstream correction.
Without it or an actual supplied assessment, the PC estimate retains that
known limitation. HB does not introduce a second PC calculation.

## Capital

Retained capital is a stock, not annual benefit income. Category amounts must
already be included in the capital sources being assessed and be disjoint.
Dates and payment provenance matter: ordinary Carer's Allowance arrears are
not the July 2026 Independent Review reassessment payment.

The implemented categories cover those reassessment payments, qualifying
injury payments/trusts, listed benefit arrears and official-error payments,
specified home/repair funds, business assets and qualifying temporary or
relative-occupied premises. Working-age 26/52-week rules and pension-age
calendar-year rules remain distinct. Authority-accepted longer periods must
be supplied where the provision permits them. These inputs do not represent
every historic compensation/support scheme listed in the capital schedules.

Remove excluded funds from shared household sources before the claimant/partner
allocation proxy. Where actual ownership is known, set
`housing_benefit_owned_household_capital_known` and
`housing_benefit_owned_household_capital` to the combined claimant/partner
interest in the configured household sources, excluding separately counted
LISAs. A known zero replaces the proxy. Remove only those claimants' own
exclusions in this path. Asset-level ownership and valuation records should
determine this amount; an equal household-adult share is only a fallback.

The LISA medical exception requires the account manager to have received
written registered-practitioner evidence of expected life below one year.
Prospective first-home eligibility alone is not unrestricted surrender:
the statutory withdrawal is a restricted conveyancer transaction.

## Non-dependants

Normal home elsewhere and youth-training inputs record the exact statutory
conditions. Income-related ESA under age 25 is exempt only outside the support
and work-related activity groups; a zero cash component is insufficient.
Hospital, custody and military-operation exemptions require current absence.
`housing_benefit_non_dep_linked_inpatient_days` must be prepared from admissions:
sum inpatient days only, link gaps at most 28 days, and restart after longer
gaps. Mental-health hospital detention is not the specified custody category.

Full-time students are exempt during study even when working. Working-age
summer-vacation students are exempt only when not in remunerative work,
unless the claimant-specific pensionable-age exception applies. NI pension-age
student rules retain their age-65 condition. Education enrolment is a fallback
for full-time status; override it for part-time courses.

Pension-age increases use claimant-specific award history. The existing core
entities cannot store a claimant/non-dependant relationship directly, so
`housing_benefit_non_dep_increase_history` accepts sparse, validated JSON
records on each claimant's benefit unit. This is an explicit data interface,
not an existing standard entity or a generic exemption input:

```json
[
  {
    "person_id": "adult_child",
    "previous_weekly_deduction": 20.4,
    "last_effective_date": "2025-04-07",
    "increases": [
      {"date": "2026-08-01", "kind": "circumstances"}
    ]
  }
]
```

Record every pending increase after the current continuous award began or the
last effective change, whichever is later. Use the amount actually still
applied before the pending increases, before rent-share allocation. Account
for ordinary uprating and immediate reductions in that previous amount.
Event kinds are `arrival`, `circumstances` and `uprating`; only the first two
start the postponement. Arrival during an existing award normally has a
previous deduction of zero. An existing resident when a new claim starts
does not establish a deferred arrival.

The first qualifying increase for the same person determines the 26-week
date, rounded forward to this claim's benefit-week start. Later increases do
not restart it. Reductions and exemptions apply immediately. Different
claimants can supply different histories for the same person. Missing history
means no evidenced postponement, not a fabricated recent arrival.

## Data and remaining coverage

These factual inputs default to zero/false or an unknown future date. Existing
datasets are not silently populated with inferred historical awards, payment
provenance, provider qualifications or claimant-specific change records.
Population results will use available data and documented fallbacks until
upstream materialisers supply those fields.

Later pension-age cohort routing, other published rate corrections, general
non-dependant income/couple rules, within-family deductions, award attribution,
and more detailed asset valuation are separate model changes. Do not describe
the model as a complete reconstruction of every HB provision or pre-2015 award.

## Government sources

- [GB working-age HB Regulations](https://www.legislation.gov.uk/uksi/2006/213).
- [GB pension-age HB Regulations](https://www.legislation.gov.uk/uksi/2006/214).
- [NI working-age HB Regulations](https://www.legislation.gov.uk/nisr/2006/405).
- [NI pension-age HB Regulations](https://www.legislation.gov.uk/nisr/2006/406).
- [Pension Credit earnings disregards](https://www.legislation.gov.uk/uksi/2002/1792/schedule/VI).
- [2026 GB carers' reassessment exclusion](https://www.legislation.gov.uk/uksi/2026/681).
- [2026 NI counterpart](https://www.legislation.gov.uk/nisr/2026/146).
- [LISA medical withdrawal exception](https://www.legislation.gov.uk/uksi/1998/1870/schedule/paragraph/4).

The relevant parameters and variables also carry their own source references.
