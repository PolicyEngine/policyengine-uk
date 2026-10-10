from policyengine_uk.model_api import *


class is_on_universal_credit(Variable):
    value_type = bool
    entity = Person
    label = "on Universal Credit"
    documentation = (
        "Whether Universal Credit is payable to this person. A couple claims "
        "Universal Credit jointly and it is awarded to them jointly (WRA 2012 "
        "ss.1(2)(b) and 2(1)(b)), and paid into an account the joint "
        "claimants nominate (Universal Credit etc. (Claims and Payments) "
        "Regulations 2013 reg 47(4); reg 47(6) pays it wholly to one member "
        "only by special arrangement). So the claimant and the partner are "
        "both on it when their benefit unit's award (universal_credit) is "
        "positive. Any other member of the benefit "
        "unit claims in their own right and is on it only if they report an "
        "award themselves."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/ukpga/2012/5/section/1",
        "https://www.legislation.gov.uk/ukpga/2012/5/section/2",
        "https://www.legislation.gov.uk/uksi/2013/380/regulation/47",
    )

    def formula(person, period, parameters):
        couple_award = person.benunit("universal_credit", period) > 0
        own_award = person("universal_credit_reported", period) > 0
        return where(person("is_claimant_or_partner", period), couple_award, own_award)
