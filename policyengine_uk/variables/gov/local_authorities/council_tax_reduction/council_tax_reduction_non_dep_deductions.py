from policyengine_uk.model_api import *


class council_tax_reduction_non_dep_deductions(Variable):
    value_type = float
    entity = BenUnit
    label = "CTR non-dependent deductions"
    documentation = (
        "Deductions for the applicant's non-dependants, including those in "
        "the applicant's own benefit unit, for a family that claims. A "
        "non-dependant of two or more jointly liable people is apportioned "
        "equally between them."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/2012/2885/regulation/9",
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/1/paragraph/8",
    )

    def formula(benunit, period, parameters):
        # Every eligible person in the household is a non-dependant of each
        # claiming family: the claimant's own family has only its benefit-unit
        # non-dependants, and jointly liable sharers are not non-dependants.
        deductions = benunit.members(
            "council_tax_reduction_individual_non_dep_deduction", period
        )
        deductions_in_household = benunit.max(benunit.members.household.sum(deductions))
        # A non-dependant of two or more jointly liable people is apportioned
        # equally between them (SI 2012/2885 Sch 1 para 8(5)).
        share = benunit("council_tax_reduction_joint_liability_share", period)
        claims = benunit("council_tax_reduction_claimant_benunit", period)
        return claims * deductions_in_household * share
