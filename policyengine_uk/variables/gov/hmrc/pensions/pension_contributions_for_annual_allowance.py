from policyengine_uk.model_api import *


class pension_contributions_for_annual_allowance(Variable):
    value_type = float
    entity = Person
    label = "Total pension contributions counting toward the Annual Allowance"
    documentation = (
        "The default DC pension input amount under FA 2004 s. 233: member "
        "contributions made before age 75, employer contributions and full "
        "salary sacrifice. Member contributions from age 75 are unrelievable "
        "under s. 188(3)(a) and excluded, while employer contributions still "
        "count. Contributions before 75 above the earnings relief limit "
        "still count. Supply the statutory total pension input amount, "
        "including valued defined-benefit accrual, to override this cash "
        "proxy. The same input feeds adjusted income and the AA charge."
    )
    definition_period = YEAR
    reference = [
        dict(
            title="Finance Act 2004 s. 233",
            href="https://www.legislation.gov.uk/ukpga/2004/12/section/233",
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
        member_contributions = person("pension_contributions", period)
        under_age_limit = (
            person("age", period)
            < parameters(
                period
            ).gov.hmrc.pensions.pension_contributions_relief_age_limit
        )
        return (
            member_contributions * under_age_limit
            + person("employer_pension_contributions", period)
            + person("pension_contributions_via_salary_sacrifice_from_pay", period)
        )
