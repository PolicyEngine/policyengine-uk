from policyengine_uk.model_api import *


class tax_free_childcare_treated_as_in_work(Variable):
    value_type = bool
    entity = Person
    label = "treated as in work for tax-free childcare"
    definition_period = YEAR
    reference = [
        "https://www.legislation.gov.uk/uksi/2015/448/regulation/12",
        "https://www.legislation.gov.uk/uksi/2015/448/regulation/14",
    ]

    def formula(person, period, parameters):
        statutory_temporary_absence_pay = (
            add(
                person,
                period,
                [
                    "statutory_sick_pay",
                    "maternity_allowance",
                    "statutory_maternity_pay",
                    "statutory_paternity_pay",
                ],
            )
            > 0
        )
        return (
            person("in_work", period)
            | person("tax_free_childcare_on_qualifying_leave", period)
            | person("tax_free_childcare_on_adoption_leave", period)
            | person("tax_free_childcare_on_shared_parental_leave", period)
            | statutory_temporary_absence_pay
        )
