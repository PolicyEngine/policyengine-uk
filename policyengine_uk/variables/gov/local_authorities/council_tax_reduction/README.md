# Council Tax Reduction

This implementation currently simulates:

- The statutory CTR scheme for pensioner households in England.
- The national CTR scheme in Wales.
- The national CTR scheme in Scotland.
- Working-age local schemes for Adur, Barking and Dagenham, Barnet, Basingstoke and Deane, Bolton, Breckland, Brent, Bromley, Bristol, Broadland, Bury, Camden, Chelmsford, Cheshire West and Chester, Chesterfield, Colchester, Crawley, Croydon, Cumberland, Darlington, Dudley, Ealing, East Cambridgeshire, East Hertfordshire, East Suffolk, Enfield, Fenland, Gateshead, Greenwich, Haringey, Harrow, Havering, Herefordshire, Hackney, Hammersmith and Fulham, Hillingdon, Hounslow, Islington, King's Lynn and West Norfolk, Kingston upon Hull, Kingston upon Thames, Lambeth, Lancaster, Lewisham, Merton, Newham, North Norfolk, North Yorkshire, Norwich, Oldham, Oxford, Redbridge, Sefton, Somerset, South Norfolk, Southend-on-Sea, Southwark, St Albans, Stevenage, Stockport, Stroud, Tameside, Thurrock, Wakefield, Warrington, West Suffolk, Westmorland and Furness, Westminster, and Worthing.

For unsupported English working-age authorities, the model continues to use reported `council_tax_benefit` values in dataset mode rather than inventing scheme rules.

The top-level `simulated_council_tax_reduction_benunit` variable aggregates implemented jurisdiction-specific CTR variables. Working-age local authority rules live under `policyengine_uk/variables/gov/local_authorities/<authority>/council_tax_reduction/`, matching the parameter tree and keeping each council's policy in its own jurisdiction folder.

The current implementation does not yet model:

- Additional authority-specific income-banded and discount-grid English schemes not yet implemented in this PR.
- Alternative maximum / second adult rebate cases.
- Universal Credit-specific CTR adjustments beyond the implemented local earnings-band paths and standard income treatment used here.
- National/statutory non-dependant couple aggregation beyond the local working-age scheme helper.
- Non-dependant deduction apportionment across multiple jointly liable Council Tax payers.

For batched implementation status and next candidates, see `scheme_work_queue.md`. For a drop-in autonomous handoff prompt, see `agent_handoff.md`.

There is also a requests-based entitledto comparison harness at `scripts/entitledto_ctr_compare.py`. It replays the calculator from a saved browser storage state and currently covers three single-adult claimant variants:

- `single_jsa`
- `single_jsa_pip_standard`
- `single_pension_credit`

It does not yet cover couples, children, or other-adult/non-dependant household shapes. entitledto's session handling is also inconsistent enough that rerunning with a fresh storage state is sometimes necessary, and fresh anonymous calculator starts can hit entitledto's day limit. A typical single-scenario run is:

`uv run --with requests --with beautifulsoup4 python scripts/entitledto_ctr_compare.py output/playwright/entitledto-live-state.json --postcode SG13 8EQ --band D --council-tax 1800 --scenario single_jsa`

There is also a requests-based Turn2us probe at `scripts/turn2us_ctr_compare.py`. It currently replays the public Turn2us calculator for a single working-age JSA claimant and records the benefits that appear on the final results page for the supplied postcode. A typical multi-authority run is:

`uv run --with requests python scripts/turn2us_ctr_compare.py "SG13 8EQ" "WA1 1UH" "DY1 1HF" "GL5 4UB"`

## Validation notes

Spot checks against public calculators and scheme sources currently show:

