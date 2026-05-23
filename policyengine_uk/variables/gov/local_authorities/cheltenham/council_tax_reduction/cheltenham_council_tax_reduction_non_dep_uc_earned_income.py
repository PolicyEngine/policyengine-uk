from policyengine_uk.model_api import *


class cheltenham_council_tax_reduction_non_dep_uc_earned_income(Variable):
    value_type = float
    entity = Person
    label = "Cheltenham Council Tax Support non-dependant Universal Credit assessed earned income"
    documentation = "Source input for person-level earned income used in the non-dependant's Universal Credit award calculation."
    definition_period = YEAR
    unit = GBP
    reference = "https://democracy.cheltenham.gov.uk/documents/s53359/Appendix%209%20-%20Council%20270226%20Council%20Tax%20Support%20Scheme%20for%20Working%20Age%20Customers%202026-27%20Final.pdf"

    def formula(person, period, parameters):
        return person("employment_income", period) + person(
            "self_employment_income", period
        )
