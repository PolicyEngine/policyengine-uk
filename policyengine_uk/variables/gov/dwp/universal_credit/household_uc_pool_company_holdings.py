from policyengine_uk.model_api import *


class household_uc_pool_company_holdings(Variable):
    value_type = float
    entity = Household
    label = (
        "Company holdings taken out of the household's Universal Credit capital pool"
    )
    documentation = (
        "Disregarded company holdings (uc_company_holding_disregard) taken "
        "out of the household's financial capital before its residual is "
        "shared among claimants and partners without a financial observation "
        "or complete override. A claimant or partner's holding is already "
        "covered when their benunit supplies a nonnegative financial "
        "observation (benunit_reported_capital) or complete override. A complete "
        "uc_reported_capital replaces ordinary sources before regulation 77 "
        "company substitution, so it includes its claimant's and partner's "
        "holdings. household_uc_reported_financial_capital consumes the override "
        "or, if larger, their effective holdings after the shared household "
        "corporate-wealth budget is applied. Removing "
        "those holdings again here would count the same disregard twice. "
        "All other holdings leave the pool here, including a dependant's "
        "holding even when their benunit supplies a report or override. "
        "When financial reports and holdings are compatible, no benunit counts "
        "any part of a disregarded holding. An inconsistent financial report "
        "that omits a known holding can leave it in the residual pool. A holding "
        "is shares, held within the household's corporate_wealth. All "
        "household holdings share one nonnegative corporate_wealth budget "
        "through household_uc_company_holding_pool_scale: when their total "
        "exceeds it, scale each person's holding proportionally before "
        "either the override floor or this deduction. This is a defensive "
        "rule for inconsistent inputs, not a statutory determination. The "
        "shared budget prevents holdings from removing ordinary savings or "
        "property. It does not change regulation 77 substitution in the "
        "owner's own assessment."
    )
    definition_period = YEAR
    unit = GBP
    quantity_type = STOCK
    reference = "https://www.legislation.gov.uk/uksi/2013/376/regulation/77"

    def formula(household, period, parameters):
        person = household.members
        has_financial_report = person.benunit("benunit_reported_capital", period) >= 0
        has_complete_override = person.benunit("uc_reported_capital", period) >= 0
        claimant_or_partner = person("is_uc_claimant", period)
        off_reported_capital = (
            has_financial_report | has_complete_override
        ) & claimant_or_partner
        holdings = household.sum(
            person("uc_company_holding_disregard", period)
            * person.household("household_uc_company_holding_pool_scale", period)
            * ~off_reported_capital
        )
        return holdings
