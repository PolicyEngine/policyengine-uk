from policyengine_uk.model_api import *


class tax_free_childcare_caring_or_incapacity_benefit(Variable):
    value_type = bool
    entity = Person
    label = "receives a caring or incapacity benefit for Tax-Free Childcare"
    documentation = (
        "Whether this person is paid or entitled to a benefit, allowance or "
        "credit listed in regulation 13(1)(b) of the Childcare Payments "
        "(Eligibility) Regulations 2015, or is on carer's leave (regulation "
        "13(1)(c)). The list is incapacity benefit, severe disablement "
        "allowance, carer's allowance, contributory employment and support "
        "allowance, credits for incapacity or limited capability for work, "
        "and Scottish carer's assistance. Disability Living Allowance and "
        "Personal Independence Payment are not on it."
    )
    definition_period = YEAR
    reference = "https://www.legislation.gov.uk/uksi/2015/448/regulation/13"

    def formula(person, period, parameters):
        p = parameters(period).gov.hmrc.tax_free_childcare
        return add(person, period, p.caring_or_incapacity_benefits) > 0
