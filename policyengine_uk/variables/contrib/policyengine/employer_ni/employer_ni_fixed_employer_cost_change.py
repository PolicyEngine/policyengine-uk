from policyengine_uk.model_api import *
from policyengine_uk.utils.employer_ni import (
    salary_sacrifice_cost_terms,
    secondary_class_1_threshold,
)


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

        if person.simulation.baseline is None:
            return 0

        # First, calculate baseline and reformed employer NI contributions.
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
        # Each schedule's salary sacrifice terms: returned pay and the
        # broad-base haircut are pay; the excess over the cap is NIC earnings
        # only, so it bears employer NI but is neither pay nor pension.
        baseline_person = person.simulation.baseline.populations["person"]
        sacrifice_pay_b, ni_only_earnings_b = salary_sacrifice_cost_terms(
            baseline_person, period
        )
        sacrifice_pay_r, ni_only_earnings_r = salary_sacrifice_cost_terms(
            person, period
        )
        pay_before_sacrifice = (
            prior_employment_income + employment_income_behavioral_response
        )
        ni_class_1_income = (
            pay_before_sacrifice
            + sacrifice_pay_b
            + benefits
            + employer_pension_contributions
        )

        # Calculate baseline employer cost
        baseline_parameters = person.simulation.baseline.tax_benefit_system.parameters(
            period
        )

        baseline_class_1 = baseline_parameters.gov.hmrc.national_insurance.class_1
        r_b = baseline_class_1.employer_scale.components[1].rate
        # The secondary threshold, or the UST/AUST where a zero rate applies.
        t_b = secondary_class_1_threshold(person, period, baseline_class_1)
        p_b = baseline_parameters.gov.contrib.policyengine.employer_ni.exempt_employer_pension_contributions
        pen_con_subtracted_b = employer_pension_contributions if p_b else 0

        baseline_employer_ni = r_b * max_(
            ni_class_1_income - pen_con_subtracted_b + ni_only_earnings_b - t_b, 0
        )
        c_b = ni_class_1_income + baseline_employer_ni

        # Calculate reform employer cost
        reform_parameters = parameters(period)
        reform_class_1 = reform_parameters.gov.hmrc.national_insurance.class_1
        r_r = reform_class_1.employer_scale.components[1].rate
        t_r = secondary_class_1_threshold(person, period, reform_class_1)
        p_r = reform_parameters.gov.contrib.policyengine.employer_ni.exempt_employer_pension_contributions
        pen_con_subtracted_r = employer_pension_contributions if p_r else 0

        # Early return if no change in parameters
        if r_b == r_r and p_b == p_r and np.array_equal(t_b, t_r):
            return 0

        # Calculate new NIC earnings keeping employer cost constant. Solve
        # c_b = x + r_r * max(x - k_r, 0) for x, the cost before employer NI,
        # where k_r is the point at which the reformed charge starts: the
        # threshold plus exempt pension contributions, less the NIC-only
        # excess. The cost is continuous and strictly increasing in x, so
        # x = c_b where c_b is at or below k_r (no reformed charge), and
        # otherwise the linear solution above it. NIC earnings include
        # statutory pay and the excess, so this also holds where pay alone is
        # below a threshold but NIC earnings are above it, and where a reform
        # moves the threshold across a person's earnings.
        k_r = pen_con_subtracted_r + t_r - ni_only_earnings_r
        new_ni_class_1_income = where(c_b <= k_r, c_b, (c_b + r_r * k_r) / (1 + r_r))

        # Find difference in employment income: the reformed pay before this
        # change includes the reform's own salary sacrifice pay terms.
        previous_employment_income = pay_before_sacrifice + sacrifice_pay_r
        new_employment_income = (
            new_ni_class_1_income - benefits - employer_pension_contributions
        )

        # Pay cannot fall below zero.
        pay_change = max_(
            new_employment_income - previous_employment_income,
            -previous_employment_income,
        )

        # Apply incidence percentage
        interpolated_pay_change = pay_change * employee_incidence

        # Statutory pay and pension contributions are not adjusted, so a person
        # with no employment income has no pay to change.
        return where(previous_employment_income > 0, interpolated_pay_change, 0)
