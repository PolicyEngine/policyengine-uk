from policyengine_uk.model_api import *


class council_tax_reduction_working_age_unearned_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Working-age council tax reduction unearned income"
    documentation = (
        "Annual unearned income of the claimant and partner counted in a "
        "working-age council tax reduction claim in Scotland or Wales, other "
        "than Universal Credit and tariff income from capital. Retirement "
        "pensions, contributory Jobseeker's Allowance and Employment and "
        "Support Allowance, carer's allowance, the Carer Support Payment "
        "component (not the Scottish Carer Supplement), "
        "maternity allowance, industrial injuries benefit, incapacity benefit, "
        "severe disablement allowance and working and child tax credits "
        "count. Child Benefit, the income-related benefits, disability "
        "benefits, Housing Benefit and child maintenance do not. Actual "
        "savings interest, dividends and rent are treated as capital, which "
        "yields tariff income instead."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/ssi/2021/249/regulation/57",
        "https://www.legislation.gov.uk/ssi/2021/249/regulation/63",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/6/paragraph/17",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/9",
    )

    def formula(benunit, period, parameters):
        person = benunit.members
        members = person("is_claimant_or_partner", period)
        income = add_for_members(
            benunit,
            period,
            [
                "state_pension",
                "private_pension_income",
                "jsa_contrib",
                "esa_contrib",
                "carers_allowance",
                "carer_support_payment",
                "maternity_allowance",
                "iidb",
                "incapacity_benefit",
                "sda",
            ],
            members,
        )
        # Only the Carer Support Payment component counts, not the Scottish
        # Carer Supplement (SSI 2021/249 reg 4(1), as amended by SSI 2025/340,
        # and the closed list in reg 57(1)).
        csp = parameters(period).gov.social_security_scotland.carer_support_payment
        csp_total = add_for_members(benunit, period, ["carer_support_payment"], members)
        csp_rate = csp.rate + csp.supplement
        supplement_share = csp.supplement / csp_rate if csp_rate > 0 else 0
        supplement = csp_total * supplement_share
        income = income - supplement
        tax_credits = add(benunit, period, ["working_tax_credit", "child_tax_credit"])
        bi = parameters(period).gov.contrib.ubi_center.basic_income
        basic_income = (
            add_for_members(benunit, period, ["basic_income"], members)
            if bi.interactions.include_in_means_tests
            else 0
        )
        return income + tax_credits + basic_income
