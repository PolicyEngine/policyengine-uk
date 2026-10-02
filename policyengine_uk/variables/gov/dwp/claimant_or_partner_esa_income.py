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
        "esa_income and so in household income. When esa_income holds what the "
        "reported awards give, either after the capital test (its formula) "
        "or as their plain total (the disable_simulated_benefits reform), the "
        "reports say whose award it is. When it holds anything else (an "
        "award entered directly, or a reform that replaces or removes it), "
        "they do not, and it is taken to be the claimant's or partner's. An "
        "entered award equal to either amount is read through the reports."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/ukpga/1992/4/section/136",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/25",
        "https://www.legislation.gov.uk/uksi/2008/794/regulation/83",
    )

    def formula(benunit, period, parameters):
        person = benunit.members
        esa_income = benunit("esa_income", period)
        reported_total = add(benunit, period, ["esa_income_reported"])
        award_on_all_reports = income_related_esa_award(benunit, period, reported_total)
        award_on_claimant_or_partner_reports = income_related_esa_award(
            benunit,
            period,
            benunit.sum(
                person("esa_income_reported", period)
                * person("is_claimant_or_partner", period)
            ),
        )
        as_reported = np.isclose(
            esa_income, award_on_all_reports, rtol=0, atol=0.005
        ) | np.isclose(esa_income, reported_total, rtol=0, atol=0.005)
        return where(as_reported, award_on_claimant_or_partner_reports, esa_income)
