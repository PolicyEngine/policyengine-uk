from policyengine_uk.model_api import *
from policyengine_uk.utils.excise import fiscal_year_segments


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
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/2/2018-04-01",
        "https://www.legislation.gov.uk/ssi/2020/413/regulation/13/made",
        "https://www.legislation.gov.uk/wsi/2022/51/regulation/5/made",
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
        ctr = parameters(
            period
        ).gov.local_authorities.council_tax_reduction.pensioners.personal_allowance
        country = benunit.household("country", period)
        countries = country.possible_values
        pension_single = 0
        pension_couple = 0
        pension_lone_parent = 0
        # The under-65 category ended at different dates in the three CTR
        # schemes. Do not reuse HB's 6 December 2018 cutoff for all countries.
        for rules, share in fiscal_year_segments(
            parameters.gov.local_authorities.council_tax_reduction.pensioners.personal_allowance.history,
            period.start.year,
        ):
            lower_category = select(
                [
                    country == countries.ENGLAND,
                    country == countries.SCOTLAND,
                    country == countries.WALES,
                ],
                # The Welsh amendment applies to whole financial-year
                # schemes, not the last days of the previous model year.
                [rules.england, rules.scotland, ctr.under_65_wales_scheme_applies],
                default=False,
            ) & (eldest_age < ctr.under_65_age)
            pension_single += share * where(
                lower_category, ctr.under_65_single[country], p.single.aged
            )
            pension_couple += share * where(
                lower_category, ctr.under_65_couple[country], p.couple.aged
            )
            pension_lone_parent += share * where(
                lower_category, ctr.under_65_single[country], p.lone_parent.aged
            )
        single_personal_allowance = (
            u_25 * p.single.younger + o_25 * p.single.older + pensioner * pension_single
        )
        couple_personal_allowance = (
            u_18 * p.couple.younger + o_18 * p.couple.older + pensioner * pension_couple
        )
        lone_parent_personal_allowance = (
            u_18 * p.lone_parent.younger
            + o_18 * p.lone_parent.older
            + pensioner * pension_lone_parent
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
