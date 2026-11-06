from policyengine_uk.model_api import *


class meets_qualifying_young_person_extension_period_condition_for_child_benefit(
    Variable
):
    value_type = bool
    entity = Person
    label = "Meets qualifying young person extension period condition for Child Benefit"
    documentation = (
        "A person under 18 who has left education or training, is registered "
        "with a qualifying body and is not in remunerative work, for the 20 "
        "weeks of the extension period their parent or carer asked for."
    )
    definition_period = YEAR
    reference = "https://www.legislation.gov.uk/uksi/2006/223/regulation/5"

    def formula(person, period, parameters):
        p = parameters(period).gov.hmrc.child_benefit.eligibility
        return (
            (person("age", period) < p.extension_period_age_limit)
            & person("is_in_child_benefit_extension_period", period)
            & ~person("is_in_remunerative_work_for_child_benefit", period)
        )
