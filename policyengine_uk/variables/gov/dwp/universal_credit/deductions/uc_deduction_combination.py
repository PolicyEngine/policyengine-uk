from policyengine_uk.model_api import *


class UCDeductionCombination(Enum):
    NONE = "No deductions"
    ADVANCE_ONLY = "Advance deductions only"
    THIRD_PARTY_ONLY = "Third party deductions only"
    GOVERNMENT_ONLY = "Government deductions only"
    ADVANCE_AND_GOVERNMENT = "Advance and government deductions"
    ADVANCE_AND_THIRD_PARTY = "Advance and third party deductions"
    THIRD_PARTY_AND_GOVERNMENT = "Third party and government deductions"
    ALL_THREE = "Advance, third party and government deductions"


class uc_deduction_combination(Variable):
    label = "UC deduction type combination"
    documentation = (
        "Which deduction types this benefit unit repays, assigned from the "
        "DWP-published distribution of type combinations among UC households "
        "with deductions."
    )
    entity = BenUnit
    definition_period = YEAR
    value_type = Enum
    possible_values = UCDeductionCombination
    default_value = UCDeductionCombination.NONE

    def formula(benunit, period, parameters):
        # Estimation fallback: datasets can impute this directly (or override
        # the draw); the parameter lives under gov.simulation because it
        # describes the world, not the law.
        c = parameters(period).gov.simulation.uc_deductions.type_combination
        shares = np.array(
            [
                c.ADVANCE_ONLY,
                c.THIRD_PARTY_ONLY,
                c.GOVERNMENT_ONLY,
                c.ADVANCE_AND_GOVERNMENT,
                c.ADVANCE_AND_THIRD_PARTY,
                c.THIRD_PARTY_AND_GOVERNMENT,
                c.ALL_THREE,
            ]
        )
        total = shares.sum()
        if total <= 0:
            # Every share reformed to zero: nobody is assigned a combination.
            # filled_array keeps this branch on the same encoding path as the
            # select below, so it yields an EnumArray like the normal branch.
            return benunit.filled_array(UCDeductionCombination.NONE)
        cumulative = np.cumsum(shares / total)
        draw = benunit("uc_deduction_type_random_draw", period)
        index = np.searchsorted(cumulative, clip(draw, 0, 1 - 1e-9), side="right")
        index = clip(index, 0, len(shares) - 1)
        has_deduction = benunit("uc_has_deduction", period)
        combinations = [
            UCDeductionCombination.ADVANCE_ONLY,
            UCDeductionCombination.THIRD_PARTY_ONLY,
            UCDeductionCombination.GOVERNMENT_ONLY,
            UCDeductionCombination.ADVANCE_AND_GOVERNMENT,
            UCDeductionCombination.ADVANCE_AND_THIRD_PARTY,
            UCDeductionCombination.THIRD_PARTY_AND_GOVERNMENT,
            UCDeductionCombination.ALL_THREE,
        ]
        return select(
            [has_deduction & (index == i) for i in range(len(combinations))],
            combinations,
            default=UCDeductionCombination.NONE,
        )
