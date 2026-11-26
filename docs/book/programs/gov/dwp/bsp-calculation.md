# Bereavement Support Payment calculation

PolicyEngine provides a financial calculation for one independently qualified
Bereavement Support Payment (BSP) award from fiscal/model year 2017. The route
covers standard and higher payments in Great Britain and Northern Ireland.
It does not determine entitlement or infer recipients from widowhood, children,
current benefits or reported cash.

## Reported and calculated cash

The canonical `bsp` output preserves **all** `bsp_reported` and adds
`bsp_calculated` once. The additional calculation defaults off. Set
`bsp_add_calculated_award` only when the new payments are verified as additional
to and disjoint from every reported BSP, WPA, war-pension or residual amount.
Reported positivity does not prove that a cell contains pure BSP. No mixed
reported amount is replaced, subtracted or automatically reclassified. The
existing dataset split and projection compatibility remain unchanged.

Only `bsp` enters the existing income, spending and fiscal accounting. The three
calculated components are not extra budget or household-income terms.

## Initial payment

Supply a fixed actual fiscal/model receipt year in `bsp_initial_payment_year`
and the independently established `bsp_initial_payment_rate` (`STANDARD` or
`HIGHER`). Zero/unknown year or an unknown category establishes no initial
payment. Both facts require genuine supplied provenance; calculated caches do
not establish them. The amount appears only when the requested year matches the
fixed receipt year. Claim year and death year are not substitutes for actual
receipt timing.

The standard initial amount is £2,500 and the higher amount is £3,500. These
are additional to recurring instalments. Later adjustments or top-ups to the
initial award are outside this route; use the normal explicit final-cash
override for such established payments. No £1,000 adjustment is inferred from
the difference between headline rates.

## Recurring instalments

Supply these facts for the **exact requested year**:

- `bsp_standard_instalments`: actual qualified standard-rate instalments received.
- `bsp_higher_instalments`: actual qualified higher-rate instalments received,
  disjoint from the standard count.
- `bsp_instalments_received_before_year`: known total standard and higher
  instalments already received for this same award before that year.

All three need genuine current-period inputs. Missing or stale history differs
from verified zero; a calculated cache does not supply evidence. Counts must
be nonnegative, prior receipts must be between zero and 18, and the two current
counts together must not exceed `18 - prior receipts`. An inconsistent
allocation produces zero recurring cash. The model does not invent which rate
came first or silently trim one count. Each standard instalment pays £100 and
each higher instalment pays £350.

There is no 12-instalment cash-year limit: accepted arrears can concentrate more
than 12 receipts in one year, subject to the combined lifetime guard. No monthly
entitlement or cash calendar is reconstructed. Across separate calculations,
the caller must keep the same award identity and consistent prior history.

For example, an additional qualified standard initial payment and 18 standard
instalments total £4,300; the analogous higher-rate total is £9,800. These are
financial maxima, not an automatic award for every bereaved person. Rates are
parameterised under `gov.dwp.bsp` and remain flat without an uprating key.
Pre-2017 calculated components are zero; reported legacy cash remains intact.

## Facts outside this calculation

Entitlement requires an external determination of contribution/work-related
conditions, residence, relationship, death and claim dates, pension age,
pregnancy/Child Benefit higher-rate facts and applicable remedial provisions.
Late claims, cohabiting-parent remedial cases and rate transitions must already
be qualified before receipt facts are supplied. Separate standard/higher counts
allow established transitions without repricing all receipts at the latest rate.
Retained-capital consequences for other benefits are not modelled here.

No dataset supplies these new facts automatically. This is a household and
rate-reform surface, not population imputation, a producer split, complete BSP
eligibility or an historical entitlement ledger. The broader
[bereavement support plan](bereavement-support-plan.md) retains those future
workstreams, including historical WPA.

## Sources

- [GOV.UK: BSP amounts and payment timing](https://www.gov.uk/bereavement-support-payment/what-youll-get).
- [Northern Ireland Direct: BSP payments](https://www.nidirect.gov.uk/articles/bereavement-support-payment).
- [GB BSP Regulations 2017, regulation 3](https://www.legislation.gov.uk/uksi/2017/410/regulation/3): recurring and additional initial amounts.
- [2026 up-rating order, article 19](https://www.legislation.gov.uk/uksi/2026/148/article/19/made): all four amounts remain unchanged.
