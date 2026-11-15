from policyengine_uk.model_api import *
from policyengine_uk.utils.employer_ni import secondary_class_1_threshold


class ni_class_1_employer(Variable):
    value_type = float
    entity = Person
    label = "NI Class 1 employer-side contributions"
    documentation = (
        "Secondary Class 1 contributions at the secondary percentage on "
        "earnings above the secondary threshold (SSCBA 1992 s.9). For an "
        "earner under 21 (s.9A) or a relevant apprentice under 25 (s.9B), "
        "earnings up to the upper secondary threshold, or the apprentice upper "
        "secondary threshold, are zero-rated."
    )
    definition_period = YEAR
    unit = GBP
    defined_for = "ni_class_1_secondary_liable"
    reference = [
        dict(
            title="Social Security Contributions and Benefits Act 1992 s.9",
            href="https://www.legislation.gov.uk/ukpga/1992/4/section/9",
        ),
        dict(
            title="Social Security Contributions and Benefits Act 1992 s.9A",
            href="https://www.legislation.gov.uk/ukpga/1992/4/section/9A",
        ),
        dict(
            title="Social Security Contributions and Benefits Act 1992 s.9B",
            href="https://www.legislation.gov.uk/ukpga/1992/4/section/9B",
        ),
    ]

    def formula(person, period, parameters):
        class_1 = parameters(period).gov.hmrc.national_insurance.class_1
        earnings = person("ni_class_1_income", period)
        if not parameters(
            period
        ).gov.contrib.policyengine.employer_ni.exempt_employer_pension_contributions:
            added_pension_contributions = person(
                "employer_pension_contributions", period
            )
            taxed_earnings = earnings + added_pension_contributions
        else:
            taxed_earnings = earnings
        # Earnings above the secondary threshold, or the UST/AUST for an
        # earner under 21 or a relevant apprentice, bear the secondary
        # percentage (s.9A, s.9B).
        threshold = secondary_class_1_threshold(person, period, class_1)
        return class_1.employer_scale.components[1].rate * max_(
            taxed_earnings - threshold, 0
        )
