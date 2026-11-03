from policyengine_uk.model_api import *


class tax_free_childcare_treated_as_in_work(Variable):
    value_type = bool
    entity = Person
    label = "treated as in work for tax-free childcare"
    documentation = (
        "Whether this person is in paid work or has an explicitly qualified "
        "regulation 12 temporary absence. Legacy leave flags and statutory-pay "
        "amounts alone do not establish regulation 12's prior-work and "
        "applicable child/account conditions. Regulation 14 concerns the "
        "connection between childcare costs and work; it does not by itself "
        "establish qualifying paid work for eligibility."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2015/448/regulation/9",
        "https://www.legislation.gov.uk/uksi/2015/448/regulation/12",
        "https://www.legislation.gov.uk/uksi/2015/448/regulation/14",
    )

    def formula(person, period, parameters):
        # Reg 12(2)(a) and (b) share the conditions in (3) and (4).
        # The explicit status covers them; a legacy leave/pay fact does not.
        return person("in_work", period) | person(
            "tax_free_childcare_qualifying_temporary_absence", period
        )
