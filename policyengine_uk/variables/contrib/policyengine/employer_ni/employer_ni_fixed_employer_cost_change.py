from policyengine_uk.model_api import *


class employer_cost(Variable):
    label = "employer cost"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(person, period, parameters):
        benefits = add(
            person,
            period,
            [
                "household_statutory_sick_pay",
                "household_statutory_maternity_pay",
                "household_statutory_paternity_pay",
            ],
        )
        return (
            person("employment_income", period)
            + person("ni_employer", period)
            + person("employer_pension_contributions", period)
            + benefits
        )


class baseline_employer_cost(Variable):
    label = "baseline employer cost"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(person, period, parameters):
        prior_employment_income = person(
            "employment_income_before_lsr", period
        )
        employment_income_behavioral_response = person(
            "employment_income_behavioral_response", period
        )
        benefits = add(
            person,
            period,
            [
                "household_statutory_sick_pay",
                "household_statutory_maternity_pay",
                "household_statutory_paternity_pay",
            ],
        )
        employer_pension_contributions = person(
            "employer_pension_contributions", period
        )
        ni_class_1_income = (
            prior_employment_income
            + employment_income_behavioral_response
            + benefits
            + employer_pension_contributions
        )

        # Calculate baseline employer cost
        baseline_parameters = parameters(period).baseline
        baseline_class_1 = (
            baseline_parameters.gov.hmrc.national_insurance.class_1
        )
        r_b = baseline_class_1.rates.employer
        t_b = baseline_class_1.thresholds.secondary_threshold * WEEKS_IN_YEAR
        p_b = (
            baseline_parameters.gov.contrib.policyengine.employer_ni.exempt_employer_pension_contributions
        )
        pen_con_subtracted_b = employer_pension_contributions
        if p_b:
            pen_con_subtracted_b = employer_pension_contributions
        else:
            pen_con_subtracted_b = 0

        baseline_employer_ni = r_b * max_(
            0, ni_class_1_income - pen_con_subtracted_b - t_b
        )
        return ni_class_1_income + baseline_employer_ni


class adjusted_employer_cost(Variable):
    label = "employer cost"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(person, period, parameters):
        employment_income = person("employment_income", period)
        benefits = add(
            person,
            period,
            [
                "household_statutory_sick_pay",
                "household_statutory_maternity_pay",
                "household_statutory_paternity_pay",
            ],
        )
        employer_pension_contributions = person(
            "employer_pension_contributions", period
        )
        ni_class_1_income = (
            employment_income + benefits + employer_pension_contributions
        )

        # Calculate employer cost
        parameters = parameters(period)
        class_1 = parameters.gov.hmrc.national_insurance.class_1
        r_r = class_1.rates.employer
        t_r = class_1.thresholds.secondary_threshold * WEEKS_IN_YEAR
        p_r = (
            parameters.gov.contrib.policyengine.employer_ni.exempt_employer_pension_contributions
        )
        pen_con_subtracted_r = employer_pension_contributions
        if p_r:
            pen_con_subtracted_r = employer_pension_contributions
        else:
            pen_con_subtracted_r = 0

        employer_ni = r_r * max_(
            0, ni_class_1_income - pen_con_subtracted_r - t_r
        )
        return ni_class_1_income + employer_ni


class employer_ni_response_consumer_incidence(Variable):
    label = "price response to employer NI reform"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(person, period, parameters):
        consumer_incidence = parameters(
            period
        ).gov.contrib.policyengine.employer_ni.consumer_incidence
        if consumer_incidence == 0:
            return 0

        if not hasattr(person.simulation, "dataset"):
            # In single-household simulations, we can't automatically put revenue into price increases because we don't know the revenue.
            return 0

        person_weight = person("person_weight", period)
        baseline_employer_cost = person("baseline_employer_cost", period)
        employer_cost = person("adjusted_employer_cost", period)
        change_in_employer_cost = employer_cost - baseline_employer_cost
        amount_paid_by_employers = (
            person_weight * change_in_employer_cost
        ).sum()

        consumption = (
            person.household("consumption", period)
            / person.household.nb_persons()
        )
        total_consumption = (consumption * person_weight).sum()
        share_of_total_consumption = consumption / total_consumption

        value = (
            amount_paid_by_employers
            * share_of_total_consumption
            * consumer_incidence
        )

        if total_consumption == 0:
            return 0

        return value


