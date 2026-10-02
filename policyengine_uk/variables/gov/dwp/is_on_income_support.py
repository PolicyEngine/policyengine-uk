from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.dwp._legacy_award_payee import (
    is_payee_of_couple_award,
)


class is_on_income_support(Variable):
    value_type = bool
    entity = Person
    label = "on Income Support"
    documentation = (
        'Whether this person is in receipt of Income Support ("person on '
        'income support", HB Regs 2006 reg 2(1); the council tax reduction '
        "schemes use the same definition). Income Support is calculated for "
        "the claimant's family and needs the claimant's or partner's own "
        "award (income_support_eligible). It is paid to the claimant, not "
        "the partner: of the claimant and partner, only the payee is in "
        "receipt, meaning the one who reports it, or the claimant where "
        "neither does, and only while it is positive. Any other member of the "
        "benefit unit, such as a non-dependent adult, claims in their own "
        "right and is on it only if they report an award themselves while "
        "Income Support is in payment and no reform removes it."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/2",
        "https://www.legislation.gov.uk/uksi/2012/2885/regulation/2",
    )

    def formula(person, period, parameters):
        active = parameters(period).gov.dwp.income_support.active
        removed = person.simulation.tax_benefit_system.get_variable(
            "income_support"
        ).is_neutralized
        couple_award = (person.benunit("income_support", period) > 0) & (
            is_payee_of_couple_award(person, period, "income_support_reported")
        )
        # Their own report, while Income Support is in payment and no reform
        # removes it. The model calculates the award only for the claimant
        # and partner, so it cannot gate another member's own claim.
        own_award = (
            active & (not removed) & (person("income_support_reported", period) > 0)
        )
        return where(person("is_claimant_or_partner", period), couple_award, own_award)
