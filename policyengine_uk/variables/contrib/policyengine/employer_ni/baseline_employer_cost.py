from policyengine_uk.model_api import *


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
                "statutory_sick_pay",
                "statutory_maternity_pay",
                "statutory_paternity_pay",
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
