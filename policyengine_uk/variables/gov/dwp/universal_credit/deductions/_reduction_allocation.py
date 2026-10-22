"""Split a Universal Credit award's reductions between debt deductions and
the benefit cap.

uc_deductions and uc_benefit_cap_reduction_after_floor both call this, so
they agree by construction, and neither reads the other, which keeps the
graph acyclic.
"""

from policyengine_uk.model_api import *


def allocate_uc_reductions(
    pre_cap_award, gross_cap_reduction, deduction_demand, max_reduction, minimum_payable
):
    """Return (deductions, applied cap reduction) for each benefit unit.

    pre_cap_award: universal_credit_pre_benefit_cap.
    gross_cap_reduction: uc_benefit_cap_reduction, the regulation 81 amount
        of SI 2013/376. benefit_cap_reduction and uc_has_deduction read it
        too, so it is never floored.
    deduction_demand: cash demand after the administrative/statutory caps,
        before the one-penny rule.
    max_reduction: uc_maximum_reduction, infinite when no protected floor is
        in force (current law).
    minimum_payable: the one-penny rule of Schedule 6 paragraph 3(1)(a) of
        SI 2013/380, annualised.

    Current law: regulation 81 reduces the award by the cap first, and
    deductions come out of what is left, leaving at least a penny payable
    (main's operations, in main's order). The applied cap reduction is the
    award actually lost, so it is bounded by the award; the gross reduction
    can exceed it.

    Under a protected floor nothing changes unless that split takes more
    than the floor allowance. Where it does, deductions are met first from
    the protected award, up to the allowance, and the cap reduction takes
    whatever allowance is left. Working from the deduction demand rather
    than the current-law deduction matters for heavily capped awards: there
    the penny rule had already squeezed the deduction under the gross cap,
    but the floor removes most of that cap.
    """
    floor_active = np.isfinite(max_reduction)

    # Current law.
    award = max_(pre_cap_award - gross_cap_reduction, 0)
    deductions = min_(deduction_demand, max_(award - minimum_payable, 0))
    cap_reduction = min_(gross_cap_reduction, max_(pre_cap_award - deductions, 0))

    # Protected floor binding: deductions first, the cap reduction absorbs.
    binds = floor_active & (cap_reduction + deductions > max_reduction)
    floor_deductions = min_(
        min_(deduction_demand, max_reduction),
        max_(pre_cap_award - minimum_payable, 0),
    )
    penny = where(floor_deductions > 0, minimum_payable, 0)
    floor_cap_reduction = min_(
        min_(gross_cap_reduction, max_(max_reduction - floor_deductions, 0)),
        max_(pre_cap_award - floor_deductions - penny, 0),
    )
    return (
        where(binds, floor_deductions, deductions),
        where(binds, floor_cap_reduction, cap_reduction),
    )
