from policyengine_uk.model_api import *


class pension_contributions_via_salary_sacrifice_from_pay(Variable):
    label = "Salary sacrifice pension contributions of people with pay"
    documentation = (
        "Salary sacrifice pension contributions, counted only for people with "
        "pay. A salary sacrifice is pay given up in exchange for an employer "
        "pension contribution, so a person without pay (employment income "
        "before labour supply responses, which policyengine_uk.Simulation fills "
        "from an employment_income input) has nothing to sacrifice. The "
        "sacrifice is not limited to the pay that remains: an employee may "
        "sacrifice, for example, a whole bonus, as long as their cash pay stays "
        "above the National Minimum Wage. The cap on salary sacrifice returns "
        "the excess over the cap to employment income, so without this "
        "condition an input sacrifice with no pay behind it would create pay."
    )
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = "https://www.gov.uk/guidance/salary-sacrifice-and-the-effects-on-paye"

    def formula(person, period, parameters):
        sacrifice = person("pension_contributions_via_salary_sacrifice", period)
        pay = person("employment_income_before_lsr", period)
        return where(pay > 0, max_(sacrifice, 0), 0)
