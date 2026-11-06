from policyengine_uk.model_api import *


class is_in_remunerative_work_for_child_benefit(Variable):
    value_type = bool
    entity = Person
    label = "In remunerative work for Child Benefit"
    documentation = (
        "Whether the person works at least 24 hours a week for payment or in "
        "expectation of payment (Child Benefit (General) Regulations 2006 "
        "reg. 1(3)), read from average weekly hours over the year."
    )
    definition_period = YEAR
    reference = "https://www.legislation.gov.uk/uksi/2006/223/regulation/1"

    def formula(person, period, parameters):
        p = parameters(period).gov.hmrc.child_benefit.eligibility
        return person("weekly_hours", period) >= p.remunerative_work_hours
