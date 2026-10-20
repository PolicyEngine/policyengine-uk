from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.dwp.housing_benefit.applicable_income._net_earnings import (
    person_net_earnings,
)


class housing_benefit_net_earnings(Variable):
    value_type = float
    entity = BenUnit
    label = "Housing Benefit net earnings"
    documentation = (
        "Net earnings of the claimant and partner, from which the Housing "
        "Benefit earnings disregards are taken. For each person: employment "
        "income plus self-employment profit (each floored at zero, as a loss "
        "in one employment is not set against another) plus statutory sick "
        "and maternity pay (regulation 35(1)(i); pension age regulation "
        "35(1)(h)), less income tax (before the winter fuel payment charge), "
        "Class 1, 2 and 4 National Insurance, and Housing Benefit's share of "
        "pension contributions (pension_contribution_deduction_rate, one-half "
        "in law), floored at zero. For an employee the regulations "
        "deduct the income tax deducted from the earnings (regulation 36(3); "
        "pension age regulation 36(2)); for the self-employed, a notional "
        "basic-rate tax on the profit alone less personal reliefs (regulation "
        "39(1); pension age regulation 40(1)). PolicyEngine attributes a "
        "person's income tax to earnings in proportion to their share of the "
        "person's total income plus statutory pay, before any negative income "
        "component. "
        "For employment income that is a lower bound "
        "on the tax on the earnings taxed as the top slice of income; for "
        "self-employment profit alongside other income it can exceed the "
        "notional tax. It is exact for an employee whose earnings are their "
        "only taxable income, and whenever no income tax is due. The earnings "
        "of a child or young person are not the claimant's (regulation 25(3); "
        "pension age regulation 23(3)), so only the claimant's and partner's "
        "count (is_claimant_or_partner)."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/35",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/36",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/38",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/39",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/35",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/36",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/39",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/40",
    )

    def formula(benunit, period, parameters):
        p = parameters(period).gov.dwp.housing_benefit.means_test
        person = benunit.members
        net_earnings = person_net_earnings(
            person, period, p.pension_contribution_deduction_rate
        )
        # The claimant and partner: a child's or young person's earnings are
        # not the claimant's (reg 25(3); pension age reg 23(3)).
        claimant_or_partner = person("is_claimant_or_partner", period)
        return benunit.sum(net_earnings * claimant_or_partner)
