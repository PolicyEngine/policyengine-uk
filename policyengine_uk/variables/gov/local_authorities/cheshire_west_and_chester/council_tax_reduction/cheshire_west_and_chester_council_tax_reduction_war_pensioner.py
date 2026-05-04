from policyengine_uk.model_api import *


class cheshire_west_and_chester_council_tax_reduction_war_pensioner(Variable):
    value_type = bool
    entity = BenUnit
    label = "Whether the Cheshire West and Chester CTR claimant is a protected war pensioner"
    documentation = "Set this for source-defined working-age war pensioners, who receive 100% support, no Band D cap, a 16,000 pound capital limit, and a full disregard of defined war pensions."
    definition_period = YEAR
    reference = "https://www.cheshirewestandchester.gov.uk/asset-library/council-tax-reduction-summary-2026-2027-annex-a-part-1.pdf"
    default_value = False
