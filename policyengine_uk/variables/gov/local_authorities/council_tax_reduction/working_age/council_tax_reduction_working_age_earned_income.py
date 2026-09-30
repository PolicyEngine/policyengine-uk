from policyengine_uk.model_api import *


class council_tax_reduction_working_age_earned_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Working-age council tax reduction net earned income"
    documentation = (
        "Annual net earnings of the claimant and partner for a working-age "
        "council tax reduction claim in Scotland or Wales, before earnings "
        "disregards. With an award of Universal Credit, earnings follow the "
        "Universal Credit measure: gross earnings (with any minimum income "
        "floor) less income tax, National Insurance and all pension "
        "contributions, with no work allowance. Without Universal Credit, "
        "earnings are employment and self-employment income and statutory "
        "sick and maternity pay, less income tax, National Insurance and half "
        "of pension contributions. The earnings of children and young persons "
        "do not count. As elsewhere in the model, all of a person's income "
        "tax is deducted from earnings."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/ssi/2021/249/regulation/49",
        "https://www.legislation.gov.uk/ssi/2021/249/regulation/50",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/6/paragraph/9",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/6/paragraph/15",
    )

    def formula(benunit, period, parameters):
        person = benunit.members
        members = person("is_claimant_or_partner", period)
        tax = add_for_members(benunit, period, ["tax"], members)
        pension_contributions = add_for_members(
            benunit, period, ["pension_contributions"], members
        )
        universal_credit_earnings = add_for_members(
            benunit, period, ["uc_mif_capped_earned_income"], members
        )
        legacy_earnings = add_for_members(
            benunit,
            period,
            [
                "employment_income",
                "self_employment_income",
                "statutory_sick_pay",
                "statutory_maternity_pay",
            ],
            members,
        )
        has_universal_credit = benunit(
            "council_tax_reduction_working_age_has_universal_credit", period
        )
        return where(
            has_universal_credit,
            max_(0, universal_credit_earnings - tax - pension_contributions),
            max_(0, legacy_earnings - tax - 0.5 * pension_contributions),
        )
