# Education Maintenance Allowance

PolicyEngine computes one explicit 2026/27 Education Maintenance Allowance (EMA)
assessment for Wales and Northern Ireland, and the Highland school route in
Scotland. Other Scottish councils, college, home-education and action-plan
routes are unsupported. The weekly financial award is `ema_weekly_award`;
`education_maintenance_allowance` is the sole annual cash output.

## Assessment facts

Supply `ema_assessment_country`, `ema_academic_year` and an actual
`ema_date_of_birth` in YYYYMMDD format. Current fiscal-year age or imputed
education does not establish a cohort. For Wales an actual earlier institution
academic start can be supplied as `ema_academic_year_start_date`; zero uses the
ordinary 1 September anchor. The Highland selector
`ema_scotland_highland_school` is required and defaults false.

Supply the source-defined assessment group income in `ema_assessed_income`
and set `ema_income_is_known` only when established. Verified zero differs
from missing income. Wales and NI normally assess 2024/25; Highland normally
assesses 2025/26. A lawfully accepted reassessment can be represented in a
separate calculation, not by automatically taking the lower of historical and
current household income. The residual/assessed total is supplied; this module
does not reconstruct its tax-base deductions or impute a supporting family.
`ema_other_qualifying_dependants` excludes the applicant and uses each scheme's
own definition, not generic household size.

`ema_financial_category` records a source-bound assessment fact. Wales's
specified exemptions and Highland's current-care/own-qualifying-benefit
exemptions differ. A Scottish care leaver is not automatically in current care;
Wales's care-leaver route requires its statutory history. NI independence,
including Income Support, income-related ESA or Universal Credit, does not
remove its income test. Detailed nationality/residence determination is supplied
through `ema_residency_conditions_met`, not inferred from country alone.

The course inputs identify actual type, provider approval, full-time mode,
weekly learning hours, qualification level, duration and incompatible funding.
Wales applies its full-time 12-hour and academic/vocational 10-week conditions;
approved Preparation for Life and Work is a separate route. NI requires a
full-time school or at least 15 guided college hours. Highland school normally
requires 21 guided hours; a documented `ema_flexible_learning_arrangement` can
waive ordinary hours/mode, not provider/school/scope conditions.

Wales uses the elapsed window from `ema_school_leaving_academic_year`, with
its separate 20th-birthday receipt-history and institution-advice route.
Highland normally funds 3 academic years or 4 for source-defined vulnerable/young
carer categories. NI's 3-year limit is distinct from its 117 positive **or
negative** confirmation limit. Unknown necessary historical counts use -1,
not an invented zero history.

## Actual period cash

Allocate actual lawfully payable weeks of this assessment to the exact requested
model/fiscal year as `ema_payable_weeks`. They must already respect agreement,
authorised absence, progress, holidays, acceptance/backdating, reassessment and
payment timing. No annual 52-week, 42-week or automatic monthly award is assumed.
A prior-year allocation is not a new payment. NI additionally uses
`ema_prior_positive_or_negative_confirmations` before the block; current
negative weeks and positives after exhaustion must already be excluded from
payable weeks. Counts cannot reconstruct their within-block order.

`ema_qualifying_bonus_count` supplies actual institution-qualified NI bonuses
for that cash year, including objectives, signatures and payment-window facts.
January/June alone do not earn a bonus. The model bounds a period's count, but
the caller must not allocate the same earned bonus twice across years.
Fiscal 2026 includes January–March 2027, so the Highland winter cohort is not
excluded merely because its first payment starts 4 January 2027.

Only model cash years 2026 and 2027 are supported for this academic assessment.
Two overlapping academic assessments require separate calculations and
aggregation, or the normal explicit final-cash override. This is not an
automatic monthly, academic-history or fiscal-receipt ledger. Wales's printed
application deadline discrepancy is not silently adjudicated; actual accepted
weeks are supplied facts.

## Income integration and limits

Canonical cash enters household benefit-income accounting, government spending
and its fiscal head once. HBAI net income includes it as an **education grant**;
`hbai_benefits` remains unchanged because state support is a separate category
in [DWP's income definition](https://www.gov.uk/government/statistics/households-below-average-income-for-financial-years-ending-1995-to-2022/households-below-average-income-series-quality-and-methodology-information-report-fye-2022#income-definition).
The weekly assessment is never added as cash. Generic benefit-uprating reforms
retain the normal registry treatment, consistent with other student cash terms.

Existing `adult_ema`, `child_ema`, `student_payments` and the Welsh childcare
consumer are unchanged. New explicit cash must be disjoint from legacy EMA,
`education_grants`, miscellaneous income and transfer residuals. No producer
mapping, automatic clearing/reclassification or population imputation is claimed.
The detailed residency decision, administrative acceptance and actual payment
schedule remain factual inputs; they are not a blanket whole-EMA eligibility
flag.

## Sources

- [Wales EMA Scheme 2026/2027](https://www.gov.wales/sites/default/files/publications/2026-04/the-education-maintenance-allowance-wales-scheme-2026-2027.pdf).
- [Highland school EMA guidance, current 2026/27 content](https://www.highland.gov.uk/downloads/file/962/ema-guidance-notes-2025-26). The URL filename retains an older year; the inspected document heading is 2026/27.
- [NI application notes 2026/27](https://www.nidirect.gov.uk/sites/default/files/2026-06/ema-ni-application-notes-2627-e-o-PDF_0.pdf) and [current NI EMA rules](https://www.nidirect.gov.uk/articles/education-maintenance-allowance-explained). NI's published birthday window is retained literally, not advanced to another calendar.
