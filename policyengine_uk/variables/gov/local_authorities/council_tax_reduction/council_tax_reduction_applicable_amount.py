from policyengine_uk.model_api import *
from policyengine_uk.variables.household.demographic.country import Country


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
        "claimant and partner are. Premiums are council_tax_reduction_premiums. "
        "A pensioner's applicable amount also has the amounts for the "
        "children and young persons in the family "
        "(council_tax_reduction_pensioner_child_amounts) and the family "
        "premium (council_tax_reduction_pensioner_family_premium)."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/1/paragraph/6",
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/2",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/1/paragraph/1",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/2",
        "https://www.legislation.gov.uk/ssi/2012/319/regulation/20",
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
                "council_tax_reduction_attained_pension_age_before_cutoff", period
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
        premiums = benunit("council_tax_reduction_premiums", period)
        # A pensioner's amounts for the children and young persons in the
        # family and the family premium (SI 2012/2885 Sch 1 para 6(1)(b)-(c);
        # WSI 2013/3029 Sch 1 para 1(1)(b)-(c); SSI 2012/319 reg 20(b)).
        # Working-age families get neither here.
        child_amounts = add(
            benunit,
            period,
            [
                "council_tax_reduction_pensioner_child_amounts",
                "council_tax_reduction_pensioner_family_premium",
            ],
        )
        return personal_allowance + premiums + child_amounts
