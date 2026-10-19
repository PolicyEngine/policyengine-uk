from policyengine_uk.model_api import *


class household_uc_unreported_claimants(Variable):
    value_type = int
    entity = Household
    label = "Claimants and partners without financial or complete UC capital reports"
    documentation = (
        "Claimants and partners counted in PolicyEngine's allocation of residual "
        "household financial capital for Universal Credit. Units with a "
        "financial observation or a complete UC override do not use this "
        "financial proxy. Property uses all claimant/partner adults instead. "
        "This includes claimant and "
        "partner roles in benefit units that do not receive Universal Credit. "
        "Allocating unidentified household capital by these counts is a "
        "modelling convention; legislation defines whose capital is assessed, "
        "not how household-level data should be allocated."
    )
    definition_period = YEAR
    unit = "person"
    reference = (
        "https://www.legislation.gov.uk/ukpga/2012/5/section/5",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/18",
    )

    def formula(household, period, parameters):
        person = household.members
        reported_capital = person.benunit("uc_reported_capital", period)
        financial_capital = person.benunit("benunit_reported_capital", period)
        has_reported_capital = (reported_capital >= 0) | (financial_capital >= 0)
        is_uc_claimant = person("is_uc_claimant", period)
        return household.sum(is_uc_claimant * ~has_reported_capital)