- Stroud (`GL5 4UB`, area `Stroud`, band `D`, single working-age owner-occupier, no children, no savings, income-based JSA): entitledto returns full Council Tax Support on an annual liability of `GBP 1,866.47`. PolicyEngine UK returns `council_tax_reduction = GBP 1,866.47`.
- Dudley (`DY1 1HF`, band `C`, single working-age owner-occupier, no children, no savings, income-based JSA): entitledto returns `GBP 15.64` per week of Council Tax Support, leaving `GBP 10.43` per week to pay. PolicyEngine UK returns `council_tax_reduction = GBP 543.62` per year and `council_tax_less_benefit = GBP 815.43` per year, matching Dudley Council's published 2025/26 scheme text and scheme PDF rather than the entitledto output.
- East Hertfordshire (`SG13 8EQ`, band `D`, single working-age owner-occupier, no children, no savings, income-based JSA, annual liability `GBP 1,800`): entitledto returns `GBP 31.59` per week of Council Tax Support and `GBP 2.93` per week left to pay. PolicyEngine UK applies the same `91.5%` maximum award rule, giving `council_tax_reduction = GBP 1,647` and `council_tax_less_benefit = GBP 153` per year.
- East Hertfordshire (`SG13 8EQ`, band `D`, single working-age lone parent, one child aged `5`, no savings, income-based JSA, annual liability `GBP 1,800`): a headed browser run through entitledto returns total benefits of `GBP 367.64` per week, made up of `GBP 310.00` income-based Jobseeker's Allowance, `GBP 31.59` Council Tax Support, and `GBP 26.05` Child Benefit. The calculator shows a weekly Council Tax bill of `GBP 34.52` reduced to `GBP 2.93`. PolicyEngine UK now keeps this household on the East Herts class D maximum award, returning `council_tax_reduction = GBP 1,647` and `council_tax_less_benefit = GBP 153`.
- East Hertfordshire (`SG13 8EQ`, band `D`, two working-age adults, no children, no savings, income-based JSA, annual liability `GBP 1,800`): a headed browser run through entitledto returns total benefits of `GBP 237.89` per week, made up of `GBP 206.30` income-based Jobseeker's Allowance and `GBP 31.59` Council Tax Support. The calculator again shows a weekly Council Tax bill of `GBP 34.52` reduced to `GBP 2.93`. PolicyEngine UK returns the same annual CTR position, `council_tax_reduction = GBP 1,647` and `council_tax_less_benefit = GBP 153`. Because this check reused an existing entitledto calculation ID to get around the anonymous daily cap, the Council Tax page initially carried forward a stale `25%` single-adult discount and had to be corrected back to `none` before the result was trusted.
- East Cambridgeshire (working-age, band `D`, annual liability `GBP 1,800`, no children, no savings): the council's 2025/26 scheme says maximum Council Tax Reduction is `91.5%` of eligible Council Tax after discounts and non-dependant deductions, with the standard `2 6/7%` daily excess-income percentage and the ARP flat working-age non-dependant deduction. PolicyEngine UK returns `council_tax_reduction = GBP 1,647` and `council_tax_less_benefit = GBP 153` before non-dependant deductions.
- East Suffolk (working-age, band `D`, annual liability `GBP 1,800`, no children, no savings): the council's 2025/26 scheme says maximum Council Tax Reduction is `91.5%` of eligible Council Tax after discounts and non-dependant deductions, with the `2 6/7%` daily excess-income percentage, equivalent to a `20%` weekly taper. Anglia Revenues Partnership says working-age CTR applicants need less than `GBP 10,000` in capital and publishes a flat `GBP 8.34` working-age non-dependant deduction for 2026/27. PolicyEngine UK returns `council_tax_reduction = GBP 1,647` and `council_tax_less_benefit = GBP 153` before non-dependant deductions.
- Breckland (working-age, band `D`, annual liability `GBP 1,800`, no children, no savings): the council's 2025/26 scheme says maximum Council Tax Reduction is `91.5%` of eligible Council Tax after discounts and non-dependant deductions, with the standard `2 6/7%` daily excess-income percentage and the ARP flat working-age non-dependant deduction. PolicyEngine UK returns `council_tax_reduction = GBP 1,647` and `council_tax_less_benefit = GBP 153` before non-dependant deductions.
- Brent (working-age, band `D`, annual liability `GBP 1,800`, no children, savings below `GBP 6,000`): the council's current Council Tax Support page uses weekly claimant-and-partner earnings bands with a `65%` maximum ordinary award, excludes DWP and HMRC benefits from the band income, and deducts `GBP 8` or `GBP 20` per week for each non-dependant depending on work status. PolicyEngine UK returns `council_tax_reduction = GBP 1,170` for a no-earnings claimant, `GBP 540` at `GBP 120` weekly earnings, and `GBP 130` after a `GBP 20` weekly working non-dependant deduction.
- Bromley (working-age, band `D`, annual liability `GBP 2,140.04`, no children, no savings): the council's 2026/27 papers continue the existing working-age scheme with `50%` maximum support, a Band `D` cap, a `20%` taper, tariff income above `GBP 6,000`, and a `GBP 16,000` capital limit. PolicyEngine UK returns `council_tax_reduction = GBP 1,070.02` for a no-income claimant, the same award on a Band `H` liability of `GBP 4,280.08`, and `GBP 539.62` after a `GBP 10.20` weekly non-dependant deduction.
- Bristol (working-age, band `D`, annual liability `GBP 2,713.68`, no children, no savings): the council's 2026/27 scheme gives full support where income does not exceed the living allowance, applies a `20%` taper, has a `GBP 16,000` capital limit, tariff income above `GBP 6,000`, a UC assessed-income/capital branch, and non-dependant deductions keyed to single non-dependant earnings or couple gross income. PolicyEngine UK returns `council_tax_reduction = GBP 2,713.68` for a no-excess-income claimant and `GBP 2,162.48` after a `GBP 10.60` weekly non-dependant deduction. Source-listed non-dependant exemptions not otherwise represented in PolicyEngine UK can be supplied with Bristol-specific source-exemption inputs.
- Croydon (working-age, band `C`, annual liability `GBP 2,311.03`, no children, no savings): the council's live 2026 pages use weekly household-income bands, with `75%` ordinary support in the lowest band, `80%` for lone parents with a child under 5, `100%` for disabled non-working claimants, a Band `D` cap except for disabled non-working households, and a strict `GBP 8,000` ordinary capital cutoff. PolicyEngine UK returns `council_tax_reduction = GBP 1,733.27` for an ordinary no-income Band `C` claimant, `GBP 1,949.93` for an ordinary Band `E` claimant after the Band `D` cap, and full support on Band `E` for a disabled non-working claimant. Croydon's 2026/27 decision papers say the scheme continues unchanged, but the detailed booklet linked from the live page is older; the implementation follows the current live table where the live examples page is inconsistent with that table.
- Cumberland (working-age, band `D`, annual liability `GBP 2,444.72`, no children, no savings): the council's 2026/27 scheme gives full support where income does not exceed the applicable amount, applies a `20%` taper, has a `GBP 16,000` capital limit, tariff income above `GBP 6,000` by complete `GBP 250` blocks, a UC assessed-income/capital branch, and remunerative-work non-dependant deductions using a 16-hour threshold. PolicyEngine UK returns `council_tax_reduction = GBP 2,444.72` for a no-excess-income claimant, `GBP 1,893.52` after a `GBP 10.60` weekly remunerative-work non-dependant deduction, and `GBP 2,174.32` when the same earnings are below the 16-hour remunerative-work threshold. Cumberland's Class F second-adult branch falls under the current alternative maximum / second adult rebate limitation.
- Herefordshire (working-age/local scheme, band `D`, annual liability `GBP 2,500`, no children, no savings): the council's 2026/27 report approves the existing scheme parameters, which give full support where income does not exceed the applicable amount, apply a `20%` taper, use a strict `GBP 6,000` working-age capital limit with no tariff income, use UC-assessed income/capital for UC cases, and apply remunerative-work non-dependant deductions using a 16-hour threshold. Pension-age applicants remain in the local scheme where the applicant or partner is on UC or a relevant income-based benefit. PolicyEngine UK returns `council_tax_reduction = GBP 2,500` for a no-excess-income claimant, `GBP 1,977.40` after a `GBP 10.05` weekly non-dependant deduction, `GBP 2,245.20` when the same earnings are below the 16-hour remunerative-work threshold, and `GBP 2,500` for a pension-age UC claimant without double-counting the national pensioner CTR path.
- Westmorland and Furness (working-age/local scheme, band `D`, annual liability `GBP 2,500`, no children, no savings): the council's 2026/27 scheme gives full support where income does not exceed the applicable amount, applies a `20%` taper, has a `GBP 16,000` capital limit with source-disregarded capital for income-based benefit cases, tariff income above `GBP 6,000` including any part `GBP 250` block, a UC assessed-income/capital branch, and remunerative-work non-dependant deductions using a 16-hour threshold. Pension-age applicants remain in the local scheme where the applicant or partner is on UC or a relevant income-based benefit, and UC non-dependant couples are not collapsed to one deduction. PolicyEngine UK returns `council_tax_reduction = GBP 2,500` for a no-excess-income claimant, `GBP 2,489.60` when savings are `GBP 6,000.01`, and `GBP 1,948.80` after a `GBP 10.60` weekly non-dependant deduction. Westmorland and Furness's alternative maximum / second adult branch falls under the current second adult rebate limitation.
- Kingston upon Hull (working-age/local scheme, band `D`, annual liability `GBP 2,500`, no children, no savings): the council's 2026/27 discount report says no CTR change, so this implementation pairs that report with the carried-forward 2025/26 formal scheme. The working-age scheme covers up to `80%` of liability after non-dependant deductions, applies a `20%` taper, has a `GBP 6,000` capital limit with source-disregarded capital for income-based benefit cases and no working-age tariff income, uses UC assessed income/capital for UC cases, and applies remunerative-work non-dependant deductions using a 16-hour threshold with a UC gross-earnings / minimum-wage fallback. Pension-age applicants remain in the local scheme where the applicant or partner is on UC or a relevant income-based benefit, except where a source-specific relevant-period flag preserves pensioner status. PolicyEngine UK returns `council_tax_reduction = GBP 2,000` for a no-excess-income claimant, `GBP 1,792` with `GBP 1,040` excess income, and `GBP 1,575.68` after a `GBP 10.20` weekly non-dependant deduction.
- North Yorkshire (working-age/local scheme, band `D`, annual liability `GBP 2,500`, no children, no savings): the council's 2026/27 formal scheme uses weekly income bands with `100%`, `75%`, `50%`, `25%`, and zero support levels by household type, excludes ordinary applicants with capital of `GBP 6,000` or above, disregards up to `GBP 16,000` of capital for income-based benefit cases, disregards Housing Benefit, and uses UC-assessed income/capital with a proportional UC housing-element disregard for UC awards. Pension-age applicants remain in the local scheme where the applicant or partner is on UC or a relevant income-based benefit, except where a source-specific relevant-period flag preserves pensioner status. PolicyEngine UK returns `council_tax_reduction = GBP 2,500` for a no-income single claimant, `GBP 1,875` at `GBP 180` weekly income, and `GBP 625` at the formal two-or-more-child family `GBP 441.01` weekly boundary. The scheme has no local working-age non-dependant deduction table in the formal discount schedule.
- Somerset (working-age/local scheme, band `D`, annual liability `GBP 1,800`, no children, no savings): the council's 2026/27 adopted scheme uses weekly claimant-and-partner income bands with `100%`, `50%`, `25%`, `10%`, and zero support levels by household type, caps eligible liability at Band `D`, disregards `GBP 25` weekly earnings and `GBP 30` weekly income for qualifying disabled households, excludes ordinary applicants with capital above `GBP 6,000`, disregards capital up to `GBP 16,000` for Income Support, income-based JSA, or income-related ESA cases, disregards Housing Benefit, Carer's Allowance, child maintenance, Child Benefit, war pensions, and the Universal Credit housing element, and reduces final awards by `GBP 10` per week for each non-dependant or non-dependant couple. Pension-age applicants remain in the local scheme where the applicant or partner is on UC or a relevant income-based benefit, except where a source-specific relevant-period flag preserves pensioner status. PolicyEngine UK returns `council_tax_reduction = GBP 1,800` for a no-income single claimant, `GBP 450` at `GBP 180` weekly income, and `GBP 730` for that Band 3 case on a `GBP 5,000` liability after one non-dependant-couple deduction.
- Fenland (working-age, band `D`, annual liability `GBP 1,800`, no children, no savings): the council's 2025/26 scheme says maximum Council Tax Reduction is `100%` of eligible Council Tax after discounts and non-dependant deductions, with the standard `2 6/7%` daily excess-income percentage and the ARP flat working-age non-dependant deduction. PolicyEngine UK returns `council_tax_reduction = GBP 1,800` and `council_tax_less_benefit = GBP 0` before non-dependant deductions.
- West Suffolk (working-age, band `D`, annual liability `GBP 1,800`, no children, no savings): the council's 2025/26 scheme says maximum Council Tax Reduction is `100%` for the period from `1 April 2023` through `31 March 2026`, then `91.5%` after `31 March 2026`, with the standard `2 6/7%` daily excess-income percentage and the ARP flat working-age non-dependant deduction. PolicyEngine UK returns `GBP 1,800` in 2025 and `GBP 1,647` in 2026 before non-dependant deductions.
- Broadland (working-age, band `D`, annual liability `GBP 1,800`, no children, no savings): the council's 2025/26 scheme says working-age applicants who are not receiving a war pension can receive up to `87%` of eligible Council Tax, with a `20%` taper, a `GBP 16,000` capital limit, and a flat `GBP 7` weekly working-age non-dependant deduction. The council's 2026/27 papers say the existing scheme continues with no changes. PolicyEngine UK returns `council_tax_reduction = GBP 1,566` and `council_tax_less_benefit = GBP 234` before non-dependant deductions.
- South Norfolk (working-age, band `D`, annual liability `GBP 1,800`, no children, no savings): the council's 2025/26 scheme says working-age applicants who are not receiving a war pension can receive up to `87%` of eligible Council Tax, with a `20%` taper, a `GBP 16,000` capital limit, and a flat `GBP 7` weekly working-age non-dependant deduction. The council's 2026/27 papers say the existing scheme continues with no changes. PolicyEngine UK returns `council_tax_reduction = GBP 1,566` and `council_tax_less_benefit = GBP 234` before non-dependant deductions.
- Southend-on-Sea (working-age/local scheme, band `D`, annual liability `GBP 1,800`, no children, no savings): the council's 2026/27 formal scheme uses weekly applicant-and-partner income bands with `75%`, `50%`, `25%`, and zero support levels by household type, applies a `GBP 20` weekly earnings disregard, excludes applicants with capital of `GBP 6,000` or above, uses UC-assessed income/capital for UC cases, and disregards source-listed Universal Credit elements. PolicyEngine UK returns `council_tax_reduction = GBP 1,350` for a no-income single claimant, `GBP 900` at `GBP 130` weekly income, and `GBP 450` for a two-child family at `GBP 410` weekly income. The formal scheme does not expose a working-age non-dependant deduction table.
- Lancaster (working-age, band `D`, annual liability `GBP 1,800`, no children, no savings): the council's 2025/26 scheme says maximum Council Tax Reduction is `100%` of eligible Council Tax after discounts and non-dependant deductions, with the `2 6/7%` daily excess-income percentage, equivalent to a `20%` weekly taper, and a `GBP 16,000` capital limit. PolicyEngine UK returns `council_tax_reduction = GBP 1,800` and `council_tax_less_benefit = GBP 0` before non-dependant deductions.
- Oldham (working-age, band `D`, annual liability `GBP 1,800`, no children, no savings): the council's 2025/26 scheme caps working-age eligible liability at Band A and applies a `15%` reduction in award, with the `2 6/7%` daily excess-income percentage and a `GBP 16,000` capital limit. PolicyEngine UK returns `council_tax_reduction = GBP 1,020` and `council_tax_less_benefit = GBP 780` before non-dependant deductions.
- Bolton (working-age, band `D`, annual liability `GBP 1,800`, no children, no savings): the council's 2026/27 scheme says maximum Council Tax Support is `82.5%` of eligible Council Tax after discounts and non-dependant deductions, with the `2 6/7%` daily excess-income percentage and a `GBP 16,000` capital limit. PolicyEngine UK returns `council_tax_reduction = GBP 1,485` and `council_tax_less_benefit = GBP 315` before non-dependant deductions.
- Basingstoke and Deane (working-age, band `D`, annual liability `GBP 1,800`, no children, no savings): the council's 2026/27 scheme says maximum Council Tax Support is `100%` of eligible Council Tax after discounts and non-dependant deductions, with the `2 6/7%` daily excess-income percentage and a `GBP 16,000` capital limit. PolicyEngine UK returns `council_tax_reduction = GBP 1,800` and `council_tax_less_benefit = GBP 0` before non-dependant deductions.
- Crawley (working-age, band `D`, annual liability `GBP 1,800`, no children, savings below `GBP 9,000`): the council's 2025/26 scheme says maximum Council Tax Reduction is `100%` of eligible Council Tax after discounts and non-dependant deductions, with a `GBP 9,000` capital limit and a `20%` weekly taper. PolicyEngine UK returns `council_tax_reduction = GBP 1,800` and `council_tax_less_benefit = GBP 0` before non-dependant deductions, and returns no support above the capital limit.
- St Albans (working-age, band `D`, annual liability `GBP 1,800`, no children, no savings): the council's 2025/26 scheme says non-Universal Credit claimants can receive `100%` of eligible Council Tax with the standard `20%` weekly taper and a `GBP 16,000` capital limit. For Universal Credit claimants, St Albans uses an earnings-band contribution table. PolicyEngine UK returns `GBP 1,800` for the non-UC no-income case, and `GBP 660` where monthly earnings of `GBP 1,000` imply a `GBP 95` monthly contribution in 2025. The scheme excludes Universal Credit awards from its one-deduction non-dependant couple rule; PolicyEngine UK counts both members in that case.
- Adur (working-age, band `D`, annual liability `GBP 1,800`, no children, no savings): the council's 2026/27 scheme says maximum Council Tax Support is `100%` of eligible Council Tax after discounts and non-dependant deductions, with the `2 6/7%` daily excess-income percentage and a `GBP 16,000` capital limit. PolicyEngine UK returns `council_tax_reduction = GBP 1,800` and `council_tax_less_benefit = GBP 0` before non-dependant deductions. The scheme excludes Universal Credit awards from its one-deduction non-dependant couple rule; PolicyEngine UK counts both members in that case.
- Worthing (working-age, band `D`, annual liability `GBP 1,800`, no children, no savings): the council's 2026/27 scheme says maximum Council Tax Support is `100%` of eligible Council Tax after discounts and non-dependant deductions, with the `2 6/7%` daily excess-income percentage and a `GBP 16,000` capital limit. PolicyEngine UK returns `council_tax_reduction = GBP 1,800` and `council_tax_less_benefit = GBP 0` before non-dependant deductions. The scheme excludes Universal Credit awards from its one-deduction non-dependant couple rule; PolicyEngine UK counts both members in that case.
- Sefton (working-age, band `D`, annual liability `GBP 1,800`, no children, no savings): the council's 2026/27 scheme says maximum Council Tax Reduction is `84%` of eligible Council Tax after discounts and non-dependant deductions, with the `2 6/7%` daily excess-income percentage, a `GBP 6,000` capital limit, and a working-age non-dependant deduction table of `GBP 2` or `GBP 5` per week when the non-dependant is in remunerative work. PolicyEngine UK returns `council_tax_reduction = GBP 1,512` and `council_tax_less_benefit = GBP 288` before non-dependant deductions. The scheme excludes Universal Credit awards from its one-deduction non-dependant couple rule; PolicyEngine UK counts both members in that case.
- Oxford (working-age, band `D`, annual liability `GBP 1,800`, no children, no savings): the council's 2026/27 scheme uses weekly income bands of `100%`, `75%`, `50%`, `25%`, and `0%`, with a `GBP 16,000` capital limit and a working-age non-dependant deduction table from `GBP 5.20` to `GBP 15.95` per week. PolicyEngine UK returns `council_tax_reduction = GBP 1,800` and `council_tax_less_benefit = GBP 0` in the lowest income band, and `GBP 1,350` where relevant weekly income is `GBP 500`.
- Redbridge (working-age, band `D`, annual liability `GBP 2,294.58`, no savings): the adopted 2026/27 full scheme uses categorical support rates of `73%`, `60%`, `50%`, `46%`, and `36%`, has no taper or Band D cap, excludes capital over `GBP 16,000`, applies a `GBP 10` weekly minimum award, and deducts `GBP 21.18` or `GBP 10.59` per week for non-dependants with a Universal Credit exception to the one-deduction couple rule. The council's shorter summary PDF says `61%` and `51%` for the no-work classes; PolicyEngine UK follows the adopted full scheme. PolicyEngine UK returns `council_tax_reduction = GBP 1,675.04` for a disability-class claimant, `GBP 1,223.78` for a no-earnings UC claimant with a child on a Band `C` liability, and `GBP 938.23` for a claimant with a child and `GBP 312.99` weekly net earnings; the strict `GBP 313` threshold returns no award.
- Kingston upon Thames (working-age, band `D`, annual liability `GBP 1,800`, no children, no savings): the council's 2026/27 scheme says maximum Council Tax Reduction is `100%` of eligible Council Tax after discounts and non-dependant deductions, with a `20%` taper, a `GBP 16,000` capital limit, tariff income above `GBP 6,000`, and a working-age non-dependant deduction table from `GBP 5.64` to `GBP 17.31` per week. PolicyEngine UK returns `council_tax_reduction = GBP 1,800` and `council_tax_less_benefit = GBP 0` before non-dependant deductions.
- Newham (working-age, band `D`, annual liability `GBP 1,800`, no children, no savings): the council's 2026 scheme says working-age maximum Council Tax Reduction is `70%` of eligible Council Tax after discounts and non-dependant deductions, with a `25%` taper, a `GBP 6,000` capital limit, and a working-age non-dependant deduction table from `GBP 7.54` to `GBP 22.61` per week. PolicyEngine UK returns `council_tax_reduction = GBP 1,260` and `council_tax_less_benefit = GBP 540` before non-dependant deductions.
- Westminster (working-age, band `D`, annual liability `GBP 1,800`, no children, no savings): the council's 2026/27 scheme says maximum Council Tax Support is `100%` of eligible Council Tax after discounts and non-dependant deductions, with a `20%` taper and a working-age non-dependant deduction table from `GBP 5.20` to `GBP 15.95` per week. The council's income and savings guide sets the Council Tax Support capital limit at `GBP 16,000` and tariff income above `GBP 6,000`. PolicyEngine UK returns `council_tax_reduction = GBP 1,800` and `council_tax_less_benefit = GBP 0` before non-dependant deductions.
- Greenwich (working-age, band `D`, annual liability `GBP 1,800`, no children, no savings): the council's current Local Council Tax Support page says working-age support covers up to `80%` of the bill, with a `25%` income taper, a `GBP 16,000` capital limit, tariff income above `GBP 6,000`, and a flat `GBP 10` weekly non-dependant deduction. PolicyEngine UK returns `council_tax_reduction = GBP 1,440` and `council_tax_less_benefit = GBP 360` before non-dependant deductions.
- Hackney (working-age, band `D`, annual liability `GBP 1,800`, no children, no savings): the council's current guidance says working-age Council Tax Reduction is limited to `90%` of the bill, with a `20%` taper, a `GBP 16,000` capital limit, tariff income above `GBP 6,000`, and a non-dependant deduction table from `GBP 5.20` to `GBP 15.95` per week. PolicyEngine UK returns `council_tax_reduction = GBP 1,620` and `council_tax_less_benefit = GBP 180` before non-dependant deductions.
- Hammersmith and Fulham (working-age, band `D`, annual liability `GBP 1,800`, no children, no savings): the council's 2026/27 report continues its 2025/26 default-style scheme with annual uprating, providing up to `100%` support for low-income residents. PolicyEngine UK models the legacy `20%` taper, `GBP 16,000` capital limit, tariff income above `GBP 6,000`, and the uprated non-dependant deduction table from `GBP 5.20` to `GBP 15.95`; it returns `council_tax_reduction = GBP 1,800` and `council_tax_less_benefit = GBP 0` before non-dependant deductions.
- Stockport (working-age, band `D`, annual liability `GBP 1,800`, no children, no savings): the council's 2026/27 scheme caps most working-age support at the equivalent Band `A` liability, has an `GBP 8,000` capital limit, and applies `GBP 5` or `GBP 10` weekly non-dependant deductions by gross income. PolicyEngine UK returns `council_tax_reduction = GBP 1,200` and `council_tax_less_benefit = GBP 600` before non-dependant deductions.
- Wakefield (working-age, band `D`, annual liability `GBP 1,800`, no children, no savings): the council's 2026/27 scheme disregards DWP income, uses assessed weekly non-DWP income bands with maximum support of `70%`, has a `GBP 6,000` capital limit, and applies a flat `GBP 7.50` weekly non-dependant deduction. PolicyEngine UK returns `council_tax_reduction = GBP 1,260` and `council_tax_less_benefit = GBP 540` before non-dependant deductions.
- Tameside (working-age, band `D`, annual liability `GBP 1,800`, no children, no savings): the council's 2026/27 scheme caps eligible liability at Band `A`, uses weekly net-income bands of `75%`, `50%`, `25%`, and `0%`, has a `GBP 6,000` capital cutoff, and has no non-dependant deductions. PolicyEngine UK returns `council_tax_reduction = GBP 900` and `council_tax_less_benefit = GBP 900`.
- Bury (working-age, band `D`, annual liability `GBP 1,800`, no children, no savings): the council's 2026/27 scheme caps eligible liability at Band `B` unless a protected-group exemption applies, uses monthly net earned-income bands from `80%` to `0%`, ignores other income, has a `GBP 8,000` capital limit, and applies a flat `GBP 40` monthly non-dependant deduction. PolicyEngine UK returns `council_tax_reduction = GBP 1,120` and `council_tax_less_benefit = GBP 680` before non-dependant deductions.
- Lambeth (working-age, band `D`, annual liability `GBP 1,800`, no children, no savings): the council's current 2026 page says the scheme changed on `1 April 2026`, uses weekly net-earnings bands from `73.5%` to `0%`, has a `GBP 10,000` savings limit for working-age residents, ignores welfare benefits and similar income, and applies `GBP 10` or `GBP 16` weekly non-dependant deductions. PolicyEngine UK returns `council_tax_reduction = GBP 1,323` and `council_tax_less_benefit = GBP 477` before non-dependant deductions.
- Camden (working-age, band `D`, annual liability `GBP 1,800`, no children, no savings): the council's current page says working-age support uses weekly gross-earnings bands after eligible childcare costs, gives full support below `GBP 118.40` weekly earnings, has a `GBP 16,000` savings and assets limit, and applies a `30%` liability deduction for each qualifying non-dependant while treating couples as one. PolicyEngine UK uses household liquid savings as the available capital proxy, and returns `council_tax_reduction = GBP 1,800` and `council_tax_less_benefit = GBP 0` before non-dependant deductions.
- Islington (working-age, band `D`, annual liability `GBP 1,800`, no children, no savings): the council's current page says non-working claimants get `95%` support unless a protected zero-earnings rule gives full support, working claimants use weekly net-pay bands, the savings and investments limit is `GBP 16,000`, and each non-dependant deduction is `GBP 7.92` per week unless an exemption applies. PolicyEngine UK returns `council_tax_reduction = GBP 1,710` and `council_tax_less_benefit = GBP 90` before non-dependant deductions.
- Ealing (working-age, band `D`, annual liability `GBP 1,800`, no children, no savings): the council's April 2026 scheme uses protected and non-protected weekly income bands, excludes working-age applicants with capital equal to or above `GBP 6,000`, applies a `GBP 38.54` weekly earnings disregard outside Universal Credit for non-single claimants, and has local non-dependant deductions from `GBP 8.35` to `GBP 23.13` per week. PolicyEngine UK returns `council_tax_reduction = GBP 1,440` for a non-protected no-income claimant and `GBP 1,800` for a protected no-income claimant.
- Enfield (working-age, band `D`, annual liability `GBP 1,800`, no children, no savings): the council's 2026/27 scheme caps working-age eligible liability at Band `C`, gives non-Universal Credit non-protected claimants up to `50%` support with a `22.5%` taper, protects single claimants under `25` and war widows, and uses Universal Credit net-earnings bands from `50%` to `10%` support. PolicyEngine UK returns `council_tax_reduction = GBP 800` for a non-protected no-income claimant and `GBP 1,600` for a protected no-income claimant.
- Haringey (working-age, band `D`, annual liability `GBP 1,800`, no children, no savings): the council's 2026/27 scheme gives ordinary working-age claimants up to `80.2%` support, protects working-age households with children or qualifying disability from that cap, applies a `20%` taper, and has a `GBP 10,000` working-age capital limit. PolicyEngine UK returns `council_tax_reduction = GBP 1,443.60` for an ordinary no-income claimant and `GBP 1,800` for a protected no-income claimant.
- Harrow (working-age, band `D`, annual liability `GBP 1,800`, no children, no savings): the council's 2026/27 scheme uses a split design: non-Universal Credit applicants receive up to `50%` ordinary support or `86%` disabled support with a `30%` taper, while Universal Credit applicants use household-type weekly net-earnings bands. PolicyEngine UK returns `council_tax_reduction = GBP 900` for an ordinary non-UC no-income claimant, `GBP 720` for a UC single claimant with `GBP 100` weekly net earnings, and `GBP 1,892` for a disabled claimant on a `GBP 2,200` Band `E` liability.
- Havering (working-age, band `D`, annual liability `GBP 1,800`, no children, no savings): the council's 2026/27 summary continues a legacy means-tested scheme with `75%` ordinary maximum support, `80%` disabled maximum support, a Band `D` cap, a `20%` taper, and a `GBP 6,000` working-age capital limit. PolicyEngine UK returns `council_tax_reduction = GBP 1,350` for an ordinary no-income claimant and `GBP 1,440` for a disabled no-income claimant; a Band `E` liability of `GBP 2,200` is capped to a `GBP 1,350` ordinary award.
- Hounslow (working-age, band `D`, annual liability `GBP 1,800`, no children, no savings): the council's live 2026 page and formal 2025/26 scheme use weekly net-earnings bands for working-age households, with ordinary support of up to `75%`, `90%` support for households where the claimant or partner receives Carer's Allowance or the Universal Credit carer element, and a `GBP 6,000` working-age capital limit. PolicyEngine UK uses household liquid savings as the available proxy for claimant/partner capital, and returns `council_tax_reduction = GBP 1,350` for a no-earnings ordinary claimant and `GBP 1,620` for a carer household.
- Lewisham (working-age, band `D`, annual liability `GBP 2,237.33`, no children, no savings): the council's 2026/27 budget papers continue its existing scheme with `75%` maximum working-age support, a `20%` taper, a `GBP 16,000` capital limit, tariff income above `GBP 6,000`, and gross-income non-dependant deductions. PolicyEngine UK returns `council_tax_reduction = GBP 1,678.00` for a no-income claimant, `GBP 3,356.00` on a Band `H` liability with no Band D cap, and `GBP 1,458.00` for a UC claimant with monthly earnings of `GBP 1,200` after the weekly UC earnings disregard. The detailed scheme source is labelled 2024/25; 2026/27 papers confirm the no-change continuation.
- Stevenage (working-age, band `D`, annual liability `GBP 1,800`, no children, no savings): the council's published scheme says working-age claimants receive `91.5%` of net liability, so PolicyEngine UK returns `council_tax_reduction = GBP 1,647` and `council_tax_less_benefit = GBP 153`.
- Chesterfield (working-age, band `D`, annual liability `GBP 1,800`, no children, no savings): the council's published scheme says working-age claimants receive `91.5%` of net liability, so PolicyEngine UK returns `council_tax_reduction = GBP 1,647` and `council_tax_less_benefit = GBP 153`.
- Colchester (working-age/local scheme, band `D`, annual liability `GBP 1,800`, no children, no savings): the council's 2026/27 formal scheme and current working-age page use weekly applicant-and-partner net-income bands with `80%` maximum support, a Band `D` liability cap, a `GBP 25` weekly earnings disregard, a strict `GBP 6,000` capital cutoff, protected `80%` support for source-listed benefit/disabled/blind groups inside the listed income bands, and source-listed Universal Credit element disregards. PolicyEngine UK returns `council_tax_reduction = GBP 1,440` for a no-income claimant, `GBP 720` for a no-child couple just above `GBP 225` weekly income, and `GBP 1,440` for a Band `H` liability capped to Band `D`. The formal scheme does not expose a working-age non-dependant deduction table.
- Warrington (`WA1 1UH`, band `C`, single working-age owner-occupier, no children, no savings, income-based JSA): entitledto returns `GBP 26.69` per week of Council Tax Support and `GBP 2.48` per week left to pay on a displayed bill of `GBP 29.17` per week, which is a `91.5%` maximum award on the displayed weekly bill. PolicyEngine UK applies the same rule structure.
- Merton (working-age, band `D`, annual liability `GBP 1,800`, no children, no savings): the council's published calculation guide says maximum Council Tax Support is usually `100%` of eligible Council Tax after discounts and non-dependant deductions, with a `20%` taper and a `GBP 16,000` capital limit, so PolicyEngine UK returns `council_tax_reduction = GBP 1,800` and `council_tax_less_benefit = GBP 0`.
- Southwark (working-age, band `D`, annual liability `GBP 1,800`, no children, no savings): the council's published 2025/26 policy summary says working-age applicants can receive up to `85%` of annual council tax liability, with a `20%` taper and a `GBP 16,000` capital limit, so PolicyEngine UK returns `council_tax_reduction = GBP 1,530` and `council_tax_less_benefit = GBP 270`.
- Darlington (working-age, band `D`, annual liability `GBP 1,800`, no children, no savings): the council's 2025/26 scheme says working-age support is up to `80%` of eligible Council Tax, with a `20%` taper and a `GBP 16,000` capital limit, so PolicyEngine UK returns `council_tax_reduction = GBP 1,440` and `council_tax_less_benefit = GBP 360`.
- Gateshead (working-age, band `D`, annual liability `GBP 1,800`, no children, no savings): the council's 2025/26 scheme says working-age households can receive support up to `91.5%` of their council tax bill and uses the `2 6/7%` daily excess-income percentage, equivalent to a `20%` weekly taper, so PolicyEngine UK returns `council_tax_reduction = GBP 1,647` and `council_tax_less_benefit = GBP 153`. The same source also sets a Gateshead-specific 2025/26 non-dependant deduction schedule, which PolicyEngine UK applies instead of the Housing Benefit schedule.
- King's Lynn and West Norfolk (working-age, band `D`, annual liability `GBP 1,800`, no children, no savings): the council's 2025/26 and 2026/27 scheme regulations say maximum Council Tax Reduction is `100%` of eligible Council Tax after discounts and non-dependant deductions, with a `2 6/7%` daily excess-income percentage, equivalent to a `20%` weekly taper, and a `GBP 16,000` capital limit, so PolicyEngine UK returns `council_tax_reduction = GBP 1,800` and `council_tax_less_benefit = GBP 0`. The scheme text says non-dependant deductions are uprated by the prescribed requirements regulations, so PolicyEngine UK uses the council's current non-dependant table for the applied 2025 and 2026 values.
- Norwich (working-age, band `D`, annual liability `GBP 1,800`, no children, no savings): the council's 2025/26 and 2026 scheme PDFs say maximum Council Tax Reduction is `100%` of eligible Council Tax after discounts and non-dependant deductions, with the `2 6/7%` daily excess-income percentage and a `GBP 16,000` capital limit, so PolicyEngine UK returns `council_tax_reduction = GBP 1,800` and `council_tax_less_benefit = GBP 0`. Norwich sets a separate working-age non-dependant deduction schedule, which PolicyEngine UK applies instead of the Housing Benefit schedule.
- North Norfolk (working-age, band `D`, annual liability `GBP 1,800`, no children, no savings): the council's 2025/26 scheme says maximum Council Tax Reduction is `91.5%` of eligible Council Tax after discounts and non-dependant deductions, with the `2 6/7%` daily excess-income percentage, equivalent to a `20%` weekly taper, and a `GBP 16,000` capital limit. The council's April 2026 update says the 2026/27 scheme continues under the arrangements introduced from `1 April 2025`. PolicyEngine UK returns `council_tax_reduction = GBP 1,647` and `council_tax_less_benefit = GBP 153`. The same source sets a flat `GBP 10` weekly non-dependant deduction and waives it where the claimant or partner receives the Limited Capability for Work component of Universal Credit.
- Policy in Practice Better Off Calculator (`SG13 8EQ`, East Hertfordshire, band `D`, single working-age owner-occupier, no children, no savings, income-based JSA, monthly council tax liability `GBP 150`): the public calculator resolves East Hertfordshire from postcode and returns `GBP 137.25` per month of Council Tax Support. That is exactly a `91.5%` award on the entered liability, matching the scheme structure and the PolicyEngine UK rule.
- Policy in Practice Better Off Calculator (`DY1 1HF`, Dudley, band `C`, single working-age owner-occupier, no children, no savings, income-based JSA, monthly council tax liability `GBP 113.25` with single-person discount): the public calculator resolves Dudley from postcode and returns `GBP 45.30` per month of Council Tax Support. That is exactly a `40%` award on the entered liability, matching Dudley's published scheme structure and the PolicyEngine UK rule.
- Policy in Practice Better Off Calculator (`WA1 1UH`, Warrington, band `C`, single working-age owner-occupier, no children, no savings, income-based JSA, monthly council tax liability `GBP 126.74` with single-person discount): the public calculator resolves Warrington from postcode and returns `GBP 95.06` per month of Council Tax Support. That is a `75%` award on the entered liability, which does not match Warrington's published 2025/26 Class D passported-JSA scheme, entitledto's `91.5%` result for the same scenario, or the current PolicyEngine UK encoding.
- Policy in Practice Better Off Calculator (`GL5 4UB`, Stroud, band `D`, single working-age owner-occupier, no children, no savings, income-based JSA, monthly council tax liability `GBP 148.09` with single-person discount): the public calculator resolves Stroud from postcode and returns `GBP 148.09` per month of Council Tax Support. That is full support on the entered liability, matching entitledto's behavior and the published Stroud scheme summary.
- Turn2us public calculator checks on the same four single working-age owner-occupier income-based JSA cases in East Hertfordshire, Warrington, Dudley, and Stroud all reached the final results page, but returned the same `Income-based Jobseekers Allowance` and `Universal Credit` lines for all four authorities and no CTR output. In these cases, Turn2us was not acting as an authority-specific CTR comparator.

