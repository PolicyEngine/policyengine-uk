from policyengine_uk.model_api import *


def hb_capped_childcare_charges(benunit, period, parameters):
    """Aggregate childcare spending capped using the existing age-based count."""
    expenses = max_(add(benunit, period, ["childcare_expenses"]), 0)
    count = benunit("num_relevant_children_for_housing_benefit_childcare", period)
    p = parameters(period).gov.dwp.tax_credits.working_tax_credit.elements
    cap = select([count == 1, count > 1], [p.childcare_1, p.childcare_2], default=0)
    return min_(expenses, cap * WEEKS_IN_YEAR)


class housing_benefit_applicable_income_childcare_element(Variable):
    value_type = float
    entity = BenUnit
    label = "Housing Benefit applicable income childcare element"
    definition_period = YEAR
    unit = GBP
    documentation = (
        "Aggregate childcare_expenses, capped using the existing age-eligible "
        "child count and limited by remaining earnings plus WTC/CTC payments. "
        "Provider eligibility, excluded charge types, work/leave conditions "
        "and incapacity/continuation exceptions are not assessed. The child "
        "count approximates children with paid care and can overstate the "
        "cap when only one of several eligible children receives paid care. "
        "These qualifying-care rules are deferred in "
        "https://github.com/PolicyEngine/policyengine-uk/issues/2236. "
        "The annual calculation assumes constant household circumstances."
    )
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/27",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/30",
        "https://www.legislation.gov.uk/nisr/2006/405/regulation/24",
        "https://www.legislation.gov.uk/nisr/2006/406/regulation/28",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/28",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/31",
        "https://www.legislation.gov.uk/nisr/2006/405/regulation/25",
        "https://www.legislation.gov.uk/nisr/2006/406/regulation/29",
    )

    def formula(benunit, period, parameters):
        return min_(
            hb_capped_childcare_charges(benunit, period, parameters),
            benunit("housing_benefit_childcare_earnings_limit", period),
        )
