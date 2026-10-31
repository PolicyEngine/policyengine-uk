from policyengine_uk.model_api import *


class meets_uc_education_condition(Variable):
    value_type = bool
    entity = Person
    label = "Meets the Universal Credit condition of not receiving education"
    documentation = (
        "Whether this person meets the basic condition in the Welfare Reform "
        "Act 2012 s. 4(1)(d) that a claimant is not receiving education, or "
        "is excepted from it: they are not receiving education "
        "(uc_receiving_education), or an exception applies "
        "(uc_is_excepted_from_education_condition). The Welfare Reform "
        "(Northern Ireland) Order 2015 art. 9(1)(d) sets the same condition. "
        "is_uc_eligible applies it to each claimant, as the Universal Credit "
        "Regulations 2013 reg. 3(2)(b) provides for a couple."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/ukpga/2012/5/section/4",
        "https://www.legislation.gov.uk/nisi/2015/2006/article/9",
    )

    def formula(person, period, parameters):
        return ~person("uc_receiving_education", period) | person(
            "uc_is_excepted_from_education_condition", period
        )
