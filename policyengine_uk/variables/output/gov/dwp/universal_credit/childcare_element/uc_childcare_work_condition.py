from policyengine_uk.model_api import *


class uc_childcare_work_condition(Variable):
    value_type = bool
    entity = BenUnit
    label = "Meets Universal Credit childcare work condition"
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/32/2020-04-06"
    )

    def formula(benunit, period, parameters):
        person = benunit.members
        adult = person("is_adult", period)
        in_work = person("in_work", period)
        adults_in_work = adult & in_work
        # Benefit unit must not have any adults not in work.
        return benunit.any(adults_in_work)
