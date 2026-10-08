from policyengine_uk.model_api import *


class housing_benefit_remunerative_work(Variable):
    value_type = bool
    entity = Person
    definition_period = YEAR
    label = "housing benefit non dep remunerative work"
    documentation = "Remunerative work under HB regulation 6: normally at least 16 hours a week, for payment or expected payment. Override the earnings/hours fallback for statutory exceptions and averaged or irregular hours."
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/74",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/55",
        "https://www.legislation.gov.uk/nisr/2006/405/regulation/72",
        "https://www.legislation.gov.uk/nisr/2006/406/regulation/53",
    )

    def formula(person, period, parameters):
        p = parameters(period).gov.dwp.housing_benefit.means_test.childcare
        paid = (
            add(person, period, ["employment_income", "self_employment_income"]) > 0
        ) | person("housing_benefit_paid_work_expected", period)
        return (person("weekly_hours", period) >= p.work_hours) & paid
