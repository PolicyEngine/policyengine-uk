# Guardian's Allowance

Guardian's Allowance is a tax-free weekly payment for qualifying children or
young people whose parental circumstances meet the statutory conditions. This
model calculates full-rate cash for UK tax years 2024–2026 from explicit,
source-qualified facts. It does not adjudicate orphan eligibility or infer it
from household relationships.

## Entitlement, exposure and cash

All three variables are annual and attach to a Person:

| Variable | Meaning | Default |
| --- | --- | --- |
| `is_entitled_to_guardians_allowance` | Actual legal entitlement of this individual, independently of cash receipt | `False` |
| `guardians_allowance_full_rate_child_weeks` | Nonnegative full-rate payable child-weeks at the represented tax year's annualised rate | `0` |
| `guardians_allowance` | Cash received by this person, calculated or entered directly | `0` |

Computed cash belongs to an entitled person who is also the cash recipient.
For 2026, a steady one-child 52-week exposure gives £22.95 × 52 = £1,193.40;
two such children give £2,386.80. A 26-week same-rate exposure gives £596.70.
These are annualised references, not a reconstruction of weekly payments
spanning an uprating date.

An ordinary direct cash input overrides calculation for the whole Person array,
including explicit zero. A lawful distinct payee can hold the cash while legal
entitlement remains on another person. Use authoritative direct cash for
prison-adjusted, frozen-abroad, mixed-rate or other exceptional payments. The
model does not subtract an aggregate imprisoned parent's maintenance payment
from a multi-child award. It adds no reported-zero sentinel or sparse mixing
of reported and calculated cells.

## Facts the caller must establish

The entitlement fact asserts a valid claim, Child Benefit entitlement for the
relevant child or qualifying young person, and the applicable parental,
adoption, parental-connection and saved-claim conditions. Child Benefit
entitlement is distinct from its cash payment: a high-income payment opt-out
does not by itself remove Guardian's Allowance entitlement.

These conditions come from [section 77 of the GB Act](https://www.legislation.gov.uk/ukpga/1992/4/section/77),
[section 77 of the Northern Ireland Act](https://www.legislation.gov.uk/ukpga/1992/7/section/77)
and the [Guardian's Allowance (General) Regulations 2003](https://www.legislation.gov.uk/uksi/2003/495).
They include prescribed missing-parent and prison or court-hospital cases,
not just both parents having died. The parental-connection test concerns the
relevant legal parent, not simply the guardian's present country or nationality.

The [2020 amendment](https://www.legislation.gov.uk/uksi/2020/297/regulation/7/made)
changed the domestic prison rule to a sentence of at least two years; the
prescribed overseas route retains its own remaining-sentence rule. The
[2025 amendment](https://www.legislation.gov.uk/uksi/2025/207/regulation/3/made)
removed the unmarried/unestablished-paternity and divorced-parent modifications
for new claims from 7 April 2025, with savings for claims made before that date
and subsequently awarded, including the specified later same-person/same-child
claims. Callers must establish the applicable route rather than infer it from
current relationships. [Claim backdating](https://www.legislation.gov.uk/uksi/2003/492/regulation/6)
and weekly maintenance or living-with conditions are also external facts.

## Verified rates and annual convention

| Tax year | Weekly full rate | Statutory commencement | Source |
| --- | --- | --- | --- |
| 2024 | £21.75 | 8 April 2024 | [SI 2024/247](https://www.legislation.gov.uk/uksi/2024/247/made) |
| 2025 | £22.10 | 7 April 2025 | [SI 2025/292](https://www.legislation.gov.uk/uksi/2025/292/made) |
| 2026 | £22.95 | 6 April 2026 | [SI 2026/232](https://www.legislation.gov.uk/uksi/2026/232/made) |

The parameter keeps these statutory dates. The existing annual tax-year
processor selects the rate in force on 30 April and exposes it at the tax
year's January label. It does not blend weeks at different rates. Positive
computed exposure outside 2024–2026 raises an unsupported-window error; direct
cash can still record an established payment. A historical cash entry alone
makes no claim that historical programme interactions have been validated.

## Tax, benefits and ownership

Guardian's Allowance is [exempt from Income Tax](https://www.legislation.gov.uk/ukpga/2003/1/section/677)
and is not subject to the High Income Child Benefit Charge. It is excluded
from the model's UC, Housing Benefit, Pension Credit, Income Support and
income-based JSA/ESA assessable-income sources. Cash is included once in each
of the independent household-benefit, HBAI-benefit, HBAI-net-income and
government-spending totals.

The cap exemptions follow **legal entitlement**, including nil cash:

- [UC regulation 83(1)(k)](https://www.legislation.gov.uk/uksi/2013/376/regulation/83)
  and [the Northern Ireland equivalent](https://www.legislation.gov.uk/nisr/2016/216/regulation/83)
  read an actual claimant. An excluded partner in a single-person claim or an
  unrelated benefit-unit member does not confer this exemption.
- [HB regulation 75F(1)(i)](https://www.legislation.gov.uk/uksi/2006/213/regulation/75F)
  and [NI regulation 73F(1)(ha)](https://www.legislation.gov.uk/nisr/2006/405/regulation/73F)
  read the claimant, partner or a responsible young person. The existing
  model's qualifying-young-person classification supplies that scope; another
  adult or a non-qualifying young person does not exempt the family.

The annual date switch retains false before 7 November 2016, so its first full
annual true value is 2017 under the April convention. This does not reconstruct
the 2016 part-year HB or UC assessment-period transition, or Northern Ireland's
historical UC rollout. Validated NI UC interactions here are 2024–2026.
Guardian's Allowance is outside the current capped welfare-benefit basket;
this change does not reconstruct the pre-2016 basket.

## Data coverage

Cash must be disjoint from `miscellaneous_income` and any other reported
payment. Producers must remove any embedded duplicate before supplying these
facts; the model makes no guessed deduction from unrelated income. Missing
new inputs default to false/zero, which preserves old records but does not
establish that nobody in a dataset is entitled. This implementation adds no
national entitlement imputation, take-up estimate, data-release migration or
claim-date/residence adjudication.
