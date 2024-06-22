from policyengine_uk.model_api import *


class private_school_vat(Variable):
    label = "private school VAT"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"

    def formula(household, period, parameters):

        # To ensure that our model matches
        # total number of students actually enrolled
        STUDENT_POPULATION_ADJUSTMENT_FACTOR = 1.0586

        # Per IFS article
        # (https://ifs.org.uk/publications/tax-private-school-fees-and-state-school-spending),
        # about 25% of private school costs would be
        # effectively VAT-free
        EFFECTIVE_RATE_FACTOR = 0.75

        private_school_vat_rate = parameters(
            period
        ).gov.contrib.labour.private_school_vat

        avg_yearly_private_school_cost = parameters(
            period
        ).calibration.programs.private_school_vat.private_school_fees

        income = household("household_market_income", period)
        count_people = household("household_count_people", period)
        household_weight = household("household_weight", period)
        weighted_income = MicroSeries(
            income, weights=household_weight * count_people
        )
        percentile = weighted_income.percentile_rank().values.astype(
            numpy.int64
        )

        attends_private_school = (
            random(household)
            < parameters(
                period
            ).calibration.programs.private_school_vat.private_school_attendance_rate[
                percentile - (percentile % 5)
            ]
        )
        num_children = add(household, period, ["is_child"])

        return (
            attends_private_school
            * num_children
            * avg_yearly_private_school_cost
            * private_school_vat_rate
            * STUDENT_POPULATION_ADJUSTMENT_FACTOR
            * EFFECTIVE_RATE_FACTOR
        )
