from policyengine_uk.model_api import *


class council_tax_reduction_non_dep_deductions(Variable):
    value_type = float
    entity = BenUnit
    label = "CTR non-dependent deductions"
    documentation = (
        "Deductions for a claiming family's non-dependants: those in its own "
        "benefit unit, in full, and those in other families, apportioned "
        "equally between the jointly liable people."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/2012/2885/regulation/9",
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/1/paragraph/8",
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
        # A non-dependant from another family is a non-dependant of each
        # jointly liable person, apportioned equally between them (SI
        # 2012/2885 Sch 1 para 8(5)).
        share = benunit("council_tax_reduction_joint_liability_share", period)
        from_other_families = share * benunit.max(
            person.household.sum(deductions * ~own_family)
        )
        return claims * (from_other_families + from_own_family)
