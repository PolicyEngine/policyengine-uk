from policyengine_uk.model_api import *


class is_in_remunerative_work_for_child_tax_credit(Variable):
    value_type = bool
    entity = Person
    label = "In remunerative work for Child Tax Credit"
    documentation = (
        "Whether the person works at least 24 hours a week for payment or in "
        "expectation of payment (Child Tax Credit Regulations 2002 reg. "
        "2(1)), read from average weekly hours over the year. The Working "
        "Tax Credit rules the definition refers to, for counting hours and "
        "for excluded work, are not modelled."
    )
    definition_period = YEAR
    reference = "https://www.legislation.gov.uk/uksi/2002/2007/regulation/2"

    def formula(person, period, parameters):
        p = parameters(period).gov.dwp.tax_credits.child_tax_credit.eligibility
        return person("weekly_hours", period) >= p.remunerative_work_hours
