from policyengine_uk.model_api import *


class council_tax_reduction_applicable_amount(Variable):
    value_type = float
    entity = BenUnit
    label = "applicable Council Tax Reduction amount"
    documentation = (
        "The applicant's personal allowance and premiums. Ages, couple status "
        "and lone-parent status are those of the Council Tax Reduction "
        "applicant and partner (is_council_tax_reduction_applicant_or_partner). "
        "Where the household head applies alone "
        "(council_tax_reduction_head_applies_alone), the head is a single "
        "person with no partner or children, whatever the benefit unit's "
        "claimant and partner are. Premiums are council_tax_reduction_premiums."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/1/paragraph/6",
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/2",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/2",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/7",
        "https://www.legislation.gov.uk/ssi/2012/319/schedule/1",
        "https://www.legislation.gov.uk/ssi/2021/249/schedule/1",
        "https://www.legislation.gov.uk/ssi/2021/249/regulation/6",
    )

    def formula(benunit, period, parameters):
        p = parameters(period).gov.dwp.housing_benefit.allowances
        # England Sch 1 para 6 specifies the "applicable amount for a pensioner";
        # Wales and Scotland also have separate pensioner allowance tables.
        # The shared definition includes qualifying age and award exclusions.
        pensioner = benunit("council_tax_reduction_pensioner", period)
        # The applicant's and partner's ages. A household head who applies alone
        # (council_tax_reduction_head_applies_alone) is a single person with no
        # partner or children: the benefit unit's are its claimant's.
        person = benunit.members
        applicant = person("is_council_tax_reduction_applicant_or_partner", period)
        head_applies_alone = benunit("council_tax_reduction_head_applies_alone", period)
        eldest_age = benunit.max(where(applicant, person("age", period), -np.inf))
        older_age_threshold = p.age_threshold.older
        younger_age_threshold = p.age_threshold.younger
        u_18 = eldest_age < younger_age_threshold
        u_25 = eldest_age < older_age_threshold
        o_25 = (eldest_age >= older_age_threshold) & ~pensioner
        o_18 = (eldest_age >= younger_age_threshold) & ~pensioner
        # Each scheme's own young person decides who is a lone parent: the
        # Universal Credit definition in Scotland's working-age scheme (SSI
        # 2021/249 regs 4 and 6), the Child Benefit definition elsewhere.
        couple = ~head_applies_alone & benunit("is_couple", period)
        lone_parent = ~head_applies_alone & benunit(
            "is_council_tax_reduction_lone_parent", period
        )
        single = ~couple & ~lone_parent
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
        # The pension-age schedules have only the severe disability and carer
        # premiums; the same pensioner test chooses the schedule.
        premiums = benunit("council_tax_reduction_premiums", period)
        return personal_allowance + premiums
