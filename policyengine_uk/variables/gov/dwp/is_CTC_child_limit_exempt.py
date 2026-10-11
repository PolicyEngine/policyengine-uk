from policyengine_uk.model_api import *
from policyengine_uk.utils.dates import birth_day


class is_CTC_child_limit_exempt(Variable):
    value_type = bool
    entity = Person
    label = "Exemption from Child Tax Credit child limit"
    documentation = (
        "Whether the Child Tax Credit child limit does not apply to this child "
        "or qualifying young person because they were born before 6 April 2017."
    )
    definition_period = YEAR
    reference = "https://www.legislation.gov.uk/ukpga/2002/21/section/9"

    def formula(person, period, parameters):
        limit = parameters(period).gov.dwp.tax_credits.child_tax_credit.limit
        # Tax Credits Act 2002 s.9(3A): the limit applies to a child or
        # qualifying young person born on or after 6 April 2017.
        born_before_limit = birth_day(person, period) < limit.born_before

        # Reform proposal
        age_exemption = (
            parameters.gov.contrib.two_child_limit.age_exemption.child_tax_credit(
                period
            )
        )
        if age_exemption > 0:
            is_exempt = person.benunit.any(person("age", period) < age_exemption)
            return born_before_limit | is_exempt

        return born_before_limit
