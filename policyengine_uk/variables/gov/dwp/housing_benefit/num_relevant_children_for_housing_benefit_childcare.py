from policyengine_uk.model_api import *


class num_relevant_children_for_housing_benefit_childcare(Variable):
    """Children whose ages permit relevant Housing Benefit childcare charges.

    Regulation 28(6) ends eligibility on the day before the first Monday
    in September after the fifteenth birthday (sixteenth if disabled).
    Annual integer ages approximate this with exclusive limits of 16 and
    17. The legacy-benefit family definition excludes claimants/partners.
    Per-child charges are unobserved, so eligible children stand in for
    children in respect of whom charges are paid under regulation 27(3).
    Disability uses the existing benefits-disability input or blindness;
    historic certification and suspended-payment cases are unobserved.
    """

    value_type = int
    entity = BenUnit
    label = "Relevant children for Housing Benefit childcare charges"
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/27",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/28",
    )

    def formula(benunit, period, parameters):
        person = benunit.members
        p = parameters(
            period
        ).gov.dwp.housing_benefit.means_test.childcare.child_age_limit
        child_or_young_person = person(
            "is_child_or_young_person_for_legacy_benefits", period
        )
        disabled = person("is_disabled_for_benefits", period) | person(
            "is_blind", period
        )
        age_limit = where(disabled, p.disabled, p.standard)
        return benunit.sum(child_or_young_person & (person("age", period) < age_limit))
