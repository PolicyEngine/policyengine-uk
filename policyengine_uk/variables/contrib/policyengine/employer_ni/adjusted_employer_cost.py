from policyengine_uk.model_api import *


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
                "statutory_sick_pay",
                "statutory_maternity_pay",
                "statutory_paternity_pay",
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
