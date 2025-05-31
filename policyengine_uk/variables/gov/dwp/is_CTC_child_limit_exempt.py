from policyengine_uk.model_api import *


class is_CTC_child_limit_exempt(Variable):
    value_type = bool
    entity = Person
    label = "Exemption from Child Tax Credit child limit"
    documentation = "Exemption from Child Tax Credit limit on number of children based on birth year"
    definition_period = YEAR

    def formula(person, period, parameters):
        limit_year = parameters(
            period
        ).gov.dwp.tax_credits.child_tax_credit.limit.start_year
        # Children must be born before April 2017.
        # We use < 2017 as the closer approximation than <= 2017.
        born_before_limit = person("birth_year", period) < limit_year

        # Reform proposal
        age_exemption = parameters.gov.contrib.two_child_limit.age_exemption.child_tax_credit(
            period
        )
        if age_exemption > 0:
            is_exempt = person.benunit.any(
                person("age", period) < age_exemption
            )
            return born_before_limit | is_exempt

        return born_before_limit
