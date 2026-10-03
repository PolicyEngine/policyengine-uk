from policyengine_uk.model_api import *


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
        single_personal_allowance = (
            u_25 * p.single.younger + o_25 * p.single.older + pensioner * p.single.aged
        )
        couple_personal_allowance = (
            u_18 * p.couple.younger + o_18 * p.couple.older + pensioner * p.couple.aged
        )
        lone_parent_personal_allowance = (
            u_18 * p.lone_parent.younger
            + o_18 * p.lone_parent.older
            + pensioner * p.lone_parent.aged
        )
        personal_allowance = (
            single * single_personal_allowance
            + couple * couple_personal_allowance
            + lone_parent * lone_parent_personal_allowance
        ) * WEEKS_IN_YEAR
        premiums = benunit("benefits_premiums", period)
        return personal_allowance + premiums