class employer_ni_response_capital_incidence(Variable):
    label = "capital response to employer NI reform"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(person, period, parameters):
        capital_incidence = parameters(
            period
        ).gov.contrib.policyengine.employer_ni.capital_incidence
        if capital_incidence == 0:
            return 0

        if not hasattr(person.simulation, "dataset"):
            # In single-household simulations, we can't automatically put revenue into price increases because we don't know the revenue.
            return 0

        person_weight = person("person_weight", period)
        baseline_employer_cost = person("baseline_employer_cost", period)
        employer_cost = person("adjusted_employer_cost", period)
        change_in_employer_cost = employer_cost - baseline_employer_cost
        amount_paid_by_employers = (
            person_weight * change_in_employer_cost
        ).sum()

        wealth = (
            person.household("corporate_wealth", period)
            / person.household.nb_persons()
        )
        total_wealth = (wealth * person_weight).sum()
        share_of_total_wealth = wealth / total_wealth

        value = (
            amount_paid_by_employers
            * share_of_total_wealth
            * capital_incidence
        )

        if total_wealth == 0:
            return 0

        return value


class employer_ni_fixed_employer_cost_change(Variable):
    label = "employer NI reform incidence"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(person, period, parameters):
        employee_incidence = parameters(
            period
        ).gov.contrib.policyengine.employer_ni.employee_incidence
        if employee_incidence == 0:
            return 0
        # First, calculate baseline and reformed employer NI contributions.

        prior_employment_income = person(
            "employment_income_before_lsr", period
        )
        employment_income_behavioral_response = person(
            "employment_income_behavioral_response", period
        )
        benefits = add(
            person,
            period,
            [
                "household_statutory_sick_pay",
                "household_statutory_maternity_pay",
                "household_statutory_paternity_pay",
            ],
        )
        employer_pension_contributions = person(
            "employer_pension_contributions", period
        )
        ni_class_1_income = (
            prior_employment_income
            + employment_income_behavioral_response
            + benefits
            + employer_pension_contributions
        )

        # Calculate baseline employer cost
        baseline_parameters = parameters(period).baseline
        baseline_class_1 = (
            baseline_parameters.gov.hmrc.national_insurance.class_1
        )
        r_b = baseline_class_1.rates.employer
        t_b = baseline_class_1.thresholds.secondary_threshold * WEEKS_IN_YEAR
        p_b = (
            baseline_parameters.gov.contrib.policyengine.employer_ni.exempt_employer_pension_contributions
        )
        pen_con_subtracted_b = employer_pension_contributions
        if p_b:
            pen_con_subtracted_b = employer_pension_contributions
        else:
            pen_con_subtracted_b = 0

        baseline_employer_ni = r_b * (
            ni_class_1_income - pen_con_subtracted_b - t_b
        )
        c_b = ni_class_1_income + baseline_employer_ni

        # Calculate new employment income keeping employer cost constant

        reform_parameters = parameters(period)
        reform_class_1 = reform_parameters.gov.hmrc.national_insurance.class_1
        r_r = reform_class_1.rates.employer
        t_r = reform_class_1.thresholds.secondary_threshold * WEEKS_IN_YEAR
        p_r = (
            reform_parameters.gov.contrib.policyengine.employer_ni.exempt_employer_pension_contributions
        )
        if p_r:
            pen_con_subtracted_r = employer_pension_contributions
        else:
            pen_con_subtracted_r = 0

        new_ni_class_1_income = (c_b + r_r * (pen_con_subtracted_r + t_r)) / (
            1 + r_r
        )

        # Find difference in employment income

        previous_employment_income = (
            ni_class_1_income - benefits
        ) - employer_pension_contributions
        new_employment_income = (
            new_ni_class_1_income - benefits
        ) - employer_pension_contributions

        pay_change = new_employment_income - previous_employment_income

        # Apply incidence percentage

        interpolated_pay_change = pay_change * employee_incidence

        # Where a person's prior employment income was below the secondary threshold, the formula doesn't hold, so assume no change.

        below_threshold = previous_employment_income < t_b

        return where(below_threshold, 0, interpolated_pay_change)
