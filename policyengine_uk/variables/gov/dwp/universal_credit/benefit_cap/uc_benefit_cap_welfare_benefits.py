from policyengine_uk.model_api import *
from policyengine_uk.utils.benefit_cap import benefit_cap_couple
from policyengine_uk.utils.benefit_unit import award_of_couple
from policyengine_uk.utils.supplied_inputs import supplied_input
from policyengine_uk.variables.gov.dwp.benefit_cap_welfare_benefits import (
    CLAIMANT_OR_PARTNER_BENEFITS,
    FAMILY_BENEFITS,
)
from policyengine_uk.variables.gov.dwp.esa_income import (
    income_related_esa_award_on_reports,
)
from policyengine_uk.variables.gov.dwp.jsa_income import (
    income_related_jsa_award_on_reports,
)

# UC Regs 2013 reg 80(2A): where the welfare benefit is Housing Benefit, "the
# amount to be used is nil". The Universal Credit cap therefore counts the
# Housing Benefit cap's benefits other than Housing Benefit.
UC_FAMILY_BENEFITS = [
    benefit
    for benefit in FAMILY_BENEFITS
    if benefit != "housing_benefit_pre_benefit_cap"
]


def supplied_total_without_housing_benefit(period) -> str:
    return (
        f"The inputs supply benefit_cap_welfare_benefits for {period}, a total "
        "that includes Housing Benefit, which the Universal Credit cap counts "
        "as nil (UC Regs 2013 reg. 80(2A)). Supply "
        "housing_benefit_pre_benefit_cap for the same period, for the cap to "
        "subtract, or supply uc_benefit_cap_welfare_benefits. The model doesn't "
        "calculate that Housing Benefit for Universal Credit, because the "
        "Housing Benefit non-dependant deductions read universal_credit."
    )


class uc_benefit_cap_welfare_benefits(Variable):
    value_type = float
    entity = BenUnit
    label = "Welfare benefits counted by the Universal Credit benefit cap"
    documentation = (
        "The welfare benefits the Universal Credit cap counts: those in "
        "benefit_cap_welfare_benefits, for the same single person or couple, "
        "with Housing Benefit at nil (UC Regs 2013 reg. 80(2A)). Where the "
        "inputs supply benefit_cap_welfare_benefits, whose total includes "
        "Housing Benefit, this subtracts the supplied "
        "housing_benefit_pre_benefit_cap. Inputs that supply the combined "
        "total also supply housing_benefit_pre_benefit_cap or this variable; "
        "otherwise the formula raises ValueError. No baseline formula on "
        "Universal Credit's route calculates Housing Benefit, so the Housing "
        "Benefit non-dependant deductions can read universal_credit."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/ukpga/2012/5/section/96",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/79",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/80",
    )

    def formula(benunit, period, parameters):
        # A supplied combined total includes Housing Benefit, and the inputs
        # supply that Housing Benefit too. Calculating it here would make
        # Universal Credit depend on Housing Benefit, whose non-dependant
        # deductions read universal_credit. A value a scenario stores as the
        # model's own (set_model_value) supplies neither.
        if supplied_input(benunit, "benefit_cap_welfare_benefits", period) is not None:
            if (
                supplied_input(benunit, "housing_benefit_pre_benefit_cap", period)
                is None
            ):
                raise ValueError(supplied_total_without_housing_benefit(period))
            return benunit("benefit_cap_welfare_benefits", period) - benunit(
                "housing_benefit_pre_benefit_cap", period
            )
        # The rest follows benefit_cap_welfare_benefits, in the same order.
        couple = benefit_cap_couple(benunit, period)
        income_based = award_of_couple(
            benunit,
            period,
            "jsa_income",
            "jsa_income_reported",
            income_related_jsa_award_on_reports,
            couple,
        ) + award_of_couple(
            benunit,
            period,
            "esa_income",
            "esa_income_reported",
            income_related_esa_award_on_reports,
            couple,
        )
        return income_based + add_for_members(
            benunit,
            period,
            CLAIMANT_OR_PARTNER_BENEFITS + UC_FAMILY_BENEFITS,
            couple,
        )
