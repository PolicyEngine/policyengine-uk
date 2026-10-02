from policyengine_uk.model_api import *


class is_on_pension_credit(Variable):
    value_type = bool
    entity = Person
    label = "on Pension Credit"
    documentation = (
        "Whether State Pension Credit is payable to this person. Pension "
        "Credit is awarded to a claimant for themselves and their partner "
        "(SPCA 2002 ss.1 and 17), so the claimant and the partner are both on "
        "it when their benefit unit's award (pension_credit) is positive. Any "
        "other member of the benefit unit claims in their own right and is on "
        "it only if they report an award themselves."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/ukpga/2002/16/section/1",
        "https://www.legislation.gov.uk/ukpga/2002/16/section/17",
    )

    def formula(person, period, parameters):
        couple_award = person.benunit("pension_credit", period) > 0
        own_award = person("pension_credit_reported", period) > 0
        return where(person("is_claimant_or_partner", period), couple_award, own_award)
