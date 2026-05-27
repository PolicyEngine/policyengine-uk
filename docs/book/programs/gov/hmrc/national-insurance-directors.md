# Company-director NI (annual cumulative basis)

```{note}
PolicyEngine UK applies a **single annual NI calculation** at the
person level. For most users this matches what HMRC charges company
directors at year end. This page explains the relationship between the
director-specific "annual cumulative" basis HMRC uses and PolicyEngine's
current modelling, and describes what would need to change to expose a
dedicated director-specific path. Tracked under
[#721](https://github.com/PolicyEngine/policyengine-uk/issues/721).
```

## What HMRC's annual cumulative basis is

Class 1 NI is normally charged on each *earnings period* (typically a
week or a month) — the employer applies the weekly/monthly thresholds
to that pay period's earnings in isolation. Directors are a special
case because their pay is often irregular: a director might take £0 in
salary for eleven months and then a £200,000 bonus in December. Under
period-by-period NI rules, that pattern would generate massive NI in
the bonus month and almost none in the other eleven, even though the
director's annual income is no different from someone earning a steady
salary.

To prevent this avoidance route, [SSCBA 1992 s.122 and the *Social
Security (Contributions) Regulations 2001*][nim12000] require directors
to use an **annual earnings period** by default:

1. The director's NI is computed on a **cumulative** year-to-date
   basis.
2. The annual thresholds (Primary Threshold, Upper Earnings Limit,
   Secondary Threshold) are applied to YTD earnings, not to each pay
   period's earnings in isolation.
3. NI is charged once YTD earnings cross each threshold, and never
   refunded if earnings drop later in the year.

There is also an "**alternative**" method, which approximates the
annual basis with monthly cumulative figures, used for in-year
operational simplicity; the final year-end reconciliation still uses
the annual basis.

## How PolicyEngine currently handles this

PolicyEngine UK already computes NI **annually** for every person:

- The Class 1 employee primary and additional formulas in
  [`variables/gov/hmrc/national_insurance/class_1/`](https://github.com/PolicyEngine/policyengine-uk/tree/main/policyengine_uk/variables/gov/hmrc/national_insurance/class_1)
  read weekly thresholds from `gov.hmrc.national_insurance.class_1.thresholds`
  and convert them to monthly (`× WEEKS_IN_YEAR / MONTHS_IN_YEAR`) before
  applying the rate.
- Because the input `employment_income` is annual and is implicitly
  spread evenly across months, the **annual NI** the model produces is
  identical to the annual cumulative figure a director would owe — for
  someone earning the same total over the year, the two methods give
  the same answer.

That's why microsimulation results don't depend on director status.

## Where the current model could diverge from HMRC's director rules

Three situations could in principle produce a different answer:

1. **Irregular within-year pay**. If a household-calculator user inputs
   an annual `employment_income` of, say, £80,000 but means it as a
   single lump-sum payment, PolicyEngine still spreads it across twelve
   months — matching the annual cumulative outcome. There is no
   surface here for the user to express the pay timing.
2. **Mid-year start or end** of directorship within a tax year. The
   pro-rating rules for directors who start or cease being a director
   part-way through a year are slightly different from regular
   employees — PolicyEngine assumes a full-year period everywhere.
3. **Multiple employments**. A director with two separate company
   roles can sometimes have NI calculated separately per employment.
   PolicyEngine has a single `employment_income` per person and so
   collapses this case.

In practice (1) and (2) only matter for the household-calculator
front-end, not microsimulation. (3) is a wider modelling gap that
applies beyond directors.

## What a dedicated director path would look like

A future PR addressing this fully would add:

- A new boolean input `is_company_director` (Person, year).
- A documentation flag on `ni_class_1_employee_primary` / `_additional`
  noting that for directors with `is_company_director == true` the
  formula returns the same annual figure as the regular path (rather
  than period-by-period NI), confirming the equivalence.
- Optional follow-up: a `company_director_pay_timing` enum so that
  household-calculator users who model a director's actual pay pattern
  can document their intent, but the resulting NI stays on the annual
  basis.

For now PolicyEngine is **functionally correct** for any user whose
input is an annual income — which is the expected interface — and
no code changes are needed in the short term.

## References

- HMRC, [NIM12000 — Class 1 NICs: company directors](https://www.gov.uk/hmrc-internal-manuals/national-insurance-manual/nim12000) — primary internal guidance covering the annual cumulative basis.
- HMRC, [CA44 — National Insurance for company directors](https://www.gov.uk/government/publications/ca44-national-insurance-for-company-directors) — the operational employer guide.
- [The Social Security (Contributions) Regulations 2001 (SI 2001/1004) reg. 8](https://www.legislation.gov.uk/uksi/2001/1004/regulation/8) — the regulation that imposes the annual earnings period.
- [Social Security Contributions and Benefits Act 1992 s. 8](https://www.legislation.gov.uk/ukpga/1992/4/section/8) — primary statute for Class 1 employee NI.

[nim12000]: https://www.gov.uk/hmrc-internal-manuals/national-insurance-manual/nim12000
