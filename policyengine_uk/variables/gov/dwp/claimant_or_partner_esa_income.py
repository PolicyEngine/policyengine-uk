from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.dwp.esa_income import income_related_esa_award


class claimant_or_partner_esa_income(Variable):
    value_type = float
    entity = BenUnit
    label = "income-related ESA of the claimant or partner"
    documentation = (
        "Income-related ESA on the claimant's and partner's reported awards, "
        "after the same capital test as esa_income. Means tests and passports "
        "that ask whether the claimant or partner is on income-related ESA "
        "read this. Another member of the benefit unit who is neither the "
        "claimant, the partner nor a child or young person they are "
        "responsible for (for example a non-dependent adult) claims in their "
        "own right, so their award is left out here; it still counts in "
        "esa_income and so in household income. When esa_income is entered "
        "directly rather than calculated from reported awards, the entered "
        "award is taken to be the claimant's or partner's."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/ukpga/1992/4/section/136",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/25",
        "https://www.legislation.gov.uk/uksi/2008/794/regulation/83",
    )

    def formula(benunit, period, parameters):
        if "esa_income" in benunit.simulation.input_variables:
            return benunit("esa_income", period)
        person = benunit.members
        reported_award = benunit.sum(
            person("esa_income_reported", period)
            * person("is_claimant_or_partner", period)
        )
        return income_related_esa_award(benunit, period, reported_award)
