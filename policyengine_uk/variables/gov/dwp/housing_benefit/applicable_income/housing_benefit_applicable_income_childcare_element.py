from policyengine_uk.model_api import *


def hb_capped_childcare_charges(benunit, period, parameters):
    """Qualifying paid care only; one-child or multiple-child family cap."""
    person = benunit.members
    charges = max_(person("housing_benefit_qualifying_childcare_charges", period), 0)
    included = person("is_child_or_young_person_for_legacy_benefits", period)
    count = benunit.sum(included & (charges > 0))
    p = parameters(period).gov.dwp.tax_credits.working_tax_credit.elements
    cap = select([count == 1, count > 1], [p.childcare_1, p.childcare_2], default=0)
    return min_(benunit.sum(charges * included), cap * WEEKS_IN_YEAR)


class housing_benefit_applicable_income_childcare_element(Variable):
    value_type = float
    entity = BenUnit
    label = "Housing Benefit applicable income childcare element"
    definition_period = YEAR
    unit = GBP
    documentation = (
        "Qualifying pre-assessed charges, capped by the number of included "
        "children with paid care and by remaining earnings plus WTC/CTC "
        "payments. Provider/work/age and continuation conditions are delegated "
        "to housing_benefit_qualifying_childcare_charges. Generic "
        "childcare_expenses are not treated as qualifying by default. The "
        "annual calculation assumes constant household circumstances."
    )
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/27",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/30",
        "https://www.legislation.gov.uk/nisr/2006/405/regulation/25",
        "https://www.legislation.gov.uk/nisr/2006/406/regulation/28",
    )

    def formula(benunit, period, parameters):
        return min_(
            hb_capped_childcare_charges(benunit, period, parameters),
            benunit("housing_benefit_childcare_earnings_limit", period),
        )
