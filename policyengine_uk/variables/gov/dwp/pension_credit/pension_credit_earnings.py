from policyengine_uk.model_api import *


class pension_credit_earnings(Variable):
    label = "earnings for Pension Credit"
    documentation = (
        "Earnings of the claimant and partner. A claimant's income includes "
        "their partner's (State Pension Credit Act 2002 s.5), but not that of "
        "children or young persons in the family."
    )
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/ukpga/2002/16/section/5",
        "https://www.legislation.gov.uk/uksi/2002/1792/regulation/17A",
    )

    def formula(benunit, period, parameters):
        sources = parameters(
            period
        ).gov.dwp.pension_credit.guarantee_credit.earnings_sources
        person = benunit.members
        earnings = add(person, period, sources)
        return benunit.sum(earnings * person("is_claimant_or_partner", period))
