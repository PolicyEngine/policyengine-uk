from policyengine_uk.model_api import *


class uc_unearned_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Universal Credit unearned income"
    documentation = (
        "The claimant's unearned income, or joint claimants' combined "
        "unearned income: income falling within the descriptions in "
        "regulation 66(1) of the Universal Credit Regulations 2013. Capital "
        "counts only through its assumed yield (uc_tariff_income, regulation "
        "72(1)); actual interest, dividends and rent are not unearned income "
        "at any capital level. Income of a child, a qualifying young person or "
        "anyone else in the benefit unit who is not a claimant does not count."
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        dict(
            title="Universal Credit Regulations 2013 reg. 22(1)(a)",
            href="https://www.legislation.gov.uk/uksi/2013/376/regulation/22",
        ),
        dict(
            title="Welfare Reform Act 2012 s. 8(3) and (4)",
            href="https://www.legislation.gov.uk/ukpga/2012/5/section/8",
        ),
        dict(
            title="Universal Credit Regulations 2013 reg. 66(1)",
            href="https://www.legislation.gov.uk/uksi/2013/376/regulation/66",
        ),
    ]

    def formula(benunit, period, parameters):
        # Reg. 22(1)(a) deducts "all of the claimant's unearned income (or in
        # the case of joint claimants all of their combined unearned income)".
        # Person-level sources count for claimants only; benefit-unit sources
        # (tariff income from capital) are added as they are.
        p = parameters(period).gov.dwp.universal_credit.means_test
        claimants = benunit.members("is_uc_assessed_claimant", period)
        return add_for_members(
            benunit, period, p.income_definitions.unearned, claimants
        )
