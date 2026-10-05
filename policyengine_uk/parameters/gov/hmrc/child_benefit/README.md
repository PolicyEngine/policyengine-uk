# Child Benefit

`child_benefit_entitlement` is the amount before take-up and payment opt-outs.
`child_benefit` pays that entitlement when either `would_claim_child_benefit`
or `child_benefit_opts_out` identifies a claimant, unless the charge-driven
opt-out remains active. `CB_HITC` then charges only the benefit actually paid.

The two inputs follow the [Microcosm Child Benefit export contract](https://github.com/PolicyEngine/microcosm/blob/4163b819402d9417554e0cb4e9ff890973897c24/packages/microcosm-build/src/microcosm/build/uk_runtime/child_benefit_take_up.py#L436):

| Would claim | Opted out | Meaning |
|---|---|---|
| false | false | Genuine nonclaimant; receives no payment under a charge reform |
| true | false | Claimant receiving payment |
| false or true | true | Registered claimant with a charge-driven payment opt-out |

Microcosm stores claims excluding opted-out families in `would_claim_child_benefit`.
The model therefore also recognises `child_benefit_opts_out` as evidence of a
registered claim. Older datasets drew the opt-out flag independently, including
for nonclaimants. Producers of those datasets must clear that flag for genuine
nonclaimants before loading; the model cannot distinguish the two meanings from
the booleans alone. Household calculators should supply both flags as false to
represent a nonclaimant.

`gov.hmrc.child_benefit.opt_out_charge_share` is a behavioural assumption, not
a statutory eligibility rule. It defaults to one: a flagged family continues
to opt out only while the charge would recover the full benefit. The charge
share is calculated independently of payment and clipped to [0, 1]. A reform
that reduces the share below the threshold, removes the charge or neutralises
`CB_HITC` restores payment. A zero charge never sustains an opt-out, even if
the assumed threshold is zero. Genuine nonclaimants remain outside payment.

Microcosm selects fully charged families first and can draw from partly charged
families if needed to meet its target. The model's default threshold is an
explicit assumption; it does not reproduce that taper fallback. Researchers can
change the threshold to test other responses. A nonpositive taper width is
treated as a cliff: no charge at or below its start and a full charge above it.