For the East Hertfordshire and Warrington calculator checks, entitledto's annual tab appears to multiply rounded weekly outputs by `52`, so the weekly figures are the closest comparison point. Additional browser-only probing suggests that reusing an existing entitledto calculation ID is good enough for lone-parent and couple spot checks, but not yet good enough for other-adult/non-dependant cases: the later pages can retain stale branch state, so those results should not be treated as validated until the flow is replayed from a fresh entitledto session.

The public Policy in Practice calculator is testable through the browser, but not through a simple documented one-shot API. The frontend is a token-gated SPA on `betteroffcalculator.co.uk` backed by `api.betteroffcalculator.co.uk`; raw ad hoc `POST /api` requests return default baseline results unless the full calculator state has already been established in the session.

Dudley references:

- https://www.dudley.gov.uk/residents/benefits/council-tax-reduction-scheme/
- https://www.dudley.gov.uk/media/khllf4zc/dudley-council-tax-reduction-scheme-2025-26.pdf

East Hertfordshire references:

- https://www.eastherts.gov.uk/benefits-and-financial-support/council-tax-support
- https://cdn-eastherts.onwebcurl.com/s3fs-public/2025-03/East%20Herts%20S13a%20202526%20Scheme%20Final.pdf

East Suffolk references:

- https://www.angliarevenues.gov.uk/services/counciltax/reductions/what-is-ctax-reduction/upload/East-Suffolk-Council-Council-Tax-Reduction-Scheme-2025-26.pdf
- https://www.angliarevenues.gov.uk/services/housing-benefits/apply/
- https://www.angliarevenues.gov.uk/services/housing-benefits/non-dependant-deductions-ctrs.cfm

