from policyengine_uk.model_api import *


class receives_income_support_in_own_right(Variable):
    value_type = bool
    entity = Person
    label = "Receives Income Support in own right"
    documentation = (
        "Whether this person receives Income Support on a claim of their own. "
        "It ends qualifying young person status for Pension Credit (SPC Regs "
        "2002 reg. 4A(5)); Universal Credit's list (UC Regs 2013 reg. 5(5)) "
        "does not include it. By default it is the person's own reported "
        "Income Support (income_support_reported) while Income Support is in "
        "payment and no reform removes it (neutralizes income_support), as "
        "is_on_income_support reads another member's own claim; set it "
        "directly otherwise. It does not read the benefit unit's calculated "
        "award, which belongs to the claimant and depends on who the family's "
        "young persons are."
    )
    definition_period = YEAR
    reference = "https://www.legislation.gov.uk/uksi/2002/1792/regulation/4A"

    def formula(person, period, parameters):
        active = parameters(period).gov.dwp.income_support.active
        # A reform that removes Income Support leaves no award to receive.
        removed = person.simulation.tax_benefit_system.get_variable(
            "income_support"
        ).is_neutralized
        return active & (not removed) & (person("income_support_reported", period) > 0)
