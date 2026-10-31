from policyengine_uk.model_api import *


class is_CTC_child_limit_own_exception(Variable):
    value_type = bool
    entity = Person
    label = "Child Tax Credit child limit exception of this child's own"
    documentation = (
        "Whether any of the multiple births, adoption, non-parental caring "
        "arrangements, non-consensual conception or continuation exceptions "
        "(Child Tax Credit Regulations 2002 regs 10 to 14) applies to this "
        "child or qualifying young person. It applies whatever their place in "
        "the order of children."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2002/2007/regulation/10/2025-04-06",
        "https://www.legislation.gov.uk/uksi/2002/2007/regulation/11/2025-04-06",
        "https://www.legislation.gov.uk/uksi/2002/2007/regulation/12/2025-04-06",
        "https://www.legislation.gov.uk/uksi/2002/2007/regulation/13/2025-04-06",
        "https://www.legislation.gov.uk/uksi/2002/2007/regulation/14/2025-04-06",
    )

    def formula(person, period, parameters):
        is_ctc_child = person(
            "is_child_or_qualifying_young_person_for_child_tax_credit", period
        )
        return is_ctc_child & (
            person("child_limit_multiple_birth_exception", period)
            | person("child_limit_adoption_exception", period)
            | person("child_limit_non_parental_caring_exception", period)
            | person("child_limit_non_consensual_conception_exception", period)
            | person("child_limit_continuation_exception", period)
        )