East Cambridgeshire references:

- https://www.angliarevenues.gov.uk/services/counciltax/reductions/what-is-ctax-reduction/upload/East-Cambridgeshire-District-Council-Council-Tax-Reduction-Schemes-2025-26.pdf
- https://www.angliarevenues.gov.uk/services/housing-benefits/apply/
- https://www.angliarevenues.gov.uk/services/housing-benefits/non-dependant-deductions-ctrs.cfm

Breckland references:

- https://www.angliarevenues.gov.uk/services/counciltax/reductions/what-is-ctax-reduction/upload/Breckland-Council-Tax-Reduction-Scheme-2025-26.pdf
- https://www.angliarevenues.gov.uk/services/housing-benefits/apply/
- https://www.angliarevenues.gov.uk/services/housing-benefits/non-dependant-deductions-ctrs.cfm

Brent references:

- https://www.brent.gov.uk/council-tax/council-tax-support

Bromley references:

- https://cds.bromley.gov.uk/documents/s50125675/Council%20Tax%20Support%20Scheme%202026-27.pdf
- https://www.bromley.gov.uk/downloads/file/3849/local-council-tax-reduction-scheme-from-1-april-2025

Bristol references:

- https://www.bristol.gov.uk/residents/benefits-and-financial-help/council-tax-reduction/council-tax-reduction-scheme
- https://www.bristol.gov.uk/files/documents/10754-bristol-council-tax-reduction-scheme-2026/file
- https://www.bristol.gov.uk/ask?id=73

