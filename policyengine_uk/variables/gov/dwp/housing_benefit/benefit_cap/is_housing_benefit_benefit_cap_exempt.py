from policyengine_uk.model_api import *


class is_housing_benefit_benefit_cap_exempt(Variable):
    value_type = bool
    entity = BenUnit
    label = "Exempt from the Housing Benefit benefit cap"
    documentation = (
        "Whether the benefit cap does not apply to the family's Housing "
        "Benefit: regulation 75E (working tax credit) or 75F (specified "
        "benefits) of the HB Regs 2006 applies (reg. 75A), or the claim falls "
        "under the Housing Benefit (Persons who have attained the qualifying "
        "age for state pension credit) Regulations 2006 (reg. 5), which have "
        "no benefit cap. Housing Benefit has no earnings exception and no "
        "exception for the Universal Credit LCWRA or carer elements."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/75A",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/75E",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/75F",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/5",
    )

    def formula(benunit, period, parameters):
        return (
            benunit("is_housing_benefit_benefit_cap_exempt_working_tax_credit", period)
            | benunit("is_housing_benefit_benefit_cap_exempt_specified_benefit", period)
            | benunit("housing_benefit_pension_age_regulations_apply", period)
        )
