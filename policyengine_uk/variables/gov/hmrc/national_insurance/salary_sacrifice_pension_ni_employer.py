from policyengine_uk.model_api import *
from policyengine_uk.utils.employer_ni import secondary_class_1_threshold


class salary_sacrifice_pension_ni_employer(Variable):
    label = "Employer NI on salary sacrifice pension contributions above cap"
    documentation = (
        "Additional employer Class 1 National Insurance due because salary "
        "sacrifice pension contributions above the cap enter NIC-only "
        "earnings. It is the employer's complete Class 1 liability "
        "(ni_class_1_employer) on the employee's earnings, less the liability "
        "on the same earnings without the NIC-only excess "
        "(salary_sacrifice_pension_ni_excess). The excess is the "
        "top slice of earnings: it bears the secondary percentage only above "
        "the secondary threshold, or above the upper secondary threshold for "
        "an earner under 21 (SSCBA 1992 s.9A) or the apprentice upper "
        "secondary threshold for an apprentice under 25 (s.9B), and nothing "
        "for an earner on whom no secondary contributions are due "
        "(ni_class_1_secondary_liable). "
        "\n\n"
        "This measures part of ni_class_1_employer, which already charges the "
        "NIC-only excess. Do not add it to a National Insurance total."
    )
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    defined_for = "ni_class_1_secondary_liable"
    reference = (
        "https://policyengine.org/uk/research/uk-salary-sacrifice-cap",
        "https://www.legislation.gov.uk/ukpga/1992/4/section/9",
        "https://www.legislation.gov.uk/ukpga/1992/4/section/9A",
        "https://www.legislation.gov.uk/ukpga/1992/4/section/9B",
    )

    def formula(person, period, parameters):
        gov = parameters(period).gov
        class_1 = gov.hmrc.national_insurance.class_1
        excess = person("salary_sacrifice_pension_ni_excess", period)
        # The earnings ni_class_1_employer charges, which include the excess.
        earnings = person("ni_class_1_income", period)
        employer_ni = gov.contrib.policyengine.employer_ni
        if not employer_ni.exempt_employer_pension_contributions:
            earnings = earnings + person("employer_pension_contributions", period)
        threshold = secondary_class_1_threshold(person, period, class_1)
        above_threshold = max_(earnings - threshold, 0)
        above_threshold_without_excess = max_(earnings - excess - threshold, 0)
        return class_1.employer_scale.components[1].rate * (
            above_threshold - above_threshold_without_excess
        )
