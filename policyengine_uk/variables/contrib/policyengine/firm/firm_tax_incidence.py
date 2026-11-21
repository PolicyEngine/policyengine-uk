from policyengine_uk.model_api import *


class firm_tax_incidence(Variable):
    label = "Household incidence of firm-only tax changes"
    documentation = (
        "The household's share of firm_tax_change_total, split between "
        "capital (by shareholding), consumers (by consumption_shareholding) "
        "and workers (by the household's share of the weighted employment "
        "income total) with the gov.contrib.policyengine.firm_incidence "
        "parameters. Not yet a term of gov_tax or household_tax: it will "
        "be once a calibrated firm dataset is available."
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period, parameters):
        total = household("firm_tax_change_total", period)
        if not np.any(total):
            return np.zeros(household.count)
        p = parameters(period).gov.contrib.policyengine.firm_incidence
        capital = household("shareholding", period)
        consumer = household("consumption_shareholding", period)
        employment_income = household.sum(
            household.members("employment_income", period)
        )
        weight = household("household_weight", period)
        weighted_employment_income = (employment_income * weight).sum()
        labour = np.divide(
            employment_income,
            weighted_employment_income,
            out=np.zeros(household.count),
            where=weighted_employment_income > 0,
        )
        share = p.capital * capital + p.consumer * consumer + p.labour * labour
        return total * share
