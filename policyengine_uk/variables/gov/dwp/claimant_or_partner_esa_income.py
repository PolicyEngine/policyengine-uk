from policyengine_uk.model_api import *
from policyengine_uk.utils.benefit_unit import claimant_or_partner_award
from policyengine_uk.variables.gov.dwp.esa_income import income_related_esa_award


class claimant_or_partner_esa_income(Variable):
    value_type = float
    entity = BenUnit
    label = "income-related ESA of the claimant or partner"
    documentation = (
        "Income-related ESA of the claimant and partner. Means tests and passports that "
        "ask whether the claimant or partner is on income-related ESA read this. "
        "Another member of the benefit unit who is neither the claimant, the "
        "partner nor a child or young person they are responsible for (for "
        "example a non-dependent adult) claims in their own right, so their "
        "award is left out here; it still counts in esa_income and so in "
        "household income. Income Support's gate (income_support_eligible) "
        "reads it too (s.124(1)(h)). Which awards esa_income holds is "
        "decided by value: when it holds the award its formula gives on all "
        "reported awards, this is the same award on the claimant's and "
        "partner's reports; when it holds the plain total of the reports, this "
        "is the plain total of the claimant's and partner's reports; when it "
        "holds anything else (an award entered directly, or a reform that "
        "replaces it), that value is taken to be the claimant's or partner's. "
        "A stored zero is zero. An entered esa_income equal to either reported "
        "amount is read through the reports, so to enter the claimant's or "
        "partner's award whatever other members report, enter this variable "
        "directly. The disable_simulated_benefits reform does that for each "
        "year, from the claimant's and partner's reports in the dataset year."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/ukpga/1992/4/section/136",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/25",
        "https://www.legislation.gov.uk/uksi/2008/794/regulation/83",
    )

    def formula(benunit, period, parameters):
        return claimant_or_partner_award(
            benunit,
            period,
            "esa_income",
            "esa_income_reported",
            income_related_esa_award,
        )
