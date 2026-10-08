from policyengine_uk.model_api import *


class housing_benefit_net_earnings(Variable):
    value_type = float
    entity = BenUnit
    label = "Housing Benefit net earnings"
    documentation = "Net earnings calculated for each claimant and partner before aggregation. Dependants' earnings do not count; individual calculation preserves the special and permitted-work couple allocation rules."
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/36",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/36",
    )

    def formula(benunit, period, parameters):
        person = benunit.members
        return benunit.sum(
            person("housing_benefit_person_net_earnings", period)
            * person("is_claimant_or_partner", period)
        )
