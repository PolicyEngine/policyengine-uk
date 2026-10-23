from policyengine_uk.model_api import *


class legacy_benefits_home_letting_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Rent from letting part of the home counted in the legacy means tests"
    documentation = (
        "Rent the claimant and any partner receive for letting part of the home "
        "they live in (sublet_income), after the weekly sub-tenant disregard. "
        "The legacy means tests treat other income derived from capital, such as "
        "rent from other property, interest and dividends, as capital, but the "
        "home is disregarded capital, so rent for part of it stays income: "
        "Income Support Schedule 9 paragraph 19, Housing Benefit Schedule 5 "
        "paragraph 22, and for claimants over the qualifying age for State "
        "Pension Credit Pension Credit regulation 15(5)(i) with Schedule IV "
        "paragraph 9 and pension-age Housing Benefit regulation 29(1)(v) with "
        "Schedule 5 paragraph 10. The disregard applies per occupier; the data "
        "give one annual amount and no count of occupiers, so the model assumes "
        "one. The pension-age amount applies when the claimant or partner is "
        "over State Pension age, which stands in for the qualifying age for "
        "State Pension Credit; the two amounts have been equal since April "
        "2008. The calculation is annual, so a year with an April change uses "
        "the amount in force at the start of the year."
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        "https://www.legislation.gov.uk/uksi/1987/1967/schedule/9/paragraph/19",
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/5/paragraph/22",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/29",
        "https://www.legislation.gov.uk/uksi/2006/214/schedule/5/paragraph/10",
        "https://www.legislation.gov.uk/uksi/2002/1792/regulation/15",
        "https://www.legislation.gov.uk/uksi/2002/1792/schedule/IV/paragraph/9",
    ]

    def formula(benunit, period, parameters):
        p = parameters(period).gov.dwp.legacy_means_tests.sub_tenant_rent_disregard
        person = benunit.members
        claimant_or_partner = person("is_claimant_or_partner", period)
        weekly_rent = (
            benunit.sum(person("sublet_income", period) * claimant_or_partner)
            / WEEKS_IN_YEAR
        )
        pension_age = benunit.any(person("is_SP_age", period) & claimant_or_partner)
        disregard = where(pension_age, p.pension_age, p.working_age)
        return max_(0, weekly_rent - disregard) * WEEKS_IN_YEAR
