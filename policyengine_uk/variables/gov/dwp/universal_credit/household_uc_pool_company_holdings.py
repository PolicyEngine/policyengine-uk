from policyengine_uk.model_api import *


class household_uc_pool_company_holdings(Variable):
    value_type = float
    entity = Household
    label = (
        "Company holdings taken out of the household's Universal Credit capital pool"
    )
    documentation = (
        "Disregarded company holdings (uc_company_holding_disregard) taken "
        "out of the household's capital before it is shared among the "
        "claimants and partners of benunits that do not report their "
        "capital. That is every holding except a reporting benunit's "
        "claimant's or partner's, which comes off that benunit's reported "
        "capital instead: the holdings of everyone in benunits that do not "
        "report, and of dependants in benunits that do, whose capital is "
        "nobody's to count. So no benunit counts any part of a disregarded "
        "holding. A holding is shares, held within the household's "
        "corporate_wealth, so no more than that is taken out: a holding "
        "entered without matching corporate_wealth cannot remove savings or "
        "property."
    )
    definition_period = YEAR
    unit = GBP
    quantity_type = STOCK
    reference = "https://www.legislation.gov.uk/uksi/2013/376/regulation/77"

    def formula(household, period, parameters):
        person = household.members
        reported = (person.benunit("uc_reported_capital", period) >= 0) | (
            person.benunit("benunit_reported_capital", period) >= 0
        )
        claimant_or_partner = person("is_uc_claimant", period)
        off_reported_capital = reported & claimant_or_partner
        holdings = household.sum(
            person("uc_company_holding_disregard", period) * ~off_reported_capital
        )
        corporate_wealth = max_(0, household("corporate_wealth", period))
        return min_(holdings, corporate_wealth)
