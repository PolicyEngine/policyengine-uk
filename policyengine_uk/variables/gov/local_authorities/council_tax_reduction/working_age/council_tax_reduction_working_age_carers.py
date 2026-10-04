from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.working_age._applicant import (
    working_age_applicant_or_partner,
)
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_scotland_scheme,
)


class council_tax_reduction_working_age_carers(Variable):
    value_type = int
    entity = BenUnit
    label = "Claimants and partners qualifying for the working-age CTR carer premium"
    documentation = (
        "The number of claimants and partners who qualify for the working-age "
        "carer premium: entitled to Carer's Allowance or, in Scotland, Carer "
        "Support Payment, whether or not an overlapping benefit reduces the "
        "payment to nil. In Scotland an award of Universal Credit that "
        "includes the carer element also qualifies; when no one in the family "
        "is entitled to a carer benefit, it counts as one carer."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/ssi/2021/249/schedule/1/paragraph/6",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/7/paragraph/14",
    )

    def formula(benunit, period, parameters):
        person = benunit.members
        claimant_or_partner = working_age_applicant_or_partner(person, period)
        entitled = person("is_entitled_to_carer_benefit", period)
        carers = benunit.sum(claimant_or_partner & entitled)
        scotland = is_scotland_scheme(benunit.household("country", period))
        # An award of Universal Credit that includes the carer element
        # (SSI 2021/249 Sch 1 para 6(1)(c)); uc_carer_element alone is the
        # potential element.
        uc_carer_element = (benunit("uc_carer_element", period) > 0) & benunit(
            "council_tax_reduction_working_age_has_universal_credit", period
        )
        return carers + (scotland & uc_carer_element & (carers == 0))
