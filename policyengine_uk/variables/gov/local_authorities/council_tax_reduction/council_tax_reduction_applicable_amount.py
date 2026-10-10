from policyengine_uk.model_api import *
from policyengine_uk.variables.household.demographic.country import Country


class council_tax_reduction_applicable_amount(Variable):
    value_type = float
    entity = BenUnit
    label = "applicable Council Tax Reduction amount"
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/1/paragraph/6",
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/2",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/2",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/7",
        "https://www.legislation.gov.uk/ssi/2012/319/schedule/1",
        "https://www.legislation.gov.uk/ssi/2021/249/schedule/1",
    )

    def formula(benunit, period, parameters):
        p = parameters(period).gov.dwp.housing_benefit.allowances
        # England Sch 1 para 6 specifies the "applicable amount for a pensioner";
        # Wales and Scotland also have separate pensioner allowance tables.
        # The shared definition includes qualifying age and award exclusions.
        pensioner = benunit("council_tax_reduction_pensioner", period)
        eldest_age = benunit("eldest_claimant_or_partner_age", period)
        older_age_threshold = p.age_threshold.older
        younger_age_threshold = p.age_threshold.younger
        u_18 = eldest_age < younger_age_threshold
        u_25 = eldest_age < older_age_threshold
        o_25 = (eldest_age >= older_age_threshold) & ~pensioner
        o_18 = (eldest_age >= younger_age_threshold) & ~pensioner
        single = benunit("is_single_person", period)
        couple = benunit("is_couple", period)
        lone_parent = benunit("is_lone_parent", period)
        # Pension-age personal allowances. England's prescribed requirements
        # (SI 2012/2885 Sch 2 para 1, amended by SI 2021/29 for schemes for
        # financial years from 2021-22) split them by when State Pension age
        # was attained, with the same cutoff and amounts as Housing Benefit.
        # The Scottish (SSI 2012/319 Sch 1 para 2) and Welsh (SI 2013/3029
        # Sch 2 para 1) schemes keep one pension-age rate, the higher one.
        # England's rows (2) and (5) do not cover a couple where one member has
        # not reached State Pension age and the other did so after the cutoff;
        # as for Housing Benefit, such a couple gets the lower rate.
        single_aged, couple_aged, lone_parent_aged = (
            p.single.aged,
            p.couple.aged,
            p.lone_parent.aged,
        )
        if p.pension_age_cutoff is not None:
            in_england = benunit.household("country", period) == Country.ENGLAND
            lower = in_england & ~benunit(
                "housing_benefit_attained_pension_age_before_cutoff", period
            )
            single_aged = where(lower, p.single.aged_from_cutoff, single_aged)
            couple_aged = where(lower, p.couple.aged_from_cutoff, couple_aged)
            lone_parent_aged = where(
                lower, p.lone_parent.aged_from_cutoff, lone_parent_aged
            )
        single_personal_allowance = (
            u_25 * p.single.younger + o_25 * p.single.older + pensioner * single_aged
        )
        couple_personal_allowance = (
            u_18 * p.couple.younger + o_18 * p.couple.older + pensioner * couple_aged
        )
        lone_parent_personal_allowance = (
            u_18 * p.lone_parent.younger
            + o_18 * p.lone_parent.older
            + pensioner * lone_parent_aged
        )
        personal_allowance = (
            single * single_personal_allowance
            + couple * couple_personal_allowance
            + lone_parent * lone_parent_personal_allowance
        ) * WEEKS_IN_YEAR
        # The pension-age schedules have only the severe disability and carer
        # premiums; the same pensioner test chooses the schedule.
        premiums = where(
            pensioner,
            benunit("pension_age_benefits_premiums", period),
            benunit("working_age_benefits_premiums", period),
        )
        return personal_allowance + premiums
