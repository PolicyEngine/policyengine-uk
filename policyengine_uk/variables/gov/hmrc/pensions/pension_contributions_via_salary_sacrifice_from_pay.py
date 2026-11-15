from policyengine_uk.model_api import *


class pension_contributions_via_salary_sacrifice_from_pay(Variable):
    label = "Salary and bonus sacrifice pension contributions of people with pay"
    documentation = (
        "Salary sacrifice and bonus sacrifice pension contributions, counted "
        "only for people with pay. The rules treat the two routes alike and the "
        "NICs exemption cap applies to their sum, so the cap, the NICs excess "
        "and the annual allowance tests all read this total. A salary "
        "sacrifice is pay given up in exchange for an employer "
        "pension contribution, so a person without pay (employment income "
        "before labour supply responses, which policyengine_uk.Simulation fills "
        "from an employment_income input) has nothing to sacrifice. The "
        "sacrifice is not limited to the pay that remains: an employee may "
        "sacrifice, for example, a whole bonus, as long as their cash pay stays "
        "above the National Minimum Wage. The cap includes excess sacrifice "
        "only in NIC earnings. Without this pay condition a sacrifice "
        "input with no pay behind it would create a NIC earnings base. A "
        "negative input counts as none."
    )
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = "https://www.gov.uk/guidance/salary-sacrifice-and-the-effects-on-paye"

    def formula(person, period, parameters):
        salary = person("pension_contributions_via_salary_sacrifice", period)
        bonus = person("pension_contributions_via_bonus_sacrifice", period)
        pay = person("employment_income_before_lsr", period)
        return where(pay > 0, max_(salary, 0) + max_(bonus, 0), 0)
