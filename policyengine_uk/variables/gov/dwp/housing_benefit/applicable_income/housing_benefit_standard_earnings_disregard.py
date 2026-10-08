from policyengine_uk.model_api import *


class housing_benefit_standard_earnings_disregard(Variable):
    value_type = float
    entity = BenUnit
    definition_period = YEAR
    unit = GBP
    label = (
        "Housing Benefit earnings disregard before accommodation and additional amounts"
    )
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/4",
        "https://www.legislation.gov.uk/uksi/2006/214/schedule/4",
        "https://www.legislation.gov.uk/nisr/2006/405/schedule/5",
        "https://www.legislation.gov.uk/nisr/2006/406/schedule/5",
    )

    def formula(benunit, period, parameters):
        p = parameters(period).gov.dwp.housing_benefit.means_test.income_disregard
        person = benunit.members
        adult = person("is_claimant_or_partner", period)
        earnings = person("housing_benefit_person_net_earnings", period) * adult
        total = benunit.sum(earnings)
        special = p.special * WEEKS_IN_YEAR
        couple = benunit("is_couple", period)
        lone_parent = benunit("is_lone_parent", period)
        ordinary_limit = where(couple, p.couple, p.single) * WEEKS_IN_YEAR
        ordinary = min_(total, ordinary_limit)
        carer = adult & (
            person("is_entitled_to_carer_benefit", period)
            | person("carer_premium_run_on", period)
        )
        country = person.household("country", period)
        ni = country == country.possible_values.NORTHERN_IRELAND
        occupation = min_(
            earnings,
            max_(
                0,
                person("housing_benefit_specified_occupation_net_earnings", period)
                + ni
                * person(
                    "housing_benefit_ni_additional_occupation_net_earnings", period
                ),
            ),
        )
        other_earnings = benunit.project(benunit.sum(earnings)) - earnings
        other_carer_or_occupation = (
            benunit.project(benunit.sum(carer)) - carer > 0
        ) | (benunit.project(benunit.sum(occupation)) - occupation > 0)
        carer_candidate = min_(
            special,
            earnings
            + where(
                other_carer_or_occupation,
                other_earnings,
                min_(other_earnings, p.couple * WEEKS_IN_YEAR),
            ),
        )
        working_carer = benunit.max(where(carer, carer_candidate, 0))
        # Paragraphs 8–9: restrict own ordinary-job top-up; a partner in a
        # specified occupation can contribute earnings under paragraph 8(2)(a).
        own_top_up = benunit.project(ordinary_limit)
        occupation_candidate = min_(
            special,
            occupation
            + min_(max_(earnings - occupation, 0), own_top_up)
            + where(
                benunit.project(benunit.sum(occupation)) - occupation > 0,
                other_earnings,
                min_(other_earnings, p.couple * WEEKS_IN_YEAR),
            ),
        )
        working_occupation = benunit.max(where(occupation > 0, occupation_candidate, 0))
        disability = (
            (benunit("disability_premium", period) > 0)
            | (benunit("severe_disability_premium", period) > 0)
            | benunit.any(
                adult
                & (
                    person("esa_support_group", period)
                    | person("esa_work_related_activity_group", period)
                )
            )
        )
        working = select(
            [disability, benunit.any(carer), benunit.sum(occupation) > 0],
            [min_(total, special), working_carer, working_occupation],
            default=ordinary,
        )
        pension_disability = benunit.any(
            adult
            & person("housing_benefit_pension_special_disregard_conditions", period)
        )
        pension = select(
            [pension_disability | (benunit.sum(occupation) > 0), benunit.any(carer)],
            [min_(total, special), min_(special, benunit.sum(earnings * carer))],
            default=ordinary,
        )
        standard = where(
            benunit("housing_benefit_pension_age_regulations_apply", period),
            pension,
            working,
        )
        standard = where(
            lone_parent, min_(total, p.lone_parent * WEEKS_IN_YEAR), standard
        )
        permitted = benunit("housing_benefit_permitted_work_disregard", period)
        has_permitted = benunit.any(
            adult & (person("housing_benefit_permitted_work_limit", period) > 0)
        )
        return where(has_permitted, permitted, standard)
