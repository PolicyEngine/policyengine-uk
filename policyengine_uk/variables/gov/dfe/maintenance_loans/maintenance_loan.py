import numpy as np

from policyengine_uk.model_api import *
from policyengine_uk.variables.household.demographic.highest_education import (
    EducationType,
)
from policyengine_uk.variables.gov.dfe.maintenance_loans.maintenance_loan_living_arrangement import (
    MaintenanceLoanLivingArrangement,
)


class maintenance_loan(Variable):
    value_type = float
    entity = Person
    label = "Maintenance loan"
    documentation = (
        "Approximate full-time England maintenance loan. "
        "This models the 2025/26 and 2026/27 full-year schedules, including the special-support schedule "
        "and the separate loan-for-living-costs schedule for students aged 60 or over. "
        "It relies on proxy variables for living arrangement and assessed household income when those are not provided explicitly."
    )
    definition_period = YEAR
    unit = GBP

    def formula(person, period, parameters):
        country = person.household("country", period)
        in_england = country == country.possible_values.ENGLAND
        current_education = person("current_education", period)
        in_higher_education = current_education == EducationType.TERTIARY
        age = person("age", period)
        eligible = in_england & in_higher_education & (age >= 18)

        income = person("maintenance_loan_household_income", period)
        living_arrangement = person("maintenance_loan_living_arrangement", period)
        benefits_schedule = person("maintenance_loan_entitled_to_benefits", period)

        p = parameters(period).gov.dfe.maintenance_loans
        threshold = p.household_income.threshold

        full_time_maximum = p.full_time.maximum
        benefit_maximum = p.full_time.maximum_entitled_to_benefits
        living_with_parents = (
            living_arrangement == MaintenanceLoanLivingArrangement.LIVING_WITH_PARENTS
        )
        away_in_london = (
            living_arrangement == MaintenanceLoanLivingArrangement.AWAY_IN_LONDON
        )

        standard_maximum_amount = select(
            [living_with_parents, away_in_london],
            [
                full_time_maximum.living_with_parents,
                full_time_maximum.away_in_london,
            ],
            default=full_time_maximum.away_outside_london,
        )
        benefit_maximum_amount = select(
            [living_with_parents, away_in_london],
            [
                benefit_maximum.living_with_parents,
                benefit_maximum.away_in_london,
            ],
            default=benefit_maximum.away_outside_london,
        )

        not_entitled_taper = p.full_time.taper.not_entitled
        one_stage_taper = select(
            [living_with_parents, away_in_london],
            [
                not_entitled_taper.living_with_parents,
                not_entitled_taper.away_in_london,
            ],
            default=not_entitled_taper.away_outside_london,
        )

        not_entitled_floor_rate = p.full_time.minimum_rate.not_entitled
        one_stage_floor_rate = select(
            [living_with_parents, away_in_london],
            [
                not_entitled_floor_rate.living_with_parents,
                not_entitled_floor_rate.away_in_london,
            ],
            default=not_entitled_floor_rate.away_outside_london,
        )

        entitled_first_stage = p.full_time.taper.entitled_to_benefits.first_stage
        first_stage_taper = select(
            [living_with_parents, away_in_london],
            [
                entitled_first_stage.living_with_parents,
                entitled_first_stage.away_in_london,
            ],
            default=entitled_first_stage.away_outside_london,
        )

        entitled_second_stage = p.full_time.taper.entitled_to_benefits.second_stage
        second_stage_taper = select(
            [living_with_parents, away_in_london],
            [
                entitled_second_stage.living_with_parents,
                entitled_second_stage.away_in_london,
            ],
            default=entitled_second_stage.away_outside_london,
        )

        entitled_floor_rate = p.full_time.minimum_rate.entitled_to_benefits
        two_stage_floor_rate = select(
            [living_with_parents, away_in_london],
            [
                entitled_floor_rate.living_with_parents,
                entitled_floor_rate.away_in_london,
            ],
            default=entitled_floor_rate.away_outside_london,
        )

        one_stage_reduction = max_(0, income - threshold) / one_stage_taper

        higher_threshold = p.household_income.higher_threshold
        first_stage_income = max_(0, min_(income, higher_threshold) - threshold)
        second_stage_income = max_(0, income - higher_threshold)
        two_stage_reduction = (
            first_stage_income / first_stage_taper
            + second_stage_income / second_stage_taper
        )

        standard_amount = where(
            benefits_schedule,
            max_(
                two_stage_floor_rate * benefit_maximum_amount,
                benefit_maximum_amount - two_stage_reduction,
            ),
            max_(
                one_stage_floor_rate * standard_maximum_amount,
                standard_maximum_amount - one_stage_reduction,
            ),
        )

        over_60 = p.over_60
        over_60_reduction = max_(0, income - threshold) / over_60.reduction_per_pound
        over_60_amount = where(
            income > over_60.maximum_income,
            0,
            max_(over_60.minimum_amount, over_60.max_amount - over_60_reduction),
        )

        amount = where(age >= 60, over_60_amount, standard_amount)
        return eligible * np.round(amount, 0)
