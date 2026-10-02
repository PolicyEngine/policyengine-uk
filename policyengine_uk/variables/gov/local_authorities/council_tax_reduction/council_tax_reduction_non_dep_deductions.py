from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.dwp.housing_benefit.non_dep_deduction._non_dependants import (
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
        "Deductions for a claiming family's non-dependants. Another family's "
        "pay one deduction per couple, the higher of the two members' amounts "
        "(both, in the Welsh scheme for people who are not pensioners, when "
        "the couple has a Universal Credit award), and one for each other "
        "member, apportioned equally between the jointly liable people. A "
        "non-dependant in the claiming family's own benefit unit is its alone. "
        "None if the applicant or partner is exempt."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/2012/2885/regulation/9",
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/1/paragraph/8",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/1/paragraph/3",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/6/paragraph/5",
        "https://www.legislation.gov.uk/ssi/2012/319/regulation/48",
        "https://www.legislation.gov.uk/ssi/2021/249/regulation/90",
    )

    def formula(benunit, period, parameters):
        person = benunit.members
        deductions = person(
            "council_tax_reduction_individual_non_dep_deduction", period
        )
        claims = benunit("council_tax_reduction_claimant_benunit", period)
        # A non-dependant in a claiming family's own benefit unit is that
        # applicant's alone (as for HB: LHA Guidance Manual 2.093, example 2).
        own_family = person(
            "is_benefit_unit_non_dependant_for_legacy_benefits", period
        ) & person.benunit("council_tax_reduction_claimant_benunit", period)
        from_own_family = benunit.sum(deductions * own_family)
        # Another family's non-dependants: one deduction for a couple, the
        # higher (Sch 1 para 8(3)), except both members of a Welsh working-age
        # couple on Universal Credit (WSI 2013/3029 Sch 6 para 5(3)), and one
        # for each other member, counted once per family and apportioned
        # equally between the jointly liable people (para 8(5)).
        country = benunit.household("country", period)
        has_pensioner = benunit.household(
            "council_tax_reduction_household_has_pensioner", period
        )
        each_member_deducted = (
            is_wales_scheme(country)
            & ~has_pensioner
            & (benunit("universal_credit_pre_benefit_cap", period) > 0)
        )
        family_amount = deduction_per_family(
            benunit, period, deductions * ~own_family, each_member_deducted
        )
        counted = person("is_benunit_head", period) * benunit.project(family_amount)
        share = benunit("council_tax_reduction_joint_liability_share", period)
        from_other_families = share * benunit.max(person.household.sum(counted))
        # Each applicant's own exemption (Sch 1 para 8(6)): where families share
        # the rent and each claims, one family's disability does not exempt
        # another's claim.
        applicant_exempt = benunit(
            "council_tax_reduction_applicant_has_non_dep_exemption", period
        )
        return where(
            applicant_exempt, 0, claims * (from_other_families + from_own_family)
        )
