from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.dwp.housing_benefit.non_dep_deduction._non_dependants import (
    charged_to_other_families,
    deduction_per_family,
)


class housing_benefit_non_dep_deductions(Variable):
    value_type = float
    entity = BenUnit
    label = "non-dependent deductions"
    documentation = (
        "Deductions for the non-dependants residing with the claimant: one "
        "for each non-dependant couple, the higher of the two members' "
        "amounts, and one for each other member, apportioned between the "
        "families liable for the rent by their shares; none if the claimant "
        "or partner is exempt."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/3",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/74",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/55",
    )

    def formula(benunit, period, parameters):
        # Deductions are made for non-dependants residing with the claimant
        # (HB Regs 2006 reg 74; HB (SPC) Regs 2006 reg 55). Joint occupiers,
        # boarders, lodgers and the landlord's household are not
        # non-dependants (reg 3(2)(d)-(e), 3(4)). A couple pays one deduction,
        # the higher (reg 74(3)). A non-dependant of more than one joint
        # occupier is apportioned between them by their shares of the
        # payments (reg 74(5); SPC reg 55(5)), so each family liable for the
        # household's rent bears its share; a boarder or lodger bears none.
        person = benunit.members
        deductions = person(
            "household_benefits_individual_non_dep_deduction", period
        ) * person("is_non_dependant_of_household_head", period)
        deduction_for_benunit = deduction_per_family(benunit, period, deductions, False)
        share = benunit("share_of_household_rent", period)
        claimant_exempt = benunit(
            "housing_benefit_non_dep_deductions_claimant_exempt", period
        )
        return where(
            claimant_exempt,
            0,
            share * charged_to_other_families(benunit, period, deduction_for_benunit),
        )
