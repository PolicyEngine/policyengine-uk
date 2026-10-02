from policyengine_uk.model_api import *


class pension_contributions_via_salary_sacrifice_from_pay(Variable):
    label = "Salary sacrifice pension contributions limited to pay"
    documentation = (
        "Salary sacrifice pension contributions limited to the pay they are "
        "sacrificed from. A salary sacrifice is pay given up in exchange for "
        "an employer pension contribution, so a person without pay sacrifices "
        "nothing, and the model allows no sacrifice above the pay the person "
        "still receives (employment income before labour supply responses, "
        "which is net of the sacrifice). The cap on salary sacrifice returns "
        "the excess over the cap to employment income, so without this limit "
        "an input sacrifice with no pay behind it would create pay."
    )
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(person, period, parameters):
        sacrifice = person("pension_contributions_via_salary_sacrifice", period)
        pay = person("employment_income_before_lsr", period)
        return min_(max_(sacrifice, 0), max_(pay, 0))
