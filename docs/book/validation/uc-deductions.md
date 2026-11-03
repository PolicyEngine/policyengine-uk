# Universal Credit deductions

```{important}
Per-household deduction statistics are validated against the DWP deductions statistics. **Weighted aggregates are not.** They scale with the model's Universal Credit caseload, which falls short of the administrative count, so headcounts and costs of deduction reforms — including protected-floor reforms — run materially low. Quote the per-household layer; treat aggregates as lower bounds until the caseload gap closes.
```

PolicyEngine UK models the money DWP takes off Universal Credit awards to repay debts: advance repayments, government debt (benefit and tax credit overpayments) and third party deductions such as utility arrears.

The implementation separates **latent demand** from the **statutory cap**. `uc_latent_deduction_rate` assigns deduction demand from the distribution DWP observed in March to May 2025 — the last full months under the 25% cap — and `gov.dwp.universal_credit.deductions.cap` applies the operational cap (40% to October 2019, 30%, 25%, then 15% under the Fair Repayment Rate from 30 April 2025) at runtime. Assigning observed post-cap rates directly would bake the cap into the data and make cap-raising reforms inexpressible.

## Advance repayments under allowance reforms

`uc_advance_repayment_amount` accepts annual cash instalments before the cap,
abolition switch and available-award limits. Set the actual amount when known;
zero explicitly removes the advance estimate. Negative values, including the
default -1, mean no amount was supplied. Each omitted benefit unit uses the
fallback even when other units supply cash. A change to the standard allowance
does not increase this demand. Actual recovery can increase if a higher
allowance releases a binding deduction cap.

