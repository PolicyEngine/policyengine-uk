from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.dwp.universal_credit.legacy_benefits_closed import (
    legacy_award_is_closed,
)


class person_legacy_benefits_closed(Variable):
    value_type = bool
    entity = Person
    label = "Legacy benefits closed for this person's award"
    documentation = (
        "The existing annual legacy-closure proxy, scoped to the award owner. "
        "The claimant and partner share legacy_benefits_closed. Other members "
        "claiming in their own right use only their own reports and Pension "
        "Credit qualifying age. Their reports neither close nor shield the "
        "couple's award, and the couple's reports do not close theirs. No new "
        "notice, deadline, run-on or legal relationship inference is made."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2014/1230/regulation/44",
        "https://www.legislation.gov.uk/uksi/2014/1230/regulation/46",
    )

    def formula(person, period, parameters):
        def reports(*variables):
            return sum(person(name, period) for name in variables) > 0

        pension_age = person("has_attained_state_pension_credit_qualifying_age", period)
        own_closed = legacy_award_is_closed(
            reports, pension_age, pension_age & False, parameters(period).gov.dwp
        )
        return where(
            person("is_claimant_or_partner", period),
            person.benunit("legacy_benefits_closed", period),
            own_closed,
        )
