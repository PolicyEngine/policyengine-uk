from policyengine_uk.model_api import *


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
    )

    def formula(benunit, period, parameters):
        # Deductions are made for non-dependants residing with the claimant
        # (HB Regs 2006 reg 74; HB (SPC) Regs 2006 reg 55). Joint occupiers,
        # boarders, lodgers and the landlord's household are not
        # non-dependants (reg 3(2)(d)-(e), 3(4)). A non-dependant of more
        # than one joint occupier is apportioned between them by their shares
        # of the payments (reg 74(5); SPC reg 55(5)), so each family liable
        # for the household's rent bears its share; a boarder or lodger bears
        # none.
        person = benunit.members
        deductions = person(
            "household_benefits_individual_non_dep_deduction", period
        ) * person("is_non_dependant_of_household_head", period)
        share = benunit("share_of_household_rent", period)
        # No deduction at all if the claimant or partner is blind or receives
        # a listed disability benefit (reg 74(6); SPC reg 55(6)). The
        # per-person exemptions in reg 74(7)-(8) (students, under-25s on
        # income-based benefits, patients, armed forces) are not modelled.
        exempt = benunit("housing_benefit_non_dep_deduction_exempt", period)
        return where(exempt, 0, share * benunit.max(person.household.sum(deductions)))
