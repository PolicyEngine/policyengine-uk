from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.dwp.jsa_income import income_related_jsa_award


class claimant_or_partner_jsa_income(Variable):
    value_type = float
    entity = BenUnit
    label = "income-based JSA of the claimant or partner"
    documentation = (
        "Income-based JSA on the claimant's and partner's reported awards, "
        "after the same capital test as jsa_income. Means tests and passports "
        "that ask whether the claimant or partner is on income-based JSA "
        "read this. Another member of the benefit unit who is neither the "
        "claimant, the partner nor a child or young person they are "
        "responsible for (for example a non-dependent adult) claims in their "
        "own right, so their award is left out here; it still counts in "
        "jsa_income and so in household income. When jsa_income holds what the "
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
        "https://www.legislation.gov.uk/uksi/1996/207/regulation/88",
    )

    def formula(benunit, period, parameters):
        person = benunit.members
        jsa_income = benunit("jsa_income", period)
        reported_total = add(benunit, period, ["jsa_income_reported"])
        award_on_all_reports = income_related_jsa_award(benunit, period, reported_total)
        award_on_claimant_or_partner_reports = income_related_jsa_award(
            benunit,
            period,
            benunit.sum(
                person("jsa_income_reported", period)
                * person("is_claimant_or_partner", period)
            ),
        )
        as_reported = np.isclose(
            jsa_income, award_on_all_reports, rtol=0, atol=0.005
        ) | np.isclose(jsa_income, reported_total, rtol=0, atol=0.005)
        return where(as_reported, award_on_claimant_or_partner_reports, jsa_income)