Croydon references:

- https://croydon.moderngov.co.uk/ieDecisionDetails.aspx?AIId=26045
- https://www.croydon.gov.uk/benefits/changes-council-tax-support/how-we-work-out-amount-council-tax-support
- https://www.croydon.gov.uk/benefits/changes-council-tax-support/your-capital-savings-investments-and-property
- https://www.croydon.gov.uk/benefits/changes-council-tax-support/other-people-who-live-you
- https://www.croydon.gov.uk/council-tax/what-council-tax-and-how-much-it/council-tax-bands

Cumberland references:

- https://www.cumberland.gov.uk/benefits-and-financial-help/council-tax-reduction/make-claim-council-tax-reduction/council-tax-reduction-scheme
- https://www.cumberland.gov.uk/sites/default/files/2026-04/cumberland_council_final_council_tax_reduction_ctr_scheme_for_2026_to_2027.pdf
- https://www.cumberland.gov.uk/council-tax/how-council-tax-calculated-and-spent/your-council-tax-bill-explained/your-guide-council-tax-and-documents/cumberland-councils-guide-council-tax-2026-2027-including-explanatory-notes-and

Herefordshire references:

- https://councillors.herefordshire.gov.uk/documents/s50131817/202627%20Council%20Tax%20Reduction%20Scheme.pdf
- https://councillors.herefordshire.gov.uk/documents/s50131582/Approved%20202526%20Council%20Tax%20Reduction%20Scheme.pdf
- https://www.herefordshire.gov.uk/council-tax/council-tax-reduction/

