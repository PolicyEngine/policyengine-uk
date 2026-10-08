from policyengine_uk.model_api import *


class housing_benefit_meals_deduction(Variable):
    value_type = float
    entity = BenUnit
    label = "Housing Benefit deduction for meals in the rent"
    documentation = (
        "The amount of the rent that is ineligible for Housing Benefit "
        "because it pays for meals: a fixed weekly amount for the claimant "
        "and each family member, by the meals provided and whether the "
        "person is 16 or over."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/1/paragraph/2",
        "https://www.legislation.gov.uk/uksi/2006/214/schedule/1/paragraph/2",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/13",
    )

    def formula(benunit, period, parameters):
        p = parameters(period).gov.dwp.housing_benefit.ineligible_charges.meals
        meals = benunit("meals_included_in_rent", period)
        provision = meals.possible_values
        person = benunit.members
        # Sch 1 para 2(4): a person attains 16 on the first Monday in
        # September after their 16th birthday; annual ages cannot place that
        # date, so the age is used.
        aged_16_or_over = benunit.sum(person("age", period) >= 16)
        under_16 = benunit.sum(person("age", period) < 16)
        members = aged_16_or_over + under_16
        weekly = select(
            [
                meals == provision.AT_LEAST_THREE_A_DAY,
                meals == provision.FEWER_THAN_THREE_A_DAY,
                meals == provision.BREAKFAST_ONLY,
            ],
            [
                aged_16_or_over * p.at_least_three_a_day.aged_16_or_over
                + under_16 * p.at_least_three_a_day.under_16,
                aged_16_or_over * p.fewer_than_three_a_day.aged_16_or_over
                + under_16 * p.fewer_than_three_a_day.under_16,
                members * p.breakfast_only,
            ],
            default=0,
        )
        return weekly * WEEKS_IN_YEAR
