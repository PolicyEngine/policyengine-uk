from policyengine_uk.model_api import *


class is_severely_disabled_for_carers_allowance(Variable):
    value_type = bool
    entity = Person
    label = "Severely disabled person for Carer's Allowance"
    documentation = (
        "A severely disabled person within SSCBA 1992 s.70(2): one for whom "
        "attendance allowance, the care component of disability living "
        "allowance at the highest or middle rate, the daily living component "
        "of personal independence payment, or armed forces independence "
        "payment is payable. A carer benefit can only be paid for caring for "
        "such a person. The Scottish equivalents, which Carer Support Payment "
        "also accepts, are not separate model variables, and the constant "
        "attendance allowances prescribed by the Invalid Care Allowance "
        "Regulations 1976 reg 3 are not modelled."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/ukpga/1992/4/section/70",
        "https://www.legislation.gov.uk/uksi/1976/409/regulation/3",
    )

    def formula(person, period, parameters):
        p = parameters(period).gov.dwp.carers_allowance
        return add(person, period, p.qualifying_disability_benefits) > 0