Westmorland and Furness references:

- https://www.westmorlandandfurness.gov.uk/benefits-and-financial-help/council-tax-reduction/make-claim-council-tax-reduction
- https://www.westmorlandandfurness.gov.uk/sites/default/files/2026-03/Westmorland%20%26%20Furness%20Council%20%20CTR%20Scheme%20202627%20%28accessible%20March%202026%29.pdf

Kingston upon Hull references:

- https://www.hull.gov.uk/council-tax-reduction/help-pay-council-tax
- https://www.hull.gov.uk/downloads/file/239/council-tax-reduction-scheme-2025-to-2026
- https://cmis.hullcc.gov.uk/cmis/CalendarofMeetings/tabid/70/ctl/ViewMeetingPublic/mid/397/Meeting/11151/Committee/3/Default.aspx

North Yorkshire references:

- https://www.northyorks.gov.uk/sites/default/files/2026-03/North%20Yorkshire%20Council%27s%20Council%20Tax%20Reduction%20Scheme%202026%20to%202027.pdf
- https://edemocracy.northyorks.gov.uk/mgAi.aspx?ID=30077

Somerset references:

- https://www.somerset.gov.uk/benefits-and-payments/council-tax-reduction/
- https://somerset.moderngov.co.uk/ieListDocuments.aspx?MId=7598
- https://somerset.moderngov.co.uk/documents/s60490/Council%20Tax%20Reduction%20and%20Exceptional%20Hardship%20Scheme%202026-27.pdf
- https://somerset.moderngov.co.uk/documents/s59784/05a%20APPENDIX%203%20Somerset%20S13A%20202627%20Scheme%20DRAFT.pdf

