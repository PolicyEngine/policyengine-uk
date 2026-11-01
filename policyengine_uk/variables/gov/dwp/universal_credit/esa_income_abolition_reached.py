from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.dwp.universal_credit.legacy_benefits_closed import (
    moves_working_age_awards,
)


class esa_income_abolition_reached(Variable):
    value_type = bool
    entity = BenUnit
    label = "Abolition of income-related ESA has reached the family's award"
    documentation = (
        "Whether the claimant or partner reports an old style income-related "
        "ESA award that its abolition has reached: their claim stays payable "
        "for less than the whole year (esa_income_payable_share below 1), "
        "from 2026-27. The Secretary of State appointed 1 July 2026 for the "
        "abolition to reach every remaining award (SI 2025/1148 art. 3A), and "
        "the Department appointed 1 October 2026 in Northern Ireland (SR "
        "2025/176 art. 3A). DWP sent migration notices to 879,000 households "
        "on income-related ESA by December 2025, most of which had claimed "
        "Universal Credit (LA Welfare Direct 6/2026, paras 51 to 54). So a "
        "family whose award the abolition reaches claims Universal Credit if "
        "it would claim when moved (claims_uc_at_legacy_closure), from the "
        "year its award starts to end. From 2027-28 the award has ended and "
        "DWP moves the family off its legacy benefits (legacy_benefits_closed). "
        "The abolition doesn't reach a claim saved for an appointee "
        "(esa_income_appointee_saving). As for the other working-age "
        "closures, DWP doesn't move a family on Pension Credit, or a single "
        "claimant, or joint claimants both, over the qualifying age for State "
        "Pension Credit (SI 2014/1230 reg 8(2B)). This reads reports, the "
        "household's country and the "
        "saving, never an award. Reports by other benefit-unit members, who "
        "claim in their own right, do not count."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2025/1148/article/3A",
        "https://www.legislation.gov.uk/nisr/2025/176/article/3A",
        "https://www.legislation.gov.uk/uksi/2014/1230/regulation/8",
        "https://www.legislation.gov.uk/uksi/2014/1230/regulation/44",
        "https://www.gov.uk/government/publications/la-welfare-direct-bulletins-2026/la-welfare-direct-62026",
    )

    def formula(benunit, period, parameters):
        person = benunit.members
        owners = person("is_claimant_or_partner", period)

        def reports(*variables):
            amounts = sum(person(name, period) for name in variables)
            return benunit.sum(amounts * owners) > 0

        reached = benunit.any(
            owners
            & (person("esa_income_reported", period) > 0)
            & (person("esa_income_payable_share", period) < 1)
        )
        return reached & moves_working_age_awards(
            reports,
            benunit("meets_pension_credit_age_conditions", period),
            benunit("is_mixed_age_couple", period),
        )
