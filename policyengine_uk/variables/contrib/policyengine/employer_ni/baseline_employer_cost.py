from policyengine_uk.model_api import *
from policyengine_uk.utils.employer_ni import secondary_class_1_threshold


class baseline_employer_cost(Variable):
    label = "baseline employer cost"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(person, period, parameters):
        prior_employment_income = person("employment_income_before_lsr", period)
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
        if person.simulation.baseline is None:
            return 0
        baseline_parameters = person.simulation.baseline.tax_benefit_system.parameters(
            period
        )
        baseline_class_1 = baseline_parameters.gov.hmrc.national_insurance.class_1
        r_b = baseline_class_1.employer_scale.components[1].rate
        # The secondary threshold, or the UST/AUST where a zero rate applies.
        t_b = secondary_class_1_threshold(person, period, baseline_class_1)
        p_b = baseline_parameters.gov.contrib.policyengine.employer_ni.exempt_employer_pension_contributions
        pen_con_subtracted_b = employer_pension_contributions
        if p_b:
            pen_con_subtracted_b = employer_pension_contributions
        else:
            pen_con_subtracted_b = 0

        baseline_employer_ni = r_b * max_(
            0, ni_class_1_income - pen_con_subtracted_b - t_b
        )
        return ni_class_1_income + baseline_employer_ni
