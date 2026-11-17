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
        "The number of applicants and partners who qualify for the working-age "
        "carer premium: entitled to Carer's Allowance or, in Scotland, Carer "
        "Support Payment, whether or not an overlapping benefit reduces the "
        "payment to nil; partners caring for the same severely disabled "
        "person count once. In Scotland from 1 April 2022 an applicant or "
        "partner whose Universal Credit award includes the carer element in "
        "respect of them also qualifies (receives_uc_carer_element), once "
        "even with a carer benefit as well."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/ssi/2021/249/schedule/1/paragraph/5",
        "https://www.legislation.gov.uk/ssi/2021/249/schedule/1/paragraph/6",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/7/paragraph/14",
    )

    def formula(benunit, period, parameters):
        person = benunit.members
        claimant_or_partner = working_age_applicant_or_partner(person, period)
        caring = person("is_entitled_to_carer_benefit", period)
        scottish_scheme = parameters(
            period
        ).gov.local_authorities.scotland.council_tax_reduction.working_age
        if scottish_scheme.carer_premium_counts_uc_carer_element:
            # An award of Universal Credit that includes the carer element
            # (SSI 2021/249 Sch 1 para 6(1)(c)) brings in the claimant it is
            # included for; uc_carer_element alone is the potential element.
            # A person with a carer benefit as well counts once (para 5(2)).
            scotland = is_scotland_scheme(benunit.household("country", period))
            caring = caring | (
                benunit.project(scotland) & person("receives_uc_carer_element", period)
            )
        carers = benunit.sum(claimant_or_partner & caring)
        # Partners caring for the same severely disabled person get one
        # premium (SSI 2021/249 Sch 1 para 5(3)-(4); SSCBA s.70(7ZA) allows
        # one Carer's Allowance per cared-for person), as in carer_premium.
        same_person = benunit("partners_care_for_same_severely_disabled_person", period)
        return where(same_person, min_(carers, 1), carers)
