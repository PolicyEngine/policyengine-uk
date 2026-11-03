from policyengine_uk.model_api import *


class pension_contributions_for_annual_allowance(Variable):
    value_type = float
    entity = Person
    label = "Total pension contributions counting toward the Annual Allowance"
    documentation = (
        "The total pension input amount (FA 2004 s. 229). For money purchase "
        "arrangements it is the input amount under s. 233: member "
        "contributions made before age 75, employer contributions and full "
        "salary sacrifice. Member contributions from age 75 are unrelievable "
        "under s. 188(3)(a) and excluded, while employer contributions still "
        "count. Contributions before 75 above the earnings relief limit "
        "still count. The defined_benefit_pension_share of workplace "
        "contributions is replaced by defined_benefit_pension_input_amount, "
        "the s. 234 input amount. Supply this variable to override the whole "
        "total. The same input feeds adjusted income and the AA charge."
    )
    definition_period = YEAR
    reference = [
        dict(
            title="Finance Act 2004 s. 229",
            href="https://www.legislation.gov.uk/ukpga/2004/12/section/229",
        ),
        dict(
            title="Finance Act 2004 s. 233",
            href="https://www.legislation.gov.uk/ukpga/2004/12/section/233",
        ),
        dict(
            title="Finance Act 2004 s. 234",
            href="https://www.legislation.gov.uk/ukpga/2004/12/section/234",
        ),
        dict(
            title="Finance Act 2004 s. 188(3)(a)",
            href="https://www.legislation.gov.uk/ukpga/2004/12/section/188",
        ),
        dict(
            title="HMRC PTM053200: other money purchase arrangements",
            href="https://www.gov.uk/hmrc-internal-manuals/pensions-tax-manual/ptm053200",
        ),
    ]
    unit = GBP

    def formula(person, period, parameters):
        # A supplied ordinary return is an actual member payment, while the
        # NICs-only excess is not. Include full employer sacrifice separately
        # once at every age, retaining the age exclusion for member payments.
        defined_benefit_share = clip(
            person("defined_benefit_pension_share", period), 0, 1
        )
        money_purchase = 1 - defined_benefit_share
        # Net pay contributions to defined-benefit arrangements are counted
        # through the defined-benefit input amount instead.
        net_pay = person("employee_pension_contributions", period)
        member_contributions = (
            person("pension_contributions", period) - net_pay * defined_benefit_share
        )
        under_age_limit = (
            person("age", period)
            < parameters(
                period
            ).gov.hmrc.pensions.pension_contributions_relief_age_limit
        )
        return (
            member_contributions * under_age_limit
            + (
                person("employer_pension_contributions", period)
                + person("pension_contributions_via_salary_sacrifice_from_pay", period)
            )
            * money_purchase
            + person("defined_benefit_pension_input_amount", period)
        )
