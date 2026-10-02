from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.dwp.housing_benefit.non_dep_deduction._non_dependants import (
    charged_to_other_families,
    deduction_per_family,
)
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_wales_scheme,
)


class council_tax_reduction_non_dep_deductions(Variable):
    value_type = float
    entity = BenUnit
    label = "CTR non-dependent deductions"
    documentation = (
        "Deductions for the non-dependants in other benefit units of the "
        "household: one per couple, the higher of the two members' amounts "
        "(both, in the Welsh scheme for people who are not pensioners, when "
        "the couple has a Universal Credit award), one for each other member, "
        "and none if the applicant or partner is exempt."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/1/paragraph/8",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/1/paragraph/3",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/6/paragraph/5",
        "https://www.legislation.gov.uk/ssi/2012/319/regulation/48",
        "https://www.legislation.gov.uk/ssi/2021/249/regulation/90",
    )

    def formula(benunit, period, parameters):
        deductions = benunit.members(
            "council_tax_reduction_individual_non_dep_deduction", period
        )
        country = benunit.household("country", period)
        has_pensioner = benunit.household(
            "council_tax_reduction_household_has_pensioner", period
        )
        # WSI 2013/3029 Sch 6 para 5(3).
        each_member_deducted = (
            is_wales_scheme(country)
            & ~has_pensioner
            & (benunit("universal_credit_pre_benefit_cap", period) > 0)
        )
        deduction_for_benunit = deduction_per_family(
            benunit, period, deductions, each_member_deducted
        )
        applicant_exempt = benunit.household(
            "council_tax_reduction_household_has_non_dep_exemption", period
        )
        return where(
            applicant_exempt,
            0,
            charged_to_other_families(benunit, period, deduction_for_benunit),
        )
