from policyengine_uk.model_api import *


class meets_housing_benefit_additional_earnings_disregard_conditions(Variable):
    value_type = bool
    entity = BenUnit
    label = (
        "meets a work condition for the Housing Benefit additional earnings disregard"
    )
    documentation = (
        "Whether the claimant or partner meets one of the work conditions for "
        "the additional earnings disregard: aged at least 25 and working at "
        "least 30 hours a week; a couple with a child or young person, or a "
        "lone parent, with someone working at least 16 hours; or a disabled "
        "claimant or partner working at least 16 hours. Disability uses the "
        "input the model uses for the disability premium. Membership of the "
        "work-related activity group and the support component are not "
        "modelled. Nor is the Working Tax Credit 30 hour element route "
        "(paragraph 17(2)(a) and 9(2)(a)); beyond the routes above it covers "
        "only a couple whose 30-hour worker is under 25 and whose partner is "
        "aged at least 60 and works 16 hours, and a disability that meets the "
        "Working Tax Credit test but not the disability premium one, and no "
        "tax credit can be claimed for 2025-26 onwards. The 50 plus element "
        "route (paragraph 17(2)(c) and 9(2)(c)) ended with the element on 6 "
        "April 2012. The net earnings test is applied in "
        "housing_benefit_applicable_income_disregard. The claimant and "
        "partner are proxied by is_adult (aged 18 or over): members under 18 "
        "are treated as children, but a qualifying young person aged 18 or 19 "
        "is treated as a claimant or partner, so their hours can meet a "
        "condition, until a claimant-or-partner variable "
        "(PolicyEngine/policyengine-uk#1896) replaces the proxy."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/4/paragraph/17",
        "https://www.legislation.gov.uk/uksi/2006/214/schedule/4/paragraph/9",
        "https://www.legislation.gov.uk/nisr/2006/405/schedule/5/paragraph/17",
        "https://www.legislation.gov.uk/nisr/2006/406/schedule/5/paragraph/9",
    )

    def formula(benunit, period, parameters):
        p = parameters(period).gov.dwp.housing_benefit.means_test.income_disregard
        person = benunit.members
        # The claimant and partner; the model's other Housing Benefit
        # variables use the same proxy. It counts a qualifying young person
        # aged 18 or 19 as an adult (#1896).
        claimant_or_partner = person("is_adult", period)
        hours = person("weekly_hours", period)
        works_hours = claimant_or_partner & (hours >= p.worker_hours)
        works_lower_hours = claimant_or_partner & (hours >= p.worker_hours_lower)
        # Para 17(2)(b)(i) and 9(2)(b)(i): one person meets both tests.
        aged_worker = benunit.any(works_hours & (person("age", period) >= p.worker_age))
        # Para 17(2)(b)(ii)-(iii) and 9(2)(b)(ii)-(iii).
        has_child = benunit.any(~claimant_or_partner)
        family_with_child = (benunit("is_couple", period) & has_child) | benunit(
            "is_lone_parent", period
        )
        family_worker = family_with_child & benunit.any(works_lower_hours)
        # Para 17(2)(b)(iv)-(v) and 9(2)(b)(iv): the disabled person works.
        disabled_worker = benunit.any(
            works_lower_hours & person("is_disabled_for_benefits", period)
        )
        return aged_worker | family_worker | disabled_worker
