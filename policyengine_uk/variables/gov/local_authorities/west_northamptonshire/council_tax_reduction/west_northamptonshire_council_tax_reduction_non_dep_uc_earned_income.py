from policyengine_uk.model_api import *


class west_northamptonshire_council_tax_reduction_non_dep_uc_earned_income(Variable):
    value_type = float
    entity = Person
    label = "West Northamptonshire Council Tax Reduction non-dependant UC earned income"
    documentation = "Person-level UC earned income for applying the source exemption where a non-dependant's Universal Credit award is calculated with no earned income. Defaults to modeled person-level gross UC earned income and can be overridden where DWP assessed income differs."
    definition_period = YEAR
    unit = GBP
    reference = "https://cms.westnorthants.gov.uk/media/2065/download"

    def formula(person, period, parameters):
        return person("uc_mif_capped_earned_income", period)
