from policyengine_uk.model_api import *


class council_tax_reduction_non_dep_deductions(Variable):
    value_type = float
    entity = BenUnit
    label = "CTR non-dependent deductions"
    documentation = (
        "Deductions for a claiming family's non-dependants, whether in its "
        "own benefit unit or another family's, apportioned equally between "
        "the jointly liable people."
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
        # Every eligible non-dependant normally resides with each liable
        # person (SI 2012/2885 reg 9(1)): another family's adult, an
        # applicant's own adult son, or a boarder's or lodger's (reg 9(2)(e)
        # excludes only the person liable to pay the applicant). A
        # non-dependant of two or more jointly liable people is apportioned
        # equally between them (Sch 1 para 8(5)). Members of the applicant's
        # own family are not its non-dependants (reg 9(2)(a)).
        own_family_member = ~person(
            "is_benefit_unit_non_dependant_for_legacy_benefits", period
        )
        non_dependants = benunit.max(person.household.sum(deductions)) - benunit.sum(
            deductions * own_family_member
        )
        share = benunit("council_tax_reduction_joint_liability_share", period)
        return claims * share * non_dependants
