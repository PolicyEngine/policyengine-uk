from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.dwp.jsa_income import income_related_jsa_award


class claimant_or_partner_jsa_income(Variable):
    value_type = float
    entity = BenUnit
    label = "income-based JSA of the claimant or partner"
    documentation = (
        "Income-based JSA of the claimant and partner. Means tests and passports that "
        "ask whether the claimant or partner is on income-based JSA read this. "
        "Anyone else in the benefit unit claims in their own right, so their "
        "award is left out here: a non-dependent adult, or a young person "
        "with an award of their own, which is payable to them. It still "
        "counts in jsa_income and so in household income. Which awards "
        "jsa_income holds is decided by value: "
        "when it holds the award its formula gives on all reported awards, "
        "this is the same award on the claimant's and partner's reports; "
        "when it holds the plain total of the reports (the "
        "disable_simulated_benefits reform), this is the plain total of the "
        "claimant's and partner's reports; when it holds anything else (an "
        "award entered directly, or a reform that replaces it), that value "
        "is taken to be the claimant's or partner's. Values are compared to "
        "within half a penny after rounding to the precision jsa_income is stored "
        "in. A stored zero is zero. "
        "An entered jsa_income equal to either reported amount is read through "
        "the reports, so to enter the claimant's or partner's award whatever "
        "other members report, enter this variable directly."
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
        reported = person("jsa_income_reported", period)
        reported_total = benunit.sum(reported)
        claimant_or_partner_reported = benunit.sum(
            reported * person("is_claimant_or_partner", period)
        )
        award_on_all_reports = income_related_jsa_award(benunit, period, reported_total)
        award_on_claimant_or_partner_reports = income_related_jsa_award(
            benunit, period, claimant_or_partner_reported
        )
        # Compare in the precision jsa_income is stored in (float32), so the
        # formula's own award always matches the award recomputed here.
        stored = jsa_income.dtype
        as_formula = np.isclose(
            jsa_income, award_on_all_reports.astype(stored), rtol=0, atol=0.005
        )
        as_reported_total = np.isclose(
            jsa_income, reported_total.astype(stored), rtol=0, atol=0.005
        )
        scoped = where(
            as_formula,
            award_on_claimant_or_partner_reports,
            where(as_reported_total, claimant_or_partner_reported, jsa_income),
        )
        return where(jsa_income > 0, scoped, 0)
