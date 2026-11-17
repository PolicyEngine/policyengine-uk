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
        "income-related ESA award (art. 7(4)(b)); a partner's award alone "
        "does not save it. A saved award is a positive claimant/partner ESA "
        "report with esa_income_appointee_saving. Where exactly one member "
        "reports Housing Benefit, the model takes that member as the Housing "
        "Benefit claimant, as has_mixed_age_couple_pension_credit_saving takes "
        "the reporter. So the family is saved when exactly one member reports "
        "Housing Benefit and that member has the saved award; when no member reports Housing Benefit "
        "and a sole claimant (exactly one is_claimant_or_partner) has it; or "
        "when housing_benefit_claimant_is_saved_esa_claimant confirms the "
        "identity and a claimant or partner has it, whoever reports Housing "
        "Benefit. That supplied status "
        "defaults to false, which leaves the identity to the reports; false "
        "cannot remove an identity they establish. Without the confirmation, "
        "a family with two Housing Benefit reporters, a reporter without the "
        "saved award, or a couple with no Housing Benefit report is unsaved. "
        "The model reads reports, not a calculated award, so it infers "
        "entitlement immediately before abolition from current receipt. An "
        "outside adult's saved report does not keep the family's award, even "
        "when that adult is the only Housing Benefit reporter, and the "
        "supplied status cannot change this; supply is_claimant_or_partner "
        "where that adult is in fact the partner. "
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
        # "The claimant" is the Housing Benefit claimant: a partner's saved
        # award alone does not save it. A saved award is a claimant or
        # partner's positive ESA report with the appointee saving. Path (a)
        # takes the only Housing Benefit reporter as the Housing Benefit
        # claimant, as has_mixed_age_couple_pension_credit_saving takes the
        # reporter. Reporters are counted
        # over every member, as housing_benefit_eligible counts the award,
        # so an adult outside the claimant/partner mask who reports Housing
        # Benefit competes. The identity holds when:
        # (a) exactly one member reports Housing Benefit and has the saved
        #     award;
        # (b) no member reports Housing Benefit and the sole claimant
        #     (exactly one is_claimant_or_partner) has it. Without a report
        #     no reader of this share changes an amount (the continuing award,
        #     the abolition claim and the Tax-Free Childcare choice all need
        #     one), so this shows only in the share itself or through a
        #     supplied housing_benefit_eligible; or
        # (c) housing_benefit_claimant_is_saved_esa_claimant confirms it and
        #     a claimant or partner has the saved award, whoever reports
        #     Housing Benefit.
        # True confirms the identity. False, the default, leaves it to the
        # reports and cannot remove an identity they establish. Anything
        # else (two reporters, a reporter without the saved award, a couple
        # with neither a report nor the confirmation) is unsaved.
        # The saved award counts only on a claimant or partner, on every
        # path. An outside adult who is the only reporter stays unsaved: the
        # Housing Benefit amount still treats the marked member as the
        # claimant and that adult as a non-dependant, so saving on the
        # adult's award would mix two identities.
        # Read reports and flags, never calculated ESA: it depends on the UC
        # claim that this share can itself trigger.
        person = benunit.members
        claimant_or_partner = person("is_claimant_or_partner", period)
        saved_esa = (
            claimant_or_partner
            & (person("esa_income_reported", period) > 0)
            & person("esa_income_appointee_saving", period)
        )
        any_saved_esa = benunit.any(saved_esa)
        hb_reporter = person("housing_benefit_reported", period) > 0
        hb_reporters = benunit.sum(hb_reporter)
        reporter_saved = (hb_reporters == 1) & benunit.any(hb_reporter & saved_esa)
        sole_claimant_saved = (
            (hb_reporters == 0)
            & (benunit.sum(claimant_or_partner) == 1)
            & any_saved_esa
        )
        confirmed = (
            benunit("housing_benefit_claimant_is_saved_esa_claimant", period)
            & any_saved_esa
        )
        esa_income_saving = reporter_saved | sole_claimant_saved | confirmed
        saved = pension_age_saving | protected_accommodation | esa_income_saving
        return where(saved, 1, working_age_share)
