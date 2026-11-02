from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.dwp.housing_benefit.applicable_income._net_earnings import (
    person_net_earnings,
)


class income_support_net_earnings(Variable):
    value_type = float
    entity = BenUnit
    label = "Income Support net earnings"
    documentation = (
        "Net earnings of the claimant and partner, from which the Income "
        "Support earnings disregard (Schedule 8) is taken, so the disregard "
        "can never exceed them. For each person: employment income plus "
        "self-employment profit, each floored at zero (a loss in one "
        "employment is not set against another, regulation 38(11)), less the "
        "income tax and National Insurance on them and Income Support's share "
        "of pension contributions (pension_contribution_deduction_rate, "
        "one-half in law), floored at zero. Statutory sick, maternity and "
        "paternity pay are not earnings (regulation 35(2)(b)) but income "
        "other than earnings (regulation 40(1)), as are pensions, benefits "
        "and maintenance, so none receives the Schedule 8 earnings disregard. "
        "For an employee the "
        "regulations deduct the income tax and primary Class 1 contributions "
        "deducted from the earnings (regulation 36(3)); for the self-employed, "
        "a notional basic-rate tax and Class 2 and 4 contributions on the profit "
        "alone (regulations 38(3) and 39). This Income Support calculation "
        "uses annual attribution rather than payroll deductions or a separate "
        "notional tax calculation: it attributes a person's income tax to "
        "their earnings in proportion to the earnings' share of the person's "
        "raw income, and their Class 1 "
        "contributions to their wages using the non-statutory share of "
        "the Class 1 base. This annual split "
        "approximates the contributions actually deducted from earnings; "
        "Class 2 and Class 4 contributions come off in full. Half of all "
        "pension contributions is deducted from earnings without identifying "
        "any attributable to sick/leave pay (Schedule 9 paragraph 4). The "
        "helper person_net_earnings also serves Housing Benefit and Council "
        "Tax Reduction, which include statutory pay in earnings. A child's "
        "or young person's earnings are not "
        "the claimant's (regulation 23(2)), so only the claimant's and "
        "partner's count. Employer-paid sick or parental-leave pay above the "
        "statutory amounts, which regulation 35(2)(b) also excludes, is not "
        "separated from employment income."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/1987/1967/regulation/23",
        "https://www.legislation.gov.uk/uksi/1987/1967/regulation/35",
        "https://www.legislation.gov.uk/uksi/1987/1967/regulation/36",
        "https://www.legislation.gov.uk/uksi/1987/1967/regulation/38",
        "https://www.legislation.gov.uk/uksi/1987/1967/regulation/39",
        "https://www.legislation.gov.uk/uksi/1987/1967/regulation/40",
    )

    def formula(benunit, period, parameters):
        p = parameters(period).gov.dwp.income_support.means_test
        person = benunit.members
        net_earnings = person_net_earnings(
            person,
            period,
            p.pension_contribution_deduction_rate,
            statutory_pay_is_earnings=False,
        )
        # The claimant and partner (reg 23(1)); a child's or young person's
        # earnings are not the claimant's (reg 23(2)).
        claimant_or_partner = person("is_claimant_or_partner", period)
        return benunit.sum(net_earnings * claimant_or_partner)
