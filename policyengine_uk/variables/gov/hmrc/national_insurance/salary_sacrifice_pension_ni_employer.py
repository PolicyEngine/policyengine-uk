from policyengine_uk.model_api import *
from policyengine_uk.utils.employer_ni import secondary_class_1_threshold


class salary_sacrifice_pension_ni_employer(Variable):
    label = "Employer NI on salary sacrifice pension contributions above cap"
    documentation = (
        "Additional employer National Insurance contributions due to "
        "salary sacrifice pension contributions exceeding the cap. "
        "The excess remains an employer pension contribution and is included "
        "only in NIC earnings. It is the top slice of the earnings "
        "ni_class_1_employer charges, so it bears the secondary percentage "
        "only above the secondary threshold, or above the upper secondary "
        "threshold for an earner under 21 (SSCBA 1992 s.9A) or the apprentice "
        "upper secondary threshold for an apprentice under 25 (s.9B). This "
        "reporting measure is separate from the actual Class 1 contribution "
        "curve and liability flags; do not add it to a National Insurance total."
    )
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = [
        "https://policyengine.org/uk/research/uk-salary-sacrifice-cap",
        "https://www.legislation.gov.uk/ukpga/1992/4/section/9A",
        "https://www.legislation.gov.uk/ukpga/1992/4/section/9B",
    ]

    def formula(person, period, parameters):
        # NIC-only earnings; this does not become an actual member payment.
        excess = person("salary_sacrifice_pension_ni_excess", period)

        gov = parameters(period).gov
        class_1 = gov.hmrc.national_insurance.class_1
        # The earnings ni_class_1_employer charges, which include the excess.
        earnings = person("ni_class_1_income", period)
        if not gov.contrib.policyengine.employer_ni.exempt_employer_pension_contributions:
            earnings = earnings + person("employer_pension_contributions", period)
        threshold = secondary_class_1_threshold(person, period, class_1)
        above_threshold = max_(earnings - threshold, 0)
        above_threshold_without_excess = max_(earnings - excess - threshold, 0)
        return class_1.employer_scale.components[1].rate * (
            above_threshold - above_threshold_without_excess
        )
