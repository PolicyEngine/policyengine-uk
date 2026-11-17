from policyengine_uk.model_api import *


class housing_benefit_payable_share(Variable):
    value_type = float
    entity = BenUnit
    label = "Share of the year Housing Benefit is payable"
    documentation = (
        "Share of the year for which this family's Housing Benefit award stays "
        "payable. Unprotected working-age awards outside specified and temporary "
        "accommodation were abolished from 1 July 2026 in Great Britain and "
        "1 October 2026 in Northern Ireland, so for a family outside the "
        "modelled savings this is the share of the year before that date. "
        "Three savings give a share of 1 in every year. "
        "in_specified_or_temporary_accommodation is the first (reg 6A(2), "
        "through art. 7(4)(a)). A family meeting "
        "the Pension Credit age conditions (meets_pension_credit_age_conditions: "
        "a single claimant, or both members of a couple, over the qualifying "
        "age, or a mixed-age couple with the SI 2019/37 art. 4 saving; reg "
        "6A(4) and (5), through art. 7(4)(a)) is the second; a mixed-age "
        "couple without the saving does not keep its award. The third is a "
        "family whose Housing Benefit claimant personally holds a saved "
        "income-related ESA award (art. 7(4)(b)). A positive claimant/partner "
        "ESA report with esa_income_appointee_saving is required, together "
        "with housing_benefit_claimant_is_saved_esa_claimant for a couple. "
        "That supplied status defaults to false: without it a couple is "
        "unsaved, because the model does not identify its Housing Benefit "
        "claimant. A sole claimant's own saved report suffices. The model "
        "reads reports, not a calculated award, so it infers entitlement "
        "immediately before abolition from current receipt. An outside "
        "adult's saved report does not keep the family's award. "
        "A Universal Credit claim ends an ESA-saved continuing award; "
        "specified or temporary accommodation Housing Benefit survives the "
        "claim (housing_benefit_eligible). "
        "Other saved working-age awards are not modelled, so their awards "
        "wrongly end on the abolition date: qualifying HB claims during the "
        "final UC assessment period on reaching pension-credit age, with "
        "entitlement from reaching that age and the relevant Decisions and "
        "Appeals Schedule 1 paragraph 26 applying (reg 6A(3); NI reg 4A(3)); "
        "and the delayed termination for "
        "claimants excluded from UC immediately before abolition under UC "
        "reg 19(1)(b) or (c), until the day after the last day of that "
        "exclusion (art 7(2)). These need award history, decisions or dates "
        "which no inputs supply."
    )
    definition_period = YEAR
    unit = "/1"
    reference = (
        "https://www.legislation.gov.uk/uksi/2025/1148/article/7",
        "https://www.legislation.gov.uk/uksi/2025/1148/article/3A",
        "https://www.legislation.gov.uk/uksi/2014/1230/regulation/6A",
        "https://www.legislation.gov.uk/nisr/2025/176/article/7",
        "https://www.legislation.gov.uk/nisr/2025/176/article/3A",
        "https://www.legislation.gov.uk/uksi/2019/37/article/4",
    )

    def formula(benunit, period, parameters):
        payable = parameters(period).gov.dwp.housing_benefit.working_age_awards_payable
        country = benunit.household("country", period)
        # Great Britain's date applies everywhere but Northern Ireland,
        # including an unknown country.
        working_age_share = where(
            country == country.possible_values.NORTHERN_IRELAND,
            payable.northern_ireland,
            payable.great_britain,
        )
        # SI 2025/1148 art. 7(4)(a) saves claimants within SI 2014/1230
        # reg 6A(2)-(5) (NI: SR 2025/176 art. 7(4)(a), reg 4A(2)-(5)).
        # Reg 6A(4) (a single claimant, or both members of a couple, over the
        # qualifying age for State Pension Credit) and 6A(5) (a mixed-age
        # couple saved by SI 2019/37 art. 4) are the Pension Credit age
        # conditions; the art. 4 saving is inferred from current receipt
        # (has_mixed_age_couple_pension_credit_saving). Specified and
        # temporary accommodation is supplied explicitly under reg 6A(2) (NI
        # reg 4A(2)).
        pension_age_saving = benunit("meets_pension_credit_age_conditions", period)
        protected_accommodation = benunit(
            "in_specified_or_temporary_accommodation", period
        )
        # Art. 7(4)(b) (NI: art. 7(4)(b)) saves an award where, immediately
        # before the abolition date, the claimant is entitled to
        # income-related ESA and the art. 3A(2) appointee saving applies.
        # Sharing an ESA assessment does not make its partner the HB claimant.
        # Use a supplied claimant-specific status, like HB's main-phase ESA
        # input, rather than inventing a general HB claimant identity. Missing
        # status saves only a sole claimant with their own saved report.
        # Read reports and flags, never calculated ESA: it depends on the UC
        # claim that this share can itself trigger.
        person = benunit.members
        claimant_or_partner = person("is_claimant_or_partner", period)
        saved_esa_report = benunit.any(
            claimant_or_partner
            & (person("esa_income_reported", period) > 0)
            & person("esa_income_appointee_saving", period)
        )
        same_claimant = (benunit.sum(claimant_or_partner) == 1) | benunit(
            "housing_benefit_claimant_is_saved_esa_claimant", period
        )
        esa_income_saving = saved_esa_report & same_claimant
        saved = pension_age_saving | protected_accommodation | esa_income_saving
        return where(saved, 1, working_age_share)
