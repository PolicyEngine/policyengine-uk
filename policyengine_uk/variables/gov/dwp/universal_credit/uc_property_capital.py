from policyengine_uk.model_api import *


class uc_property_capital(Variable):
    value_type = float
    entity = BenUnit
    label = "Universal Credit property capital share"
    documentation = (
        "Benefit unit's conventional share of the household's net countable "
        "property in the assessment year. Allocate equally to ALL claimant "
        "and partner adults in the household, pooling each unit's shares, "
        "regardless of financial reports, UC receipt or complete UC overrides. "
        "A complete override consumes this share; it is not redistributed. "
        "This is an assumption about unobserved ownership, not a statutory "
        "ownership rule. The main home is excluded. Other property is assumed "
        "to incur sale expenses and have no Schedule 10 disregard; the data "
        "lack reliable asset-level disregard and debt flags, so secured debt "
        "defaults to zero unless supplied in the property-specific inputs."
    )
    definition_period = YEAR
    unit = GBP
    quantity_type = STOCK
    reference = (
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/49",
        "https://www.legislation.gov.uk/uksi/2013/376/schedule/10",
    )

    def formula(benunit, period, parameters):
        p = parameters(period).gov.dwp.universal_credit.means_test.capital
        household_property = sum(
            benunit.household(source, period) for source in p.property_sources
        )
        person = benunit.members
        household_claimants = benunit.max(
            person.household.sum(person.household.members("is_uc_claimant", period))
        )
        benunit_claimants = benunit.sum(person("is_uc_claimant", period))
        return household_property * benunit_claimants / max_(1, household_claimants)