For existing latent-rate and type-combination inputs, the fallback keeps the
existing marginal-mean split and converts its advance share using the **same
year's unreformed standard allowance** for the claimant category. The reference
reads the projected baseline parameter tree at 30 April, consistently with
fiscal-year sampling. For example, the 2025 single 25+ allowance of £400.14/month
converts a 10% advance share to £40.014/month. Reforming the allowance to £440
keeps that cash demand unchanged, subject to the current 15% cap and penny floor.
[SI 2013/383 regulation 10](https://www.legislation.gov.uk/uksi/2013/383/regulation/10)
provides for recovery by offset/deduction; it does not set an allowance-indexed
instalment.

The final award and protected-floor allocation continue to consume
`uc_deduction_rate` times the standard allowance. An explicitly supplied rate
retains its existing effect and overrides the rate formula, including its cash
advance calculation. The usual advance, third-party and government abolition
switches retain their existing behavior.

This change isolates allowance reforms within each annual cross-section. The
legacy inputs do not identify the cash-origin year, repayment duration or cohort
schedule. They cannot establish unchanged instalments across projected years or
family-status changes. Supply cash for the relevant years to describe a known
advance schedule. Government/third-party percentage proxies and the aggregate
above-cap excess are unchanged; their legal classification, maintenance priority
and annual projection remain separate work under #2410. No maintenance or last
resort cash interface or new category incidence is introduced.

## Validation against DWP deductions statistics

Enhanced FRS 2023/24 v1.40.3, against [DWP's Universal Credit deductions statistics](https://www.gov.uk/government/statistics/universal-credit-quarterly-statistics-29-april-2013-to-12-february-2026/universal-credit-deductions-statistics-march-2025-to-february-2026).

Shares below are of **all** UC households, not of those with deductions — the denominator both the model and DWP use.

| Statistic | Model | DWP published |
|---|---|---|
| Share of UC households with deductions | 47.0–47.1% | 46–47% |
| At-cap share of all UC households, 25% regime (2024) | 13.4% | 13–14% (Mar–May 2025) |
| At-cap share of all UC households, 15% regime (2025) | 26.4% | 21% (Jun 2025–Feb 2026) |
| Above-cap share of all UC households (last resort) | 1.8% | 2% |
| Mean monthly deduction, 25% regime | £66 | £67–68 |
| Mean monthly deduction, 15% regime | £50 | £51–54 |
| Mean annual gain, 25%→15% cap | £421 | £420 (gov.uk) |
| Households better off, 25%→15% cap | 1.01m | ~1.2m (gov.uk) |

The pre-Fair-Repayment-Rate pileup at the cap and both regimes' mean amounts reproduce without being separately fitted: the cap parameter generates them from the same latent distribution.

## Limitations

These bound what the module can support. They are stated rather than tuned away.

### Aggregates scale with the UC caseload

The model has 4.2m UC benefit units against roughly 7.2m administrative households, and correspondingly 1.9m deducting households and £1.2bn/year deducted against 3.3m and roughly £2.0bn/year in the administrative data. This is the model's UC take-up and calibration gap, not a deductions artefact — per-household statistics validate precisely because the gap divides out. It is tracked in [policyengine-uk-data#452](https://github.com/PolicyEngine/policyengine-uk-data/issues/452).

The practical consequence: **poverty headcounts and exchequer costs of a protected-floor or cap reform run low roughly in proportion to the caseload shortfall.** Analyses replicating published floor estimates (such as JRF's) should compare per-household gains and distributional shape, not totals.

### The at-cap share under the 15% regime runs high

The model puts 26.4% of UC households at the 15% cap against 21% observed. The latent-demand model holds demand fixed while real deductions attrit under a lower cap through affordability requests and composition drift.

This has a direction. Reforms that **lower** the cap further overstate the number of constrained households and so overstate the gains from later raising it. Reforms that **raise** the cap toward 25% sit inside the observed window and are on firmer ground.

### Only 2024 and 2025 are validated

The latent distribution is observed in 2025 and applied to all model years as a constancy assumption; published deductions statistics begin in March 2025. Simulations of years before 2021 apply a 2025-shaped demand distribution under the 40% and 30% caps then in force, which no published statistic can check. Treat pre-2024 deduction results as uncalibrated.

### The protected floor binds on last resort deductions

The `protected_floor` lever limits combined deductions and benefit cap reductions to (1 − floor) × the standard allowance. Where the current-law split already fits inside that allowance, nothing changes. Where it does not, deductions are met first from the protected award, up to the allowance, and the benefit cap reduction absorbs the rest. Both `uc_deductions` and `uc_benefit_cap_reduction_after_floor` come from one allocation (`_reduction_allocation.py`), so they agree by construction.

JRF specifies the combined limit, not a priority between the two: their [September 2026 briefing](https://www.jrf.org.uk/social-security/a-protected-minimum-floor-in-universal-credit-to-cut-deep-child-poverty) proposes that "the sum of the 'capped amount' and any debt deductions is limited to the difference between a household's standard allowance and the level of the protected minimum floor". Debt first is the modeling choice, for three reasons. Under the Fair Repayment Rate the 15% deductions cap equals the allowance an 85% floor leaves, so cappable deductions never breach the floor on their own, and the policy JRF builds on (extending the Fair Repayment Rate "to all deductions, including the benefit cap") leaves deductions where that rate puts them. JRF's own example (standard allowance £98 a week, a £15 deduction, an £80 cap reduction, total limited to £15) is consistent with it. And it does not depend on how heavily the household is capped: if the deduction were limited by the gross cap reduction, a household capped down to a few pence would have its deduction squeezed to almost nothing even though the floor then removes most of that cap. The award is the same under either priority; only the split differs.

Where deductions alone do exceed the allowance, the floor binds on the whole of `uc_deductions`, including the above-cap excess that current law exempts from the deductions cap (last resort and child maintenance deductions). JRF's briefing does not say whether their floor exempts those categories — its worked example involves only cappable deductions and the benefit cap — so this is a modeling choice.

Both components report what the award actually loses, so `uc_deductions` and `uc_benefit_cap_reduction_after_floor` sum to the entitlement forgone, and the applied cap reduction never exceeds the award (a £1,000 cap reduction on a £500 award applies £500). `uc_benefit_cap_reduction`, the regulation 81 amount, itself stays gross, and so does `benefit_cap_reduction`, which adds it to the Housing Benefit reduction. Read `uc_benefit_cap_reduction_after_floor` for the cap reduction applied to a UC award under a floor reform.

### Other assumptions

- Rate and type combination are drawn independently: DWP publishes no joint table. Type-abolition reforms split a household's rate by national mean amounts per type (£41 advance / £37 third party / £59 government).
- Deduction spells are annualised under the surveyed-status-as-full-year convention. Monthly means validate, so cross-sectional statistics are sound, but annual per-household gains are upper bounds for spell-limited types such as advance recovery (at most 24 months).
- The last resort band is top-coded at 25% in DWP tables; its 30% upper edge is a modeling assumption.
- Regional incidence factors derive from rounded constituency proportions across all 633 rows of DWP's Table 6.
- The rate distribution is national. Regional composition plausibly differs (more advances in high-incidence regions); the module assumes it does not.

## Reform levers

```python
# Return the cap to 25%:
{"gov.dwp.universal_credit.deductions.cap": {"2026-01-01.2030-12-31": 0.25}}

# Abolish government debt deductions only:
{
    "gov.dwp.universal_credit.deductions.abolish.government": {
        "2026-01-01.2030-12-31": True
    }
}

# JRF-style protected minimum floor at 85% of the standard allowance,
# binding on deductions and benefit cap reductions jointly:
{"gov.dwp.universal_credit.deductions.protected_floor": {"2026-01-01.2030-12-31": 0.85}}
```

A cap of 1 − *x* is equivalent to a protected minimum floor at *x* of the standard allowance for capped deduction types. The dedicated `protected_floor` lever additionally binds on benefit cap reductions, which is where most of JRF's post-Fair-Repayment-Rate effect comes from — and, because deductions are met first, where nearly all of the modeled effect lands.

## Where the assignment lives

Statutory parameters — the cap, the protected floor, the minimum payable penny, the abolition switches — live under `gov.dwp.universal_credit.deductions`. The calibrated distributions live under `gov.simulation.uc_deductions`: they describe the world, not the law.

The assignment formulas are an explicit fallback. The end state imputes `uc_latent_deduction_rate` and `uc_deduction_combination` at dataset build, at which point the model consumes them as plain inputs and the fallback retires; raw-FRS users keep working through the fallback until then. Assignment uses deterministic splitmix64 hashes of `benunit_id`, reproducible across runs and machines, and overridable by datasets or situations through `uc_deduction_random_draw` and `uc_deduction_type_random_draw`. Every simulation built from data gets the hashed draws, including a constituency or local authority filtered from the national data, and a benefit unit gets the same draw there as in the national run. Household situations get no deductions unless set explicitly.
