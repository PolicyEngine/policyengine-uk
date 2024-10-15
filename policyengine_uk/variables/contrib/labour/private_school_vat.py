from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.hmrc.tax import household_tax


class attends_private_school(Variable):
    label = "attends private school"
    entity = Person
    definition_period = YEAR
    value_type = bool

    def formula(person, period, parameters):
        household = person.household
        # To ensure that our model matches
        # total number of students actually enrolled

        ps_vat_params = parameters(period).gov.simulation.private_school_vat
        private_school_attendance_rate = (
            ps_vat_params.private_school_attendance_rate
        )

        population_adjustment_factor = ps_vat_params.private_school_factor

        person = household.members

        is_child = person("is_child", period)

        taxes = household.sum(
            person("income_tax", period) + person("national_insurance", period)
        )

        net_income = (
            household("household_market_income", period)
            + household("household_benefits", period)
            - taxes
        )

        household_weight = household("household_weight", period)
        weighted_income = MicroSeries(net_income, weights=household_weight)

        percentile = np.zeros_like(weighted_income).astype(numpy.int64)
        mask = household_weight > 0

        percentile[mask] = (
            weighted_income[mask]
            .percentile_rank()
            .clip(0, 100)
            .values.astype(numpy.int64)
        )
        # STUDENT_POPULATION_ADJUSTMENT_FACTOR = 0.78
        STUDENT_POPULATION_ADJUSTMENT_FACTOR = population_adjustment_factor

        p_attends_private_school = (
            np.array(
                [
                    interpolate_percentile(private_school_attendance_rate, p)
                    for p in percentile
                ]
            )
            * STUDENT_POPULATION_ADJUSTMENT_FACTOR
            * is_child
        )

        return random(person) < p_attends_private_school


class private_school_vat(Variable):
    label = "private school VAT"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"

    def formula(household, period, parameters):
        num_children = add(household, period, ["attends_private_school"])

        ps_vat_params = parameters(period).gov.simulation.private_school_vat
        private_school_vat_basis = ps_vat_params.private_school_vat_basis
        avg_yearly_private_school_cost = ps_vat_params.private_school_fees

        private_school_vat_rate = parameters(
            period
        ).gov.contrib.labour.private_school_vat

        return (
            num_children
            * avg_yearly_private_school_cost
            * private_school_vat_rate
            * private_school_vat_basis
        )


def interpolate_percentile(param, percentile):
    if str(percentile) in param:
        return param[str(percentile)]
    else:
        idx = percentile - (percentile % 5)
        p1 = idx
        p2 = idx + 5
        v1 = param[str(idx)]
        v2 = param[str(idx + 5)]
        return v1 + (v2 - v1) * (percentile - p1) / (p2 - p1)
