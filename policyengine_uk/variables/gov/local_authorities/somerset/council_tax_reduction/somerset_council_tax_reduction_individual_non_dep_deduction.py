from policyengine_uk.model_api import *


class somerset_council_tax_reduction_individual_non_dep_deduction(Variable):
    value_type = float
    entity = Person
    label = "Somerset Council Tax Reduction individual non-dependant deduction"
    definition_period = YEAR
    unit = GBP
    defined_for = "council_tax_reduction_individual_non_dep_deduction_eligible"
    reference = "https://somerset.moderngov.co.uk/documents/s59784/05a%20APPENDIX%203%20Somerset%20S13A%20202627%20Scheme%20DRAFT.pdf"

    def formula(person, period, parameters):
        ctr = parameters(period).gov.local_authorities.somerset.council_tax_reduction
        household_person = person.household.members
        claimant_benunit = household_person.benunit(
            "benunit_contains_household_head", period
        )
        claimant_local_scheme = person.household.any(
            claimant_benunit
            & household_person.benunit(
                "somerset_council_tax_reduction_is_local_scheme", period
            )
        )
        exempt = person(
            "somerset_council_tax_reduction_non_dep_source_exemption", period
        )
        deduction = ctr.non_dep_deduction.amount * WEEKS_IN_YEAR
        return claimant_local_scheme * where(exempt, 0.0, deduction)
