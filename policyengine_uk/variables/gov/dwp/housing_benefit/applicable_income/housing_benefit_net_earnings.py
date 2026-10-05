from policyengine_uk.model_api import *


class housing_benefit_net_earnings(Variable):
    value_type = float
    entity = BenUnit
    label = "Housing Benefit net earnings"
    documentation = (
        "Net earnings of the claimant and partner, from which the Housing "
        "Benefit earnings disregards are taken. For each person: employment "
        "income plus self-employment profit (each floored at zero, as a loss "
        "in one employment is not set against another), less income tax, "
        "Class 1, 2 and 4 National Insurance, and half of pension "
        "contributions, floored at zero. The regulations deduct the income "
        "tax deducted from, or notionally charged on, the earnings themselves; "
        "PolicyEngine attributes a person's income tax to earnings in "
        "proportion to their share of the person's total income. That is exact "
        "when earnings are the person's only taxable income or no income tax "
        "is due. Children's earnings are excluded (regulation 25(3); "
        "pension age regulation 23(3))."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/36",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/38",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/36",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/39",
    )

    def formula(benunit, period, parameters):
        p = parameters(period).gov.dwp.housing_benefit.means_test
        person = benunit.members
        earnings = max_(person("employment_income", period), 0) + max_(
            person("self_employment_income", period), 0
        )
        total_income = person("total_income", period)
        earnings_share = np.divide(
            earnings,
            total_income,
            out=np.zeros_like(earnings),
            where=total_income > 0,
        )
        income_tax = person("income_tax", period) * min_(earnings_share, 1)
        national_insurance = add(
            person, period, ["ni_class_1_employee", "ni_class_2", "ni_class_4"]
        )
        pension_contributions = (
            person("pension_contributions", period)
            * p.pension_contribution_deduction_rate
        )
        net_earnings = max_(
            earnings - income_tax - national_insurance - pension_contributions,
            0,
        )
        # The claimant and partner; the model's other Housing Benefit
        # variables use the same proxy.
        claimant_or_partner = person("is_adult", period)
        return benunit.sum(net_earnings * claimant_or_partner)
