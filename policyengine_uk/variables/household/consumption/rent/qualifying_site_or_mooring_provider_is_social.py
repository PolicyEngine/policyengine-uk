from policyengine_uk.model_api import *


class qualifying_site_or_mooring_provider_is_social(Variable):
    value_type = bool
    entity = BenUnit
    label = "Qualifying site or mooring provider is social"
    documentation = (
        "Whether the qualifying site or mooring amount entered in "
        "benunit_rent is owed directly to a provider of social housing "
        "under the applicable Universal Credit rules. Establish this "
        "provider classification outside the model. In Great Britain, "
        "use the Schedule 4 paragraph 2 definition, including the "
        "social-housing condition for a profit-making registered provider. "
        "In Northern Ireland, the provider must be the Housing Executive "
        "or a registered housing association. This fact applies only "
        "alongside has_qualifying_site_or_mooring_liability. True then "
        "selects the existing UC social rent route; this fact alone does not "
        "establish a qualifying payment, actual or deemed liability, or "
        "overall benefit eligibility. benunit_is_rent_liable remains "
        "a separate condition. False retains the existing private capped "
        "route for a qualifying owner. The existing council or housing "
        "association tenure proxy retains priority. Neither ownership, "
        "MOBILE accommodation nor the household head determines this "
        "provider fact. It does not change tenure, tenancy, rent allocation "
        "or size criteria, or allocate mixed private and social payments."
    )
    definition_period = YEAR
    default_value = False
    reference = (
        "https://www.legislation.gov.uk/uksi/2013/376/schedule/4/paragraph/2",
        "https://www.legislation.gov.uk/uksi/2013/376/schedule/4/paragraph/20",
        "https://www.legislation.gov.uk/uksi/2013/376/schedule/4/paragraph/30",
        "https://www.legislation.gov.uk/nisr/2016/216/schedule/4/paragraph/2",
        "https://www.legislation.gov.uk/nisr/2016/216/schedule/4/paragraph/19",
        "https://www.legislation.gov.uk/nisr/2016/216/schedule/4/paragraph/29",
    )
