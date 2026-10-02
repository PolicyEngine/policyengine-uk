from policyengine_uk.model_api import *


class meets_uc_minimum_age_condition(Variable):
    value_type = bool
    entity = Person
    label = "Meets the Universal Credit minimum age condition"
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/ukpga/2012/5/section/4",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/8",
    )
    documentation = """
    The standard minimum age is 18; regulation 8 permits claims from age 16
    in specified circumstances. Observable proxies cover limited capability
    for work, caring, and responsibility for a child.

    uc_limited_capability_for_work is a proxy (limited capability for work and
    work-related activity, which defaults to is_disabled_for_benefits, or an
    ESA award of the person's own), not an observation of LCW or a pending
    assessment supported by medical evidence under regulation 8(1)(a)-(b).
    is_carer_for_benefits means receipt of Carer's Allowance or Scottish Carer
    Support Payment, or at least the Carer's Allowance qualifying hours of
    care (currently 35 weekly). Its hours limb does not verify the recipient's
    qualifying disability benefit, and it does not exclude paid care.

    For regulation 8(1)(d), responsibility is proxied by being a claimant in a
    benefit unit with a nonclaimant child under the UC child definition. A
    qualifying young person alone does not satisfy this limb. Benefit-unit
    membership does not observe individual legal responsibility.

    Regulation 8(1)(e)-(g) (a partner's responsibility, pregnancy/recent birth,
    and absence of parental support) are not observed. The regulation 8(2)
    care-leaver exclusion, which applies to (c), (f), and (g), is also not
    observed. These provisions are not separately modelled.
    """

    def formula(person, period, parameters):
        p = parameters(period).gov.dwp.universal_credit.eligibility
        age = person("age", period)
        claimant = person("is_uc_claimant", period)
        child = person("is_child_for_universal_credit", period)
        responsible_for_child = claimant & person.benunit.any(child & ~claimant)
        reduced_age_exception = (
            person("uc_limited_capability_for_work", period)
            | person("is_carer_for_benefits", period)
            | responsible_for_child
        )
        return (age >= p.min_age) | ((age >= p.reduced_min_age) & reduced_age_exception)
