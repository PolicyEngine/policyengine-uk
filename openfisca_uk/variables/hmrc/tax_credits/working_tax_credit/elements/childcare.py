from openfisca_uk.model_api import *


class wtc_childcare_element(Variable):
    value_type = float
    entity = BenUnit
    label = "Working Tax Credit childcare element"
    definition_period = YEAR
    unit = "currency-GBP"
    reference = "https://www.legislation.gov.uk/uksi/2002/2005/part/2/crossheading/child-care-element"

    def formula(benunit, period, parameters):
        wtc = parameters(period).benefit.tax_credits.working_tax_credit
        person = benunit.members
        is_adult = person("is_adult", period)
        works_lower_hours = person("weekly_hours", period) >= wtc.eligibility.work_requirements.lower
        meets_additional_work_condition = ~(benunit.sum(is_adult & ~works_lower_hours) > 0)
        num_children = benunit("num_children", period)
        maximum = wtc.elements.childcare.maximum
        max_weekly_childcare = where(num_children == 1, maximum.single, maximum.multiple)
        max_childcare_amount = max_weekly_childcare * WEEKS_IN_YEAR
        # Reg. 15 directs to round childcare expenses upwards
        expenses = np.ceil(aggr(benunit, period, ["childcare_expenses"]))
        eligible_expenses = min_(max_childcare_amount, expenses) * meets_additional_work_condition
        return wtc.elements.childcare.coverage * eligible_expenses