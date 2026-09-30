from policyengine_uk.model_api import *


class receives_severe_disability_premium_qualifying_benefit(Variable):
    value_type = bool
    entity = Person
    label = "Receives a severe disability premium qualifying benefit"
    documentation = (
        "In receipt of a benefit that makes a claimant or partner severely "
        "disabled for the legacy severe disability premium: attendance "
        "allowance (either rate), the care component of disability living "
        "allowance at the highest or middle rate, the daily living component "
        "of personal independence payment at either rate, or armed forces "
        "independence payment. The same receipt makes a non-dependant "
        "ignored in the premium's residence condition. Armed Forces "
        "Compensation Scheme payments other than armed forces independence "
        "payment do not qualify. The Scottish equivalents (adult disability "
        "payment, pension age disability payment and Scottish adult "
        "disability living allowance) are not separate model variables, and "
        "the hospital and concessionary-payment rules are not modelled."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/3/paragraph/14",
        "https://www.legislation.gov.uk/uksi/1987/1967/schedule/2/paragraph/13",
        "https://www.legislation.gov.uk/uksi/2008/794/schedule/4/paragraph/6",
        "https://www.legislation.gov.uk/uksi/1996/207/schedule/1/paragraph/15",
    )

    def formula(person, period, parameters):
        p = parameters(period).gov.dwp.disability_premia
        return add(person, period, p.severe_qualifying_benefits) > 0
