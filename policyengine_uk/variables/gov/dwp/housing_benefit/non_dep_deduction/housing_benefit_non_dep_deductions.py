from policyengine_uk.model_api import *
from policyengine_uk.variables.household.consumption.rent.non_dependant_normally_resides_with import (
    apportioned_non_dependant_deductions,
)


class housing_benefit_non_dep_deductions(Variable):
    value_type = float
    entity = BenUnit
    label = "non-dependent deductions"
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/3",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/74",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/55",
        "https://assets.publishing.service.gov.uk/media/5a7ce2b840f0b6629523c64c/hbgm-a5-calculating-benefit.pdf",
    )

    def formula(benunit, period, parameters):
        # Deductions are made for non-dependants residing with the claimant
        # (HB Regs 2006 reg 74; HB (SPC) Regs 2006 reg 55). Joint occupiers,
        # boarders, lodgers and the landlord's household are not
        # non-dependants (reg 3(2)(d)-(e), 3(4)). A non-dependant of more
        # than one joint occupier is apportioned between them by their shares
        # of the payments (reg 74(5); SPC reg 55(5)); one who resides with
        # only one joint occupier is deducted in full from that occupier's
        # award (HB Guidance Manual A5 para 5.622). Which joint occupiers a
        # non-dependant resides with is non_dependant_normally_resides_with;
        # a boarder or lodger bears none.
        person = benunit.members
        deductions = person(
            "household_benefits_individual_non_dep_deduction", period
        ) * person("is_non_dependant_of_household_head", period)
        return apportioned_non_dependant_deductions(
            benunit, period, deductions, equally=False
        )
