from policyengine_uk.model_api import *
from policyengine_uk.utils.employer_ni import secondary_class_1_threshold


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
        # The sacrifice above the cap bears employer NI but is not cash pay or
        # an actual pension payment.
        ni_only_earnings = person("salary_sacrifice_pension_ni_excess", period)

        # Calculate employer cost
        parameters = parameters(period)
        class_1 = parameters.gov.hmrc.national_insurance.class_1
        r_r = class_1.employer_scale.components[1].rate
        # The secondary threshold, or the UST/AUST where a zero rate applies.
        t_r = secondary_class_1_threshold(person, period, class_1)
        p_r = parameters.gov.contrib.policyengine.employer_ni.exempt_employer_pension_contributions
        pen_con_subtracted_r = employer_pension_contributions
        if p_r:
            pen_con_subtracted_r = employer_pension_contributions
        else:
            pen_con_subtracted_r = 0

        employer_ni = r_r * max_(
            0, ni_class_1_income - pen_con_subtracted_r + ni_only_earnings - t_r
        )
        return ni_class_1_income + employer_ni
