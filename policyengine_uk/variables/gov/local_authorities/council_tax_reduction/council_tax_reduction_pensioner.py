from policyengine_uk.model_api import *


class council_tax_reduction_pensioner(Variable):
    value_type = bool
    entity = BenUnit
    label = "Pensioner for Council Tax Reduction"
    documentation = (
        "Whether this family's claim falls under the pension-age Council Tax "
        "Reduction rules: the applicant or the applicant's partner has reached "
        "State Pension age. Each applicant's scheme follows their own family, "
        "so where families share the rent and each claims, a working-age family is "
        "assessed under the working-age rules even if the household head's "
        "family is pension-age, and the reverse. The further condition that "
        "neither the applicant nor a partner is on Income Support, income-based "
        "Jobseeker's Allowance, income-related Employment and Support "
        "Allowance or Universal Credit is not modelled here."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2012/2885/regulation/3",
        "https://www.legislation.gov.uk/uksi/2012/2886/schedule/paragraph/3",
        "https://www.legislation.gov.uk/wsi/2013/3029/regulation/3",
        "https://www.legislation.gov.uk/ssi/2021/249/regulation/3",
        "https://www.legislation.gov.uk/ssi/2012/319/regulation/12",
    )

    def formula(benunit, period, parameters):
        # SI 2012/2885 reg 3(1)(a)(i): "he has attained the qualifying age for
        # state pension credit". is_SP_age stands in for that age, as
        # elsewhere in the model.
        person = benunit.members
        applicant_or_partner = person(
            "is_council_tax_reduction_applicant_or_partner", period
        )
        return benunit.any(applicant_or_partner & person("is_SP_age", period))