Broadland references:

- https://www.southnorfolkandbroadland.gov.uk/asset-library/broadland-ctr-scheme-2025-26.pdf
- https://southnorfolkandbroadland.moderngov.co.uk/documents/s12491/CTAX%20Reduction%20Scheme.pdf

Fenland references:

- https://www.angliarevenues.gov.uk/services/counciltax/reductions/what-is-ctax-reduction/upload/Fenland-District-Council-Council-Tax-Reduction-Scheme-2025-26.pdf
- https://www.angliarevenues.gov.uk/services/housing-benefits/apply/
- https://www.angliarevenues.gov.uk/services/housing-benefits/non-dependant-deductions-ctrs.cfm

West Suffolk references:

- https://www.angliarevenues.gov.uk/services/counciltax/reductions/what-is-ctax-reduction/upload/West-Suffolk-Council-Council-Tax-Reduction-Scheme-2025-26.pdf
- https://www.angliarevenues.gov.uk/services/housing-benefits/apply/
- https://www.angliarevenues.gov.uk/services/housing-benefits/non-dependant-deductions-ctrs.cfm

South Norfolk references:

- https://www.southnorfolkandbroadland.gov.uk/asset-library/south-norfolk-ctr-scheme-2025-26.pdf
- https://southnorfolkandbroadland.moderngov.co.uk/documents/g1058/Printed%20minutes%2024th-Nov-2025%2009.00%20South%20Norfolk%20Cabinet.pdf?T=1

