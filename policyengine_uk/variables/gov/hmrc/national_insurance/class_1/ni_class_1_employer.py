from policyengine_uk.model_api import *


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
        thresholds = class_1.thresholds
        age_limits = class_1.secondary_zero_rate_age_limits
        secondary_threshold = thresholds.secondary_threshold * WEEKS_IN_YEAR
        age = person("age", period)
        # s.9A: 0% up to the upper secondary threshold for an earner under 21.
        under_21_threshold = where(
            age < age_limits.under_21_group,
            thresholds.upper_secondary_threshold * WEEKS_IN_YEAR,
            0,
        )
        # s.9B: 0% up to the apprentice upper secondary threshold for a
        # relevant apprentice (an apprentice under 25). s.9A(1A) gives s.9B
        # priority, and s.9A still zero-rates an under-21 apprentice's earnings
        # above the apprentice threshold up to the under-21 one, so the higher
        # of the two applies.
        relevant_apprentice = person("is_apprentice", period) & (
            age < age_limits.relevant_apprentice
        )
        apprentice_threshold = where(
            relevant_apprentice,
            thresholds.apprentice_upper_secondary_threshold * WEEKS_IN_YEAR,
            0,
        )
        # Earnings above the higher of these thresholds and the secondary
        # threshold bear the secondary percentage (s.9A(9)-(10), s.9B(7)).
        threshold = max_(
            secondary_threshold, max_(under_21_threshold, apprentice_threshold)
        )
        return class_1.rates.employer * max_(taxed_earnings - threshold, 0)
