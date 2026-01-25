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
        return person("birth_year", period) < limit_year
