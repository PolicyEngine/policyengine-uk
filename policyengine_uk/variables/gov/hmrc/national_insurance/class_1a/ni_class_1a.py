from policyengine_uk.model_api import *


class ni_class_1a(Variable):
    value_type = float
    entity = Person
    label = "NI Class 1A contributions"
    documentation = (
        "Class 1A contributions the employer pays on the person's taxable "
        "benefits in kind, which Class 1 leaves out of earnings (SSCBA 1992 "
        "s. 10(1) and (4)). The Class 1A percentage equals the secondary "
        "Class 1 percentage for the year (s. 10(5)), except in 2022-23, when "
        "the Health and Social Care Levy (Repeal) Act 2022 fixes it at "
        "14.53%. Unlike secondary Class 1, it has no threshold and no zero "
        "rate for earners under 21 or apprentices under 25, and the "
        "Employment Allowance cannot be set against it. The employer NI "
        "incidence variables cover secondary Class 1 only, so no household "
        "bears Class 1A or a change in it: it stays with the employer as "
        "revenue in gov_tax."
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        dict(
            title="Social Security Contributions and Benefits Act 1992 s. 10",
            href="https://www.legislation.gov.uk/ukpga/1992/4/section/10",
        ),
        dict(
            title="Health and Social Care Levy (Repeal) Act 2022 Schedule paragraph 1",
            href="https://www.legislation.gov.uk/ukpga/2022/43/schedule/paragraph/1/enacted",
        ),
    ]

    def formula(person, period, parameters):
        ni = parameters(period).gov.hmrc.national_insurance
        fixed = ni.class_1a.percentage_2022_23
        if fixed.in_effect:
            rate = fixed.rate
        else:
            rate = ni.class_1.employer_scale.components[1].rate
        return rate * person("benefits_in_kind", period)
