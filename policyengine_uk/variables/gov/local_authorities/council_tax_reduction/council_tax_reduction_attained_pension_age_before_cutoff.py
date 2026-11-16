from policyengine_uk.model_api import *


class council_tax_reduction_attained_pension_age_before_cutoff(Variable):
    value_type = bool
    entity = BenUnit
    label = "CTR applicant or partner attained State Pension age before the cutoff"
    documentation = (
        "Whether the Council Tax Reduction applicant or their partner attained "
        "State Pension age before 1 April 2021, the cutoff England's pensioner "
        "scheme shares with Housing Benefit. Such applicants keep the higher "
        "pension-age personal allowance; other members of the household do "
        "not count. Before the cutoff took effect there was a single "
        "pension-age allowance, the higher one, so this is true for every unit "
        "then. Annual 2021 represents FY2021-22 under the model fiscal-year "
        "convention: the English amendment applies to financial years "
        "beginning on or after 1 April 2021. This flag does not decide "
        "pension-age eligibility."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/2",
        "https://www.legislation.gov.uk/uksi/2021/29/regulation/1/made",
        "https://www.legislation.gov.uk/uksi/2021/29/regulation/7/made",
    )

    def formula(benunit, period, parameters):
        return np.ones(benunit.count, dtype=bool)

    def formula_2021(benunit, period, parameters):
        cutoff = parameters(
            period
        ).gov.dwp.housing_benefit.allowances.pension_age_cutoff
        if cutoff is None:
            return np.ones(benunit.count, dtype=bool)
        # SI 2012/2885 Sch 2 para 1 reads the applicant's and partner's ages,
        # the same people the pensioner test reads
        # (is_council_tax_reduction_applicant_or_partner). Dates are compared
        # as exact YYYYMMDD integers.
        person = benunit.members
        applicant_or_partner = person(
            "is_council_tax_reduction_applicant_or_partner", period
        )
        attained = person("state_pension_age_date", period)
        return benunit.any(applicant_or_partner & (attained < cutoff))
