# Child Benefit

`child_benefit_entitlement` is the amount before take-up and payment opt-outs.
`child_benefit` pays that entitlement only when `would_claim_child_benefit`
is true, unless the charge-driven opt-out remains active. `CB_HITC` then charges
only the benefit actually paid.

Claiming and opting out of payment are independent inputs:

| Would claim | Opted out | Meaning |
|---|---|---|
| false | false or true | Nonclaimant; receives no payment under a charge reform |
| true | false | Claimant receiving payment |
| true | true | Registered claimant with a charge-driven payment opt-out |

EnhancedFRS draws the opt-out flag independently, including for nonclaimants.
That input remains supported: a false claim flag always prevents payment,
regardless of the opt-out flag. Household calculators should set
`would_claim_child_benefit` to false to represent a nonclaimant.

[Earlier Microcosm exports](https://github.com/PolicyEngine/microcosm/blob/4163b819402d9417554e0cb4e9ff890973897c24/packages/microcosm-build/src/microcosm/build/uk_runtime/child_benefit_take_up.py#L436)
stored `claims & ~opt_out` in `would_claim_child_benefit`, obscuring registered
opt-outs. Those datasets must be rebuilt or migrated by their producer to
export registered claims, including opted-out claimants, before using this
model to score the return to payment. The model does not infer claims from
opt-out flags or dataset names, since that would revive EnhancedFRS
nonclaimants. Coordinate the corrected Microcosm export, this model and rebuilt
data in a release; updating model code alone does not repair existing data.

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
