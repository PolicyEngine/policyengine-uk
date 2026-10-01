from policyengine_uk.model_api import *
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
        "the couple has a Universal Credit award), and none if the applicant "
        "or partner is exempt."
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
        deduction_for_benunit = where(
            each_member_deducted,
            benunit.sum(deductions),
            benunit.max(deductions),
        )
        is_benunit_head = benunit.members("is_benunit_head", period)
        counted = is_benunit_head * benunit.project(deduction_for_benunit)
        deductions_in_household = benunit.max(benunit.members.household.sum(counted))
        applicant_exempt = benunit.household(
            "council_tax_reduction_household_has_non_dep_exemption", period
        )
        return where(
            applicant_exempt, 0, deductions_in_household - deduction_for_benunit
        )