Lancaster references:

- https://www.lancaster.gov.uk/assets/attach/14831/lancaster-city-council-2025-26-council-tax-support-scheme.pdf

Oldham references:

- https://www.oldham.gov.uk/download/downloads/id/2632/council_tax_reduction_scheme_2025-26.pdf

Bolton references:

- https://www.bolton.gov.uk/downloads/file/745/bolton-council-tax-reduction-scheme

Basingstoke and Deane references:

- https://www.basingstoke.gov.uk/content/page/77332/Basingstoke%20S13A%202026%20Scheme%20Final.pdf

Crawley references:

- https://crawley.gov.uk/sites/default/files/2025-02/Council%20Tax%20Reduction%20scheme%202025%20to%202026.pdf

St Albans references:

- https://www.stalbans.gov.uk/sites/default/files/attachments/St%20Albans%20S13A%20202526%20Final.pdf
- https://www.stalbans.gov.uk/council-tax-support

Adur references:

- https://www.adur-worthing.gov.uk/media/Media,174007,smxx.pdf
- https://www.adur-worthing.gov.uk/benefits/council-tax-support/

Worthing references:

- https://www.adur-worthing.gov.uk/media/Media,174008,smxx.pdf
- https://www.adur-worthing.gov.uk/benefits/council-tax-support/

Sefton references:

- https://www.sefton.gov.uk/media/occbaemk/ctr-scheme-2026-27.pdf
- https://www.sefton.gov.uk/advice-benefits/help-with-council-tax/

Oxford references:

- https://www.oxford.gov.uk/council-tax-reduction/council-tax-reduction-scheme-2026-27

Redbridge references:

- https://www.redbridge.gov.uk/media/frbd0rgm/council-tax-reduction-scheme-2026-2027-full-scheme.pdf
- https://www.redbridge.gov.uk/media/gleawsfi/council-tax-reduction-scheme-2026-2027-on-redbridge-web-page.pdf
- https://www.redbridge.gov.uk/council-tax/discounts-and-exemptions/council-tax-reduction/apply-for-council-tax-reduction/
- https://www.redbridge.gov.uk/council-tax/bands-and-charges/

Stevenage references:

- https://www.stevenage.gov.uk/benefits/council-tax-support
- https://www.stevenage.gov.uk/documents/council-tax/council-tax-support-scheme-2025-26.pdf

Chesterfield references:

- https://www.chesterfield.gov.uk/council-tax-and-business-rates/council-tax/council-tax-support
- https://www.chesterfield.gov.uk/media/zuxllbgk/chesterfield-borough-council-council-tax-support-scheme-2019-20.pdf

Colchester references:

- https://www.colchester.gov.uk/housing-benefit-local-council-tax-support/lcts-working-age/
- https://cbccrmdata.blob.core.windows.net/noteattachment/CBC-null-Local-council-tax-support-policy-updated-01-04-26-Local%20Council%20Tax%20support%20policy.pdf

Warrington references:

- https://www.warrington.gov.uk/benefits-calculator
- https://www.warrington.gov.uk/income-and-capital
- https://www.warrington.gov.uk/non-dependants
- https://www.warrington.gov.uk/sites/default/files/2025-04/CTS%20Scheme%202025-26.pdf

Merton references:

- https://www.merton.gov.uk/sites/default/files/2025-03/Council%20Tax%20Reduction%20Scheme%20L%20B%20Merton%202025-26.pdf
- https://www.merton.gov.uk/council-tax-benefits-and-housing/benefits/council-tax-support/calculating-council-tax-support
- https://www.merton.gov.uk/council-tax-benefits-and-housing/benefits/council-tax-support/council-tax-support-scheme-consultations-and-official-text

Southwark references:

- https://www.southwark.gov.uk/council-tax/get-money-your-council-tax-bill/council-tax-reduction/how-much-your-bill-can-be-reduced
- https://www.southwark.gov.uk/sites/default/files/2025-03/Southwark%20Council%20Tax%20Reduction%20Policy%202025-26.pdf
- https://www.southwark.gov.uk/sites/default/files/2025-03/Southwark%20Council%20Tax%20Reducation%20Policy%202025-26%20shorter%20version.pdf

Darlington references:

- https://www.darlington.gov.uk/media/czqfj5rz/council-tax-support-scheme-25-26-final.pdf

Gateshead references:

- https://www.gateshead.gov.uk/article/27558/Part-1-Introduction
- https://www.gateshead.gov.uk/article/27575/Part-4-Classes-of-person-entitled-to-a-reduction-under-this-scheme
- https://www.gateshead.gov.uk/article/27582/Part-7-Maximum-council-tax-reduction-for-the-purposes-of-calculating-eligibility-for-a-reduction-under-this-scheme-and-the-amount-of-reduction
- https://www.gateshead.gov.uk/article/27578/Part-5-Classes-of-person-excluded-from-this-scheme

King's Lynn and West Norfolk references:

- https://www.west-norfolk.gov.uk/download/downloads/id/9853/council_tax_reduction_scheme_2025_to_2026.pdf
- https://www.west-norfolk.gov.uk/download/downloads/id/3330/council_tax_support_regulations.pdf
- https://www.west-norfolk.gov.uk/info/20019/council_tax_support/29/council_tax_support_-_non-dependants

Norwich references:

- https://www.norwich.gov.uk/download/downloads/id/10735/council_tax_reduction_scheme_2025-26.pdf
- https://www.norwich.gov.uk/sites/default/files/2026-03/Council-Tax-Reduction-Scheme-2026.pdf

North Norfolk references:

- https://www.north-norfolk.gov.uk/media/10894/north-norfolk-council-tax-reduction-scheme-for-2025-to-2026.pdf
- https://www.north-norfolk.gov.uk/tasks/benefits/housing-benefit-and-council-tax-support-rates-from-april-2026/

Hounslow references:

- https://www.hounslow.gov.uk/council-tax-support
- https://www.hounslow.gov.uk/downloads/file/11485/hounslow-council-tax-reduction-scheme-2025-to-2026
- https://democraticservices.hounslow.gov.uk/documents/s205995/Budget%20Report%202026.pdf

Lewisham references:

- https://lewisham.gov.uk/myservices/benefits/council-tax-reduction-scheme
- https://lewisham.gov.uk/-/media/services/council-tax/lewisham-council-tax-reduction-scheme-2024-2025.pdf
- https://lewisham.moderngov.co.uk/documents/s123568/2026-27%20PASC%20Draft%20Budget%20Report.pdf
- https://lewisham.moderngov.co.uk/documents/s123572/2026-27%20PASC%20Budget%20Report%20Y%20GF%20Appendices.pdf

Harrow references:

- https://www.harrow.gov.uk/downloads/file/33606/council-tax-support-scheme-2026-27

Havering references:

- https://democracy.havering.gov.uk/documents/s83106/12%20-%20Appendix%20I%20%20Summary%20of%20the%20Council%20Tax%20Support%20Scheme%202026-27.pdf
- https://democracy.havering.gov.uk/documents/s83059/0-1%20-%20Budget%20report%20cabinet%202026%202.pdf
- https://www.havering.gov.uk/downloads/file/6930/council-tax-support-scheme-2025-2026
