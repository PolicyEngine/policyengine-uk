from policyengine_uk.model_api import *


class is_housing_benefit_young_individual(Variable):
    value_type = bool
    entity = BenUnit
    label = "Young individual (Housing Benefit)"
    documentation = (
        "A single claimant (no partner and not a lone parent) under the "
        "shared accommodation age threshold. The exceptions for a housing "
        "association landlord, care leavers, former hostel residents, "
        "offenders under multi-agency management, people who need overnight "
        "care, qualifying parents or carers, victims of domestic violence "
        "and of modern slavery are not identified."
    )
    definition_period = YEAR
    reference = "https://www.legislation.gov.uk/uksi/2006/213/regulation/2"

    def formula(benunit, period, parameters):
        threshold = parameters(period).gov.dwp.LHA.shared_accommodation_age_threshold
        return benunit("is_single_person", period) & (
            benunit("eldest_claimant_or_partner_age", period) < threshold
        )
