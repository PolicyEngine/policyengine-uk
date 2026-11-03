from policyengine_uk.model_api import *


class receives_income_support_in_own_right(Variable):
    value_type = bool
    entity = Person
    label = "Receives Income Support in own right"
    documentation = (
        "Whether this person receives Income Support on a claim of their own, "
        "as the Child Benefit qualifying young person test reads it (Child "
        "Benefit (General) Regulations 2006 reg. 8(2)(a)); through that test "
        "it also ends the Housing Benefit and legacy young person. It is the "
        "person's own reported Income Support (income_support_reported) "
        "while Income Support is in payment (gov.dwp.income_support.active) "
        "and no reform neutralises income_support; set it directly otherwise. "
        "For a member who is not the claimant or partner, "
        "is_on_income_support reads the same report. For a claimant or "
        "partner, is_on_income_support reads the benefit unit's calculated "
        "award, for whichever of the claimant and partner receives it, but "
        "that award depends on who the family's Child Benefit young persons "
        "are, so this variable cannot read it without a cycle. A reform that "
        "removes Income Support must set gov.dwp.income_support.active to "
        "false, neutralise income_support, or set reported awards to zero, "
        "for the Child Benefit status to follow; replacing its formula with "
        "zero leaves this variable true. Pension Credit (SPC Regs 2002 reg. "
        "4A(5)) reads is_on_income_support instead, so it follows such a "
        "reform for a claimant or partner. Universal Credit's list (UC Regs "
        "2013 reg. 5(5)) does not include Income Support."
    )
    definition_period = YEAR
    reference = "https://www.legislation.gov.uk/uksi/2006/223/regulation/8"

    def formula(person, period, parameters):
        active = parameters(period).gov.dwp.income_support.active
        # A reform that removes Income Support leaves no award to receive.
        removed = person.simulation.tax_benefit_system.get_variable(
            "income_support"
        ).is_neutralized
        return active & (not removed) & (person("income_support_reported", period) > 0)
