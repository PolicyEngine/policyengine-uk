from policyengine_uk.model_api import *


class council_tax_reduction_applicable_amount(Variable):
    value_type = float
    entity = BenUnit
    label = "applicable Council Tax Reduction amount"
    documentation = (
        "The applicant's personal allowance and premiums. Ages, couple status "
        "and State Pension age are those of the Council Tax Reduction "
        "applicant and partner (is_council_tax_reduction_applicant_or_partner). "
        "Where the household head applies alone, the head is a single person "
        "with no partner or children, whatever the benefit unit's claimant "
        "and partner are."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/1/paragraph/6",
        "https://www.legislation.gov.uk/ssi/2012/319/regulation/20",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/1/paragraph/1",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/7",
        "https://www.legislation.gov.uk/ssi/2021/249/schedule/1",
    )

    def formula(benunit, period, parameters):
        p = parameters(period).gov.dwp.housing_benefit.allowances
        person = benunit.members
        applicant = person("is_council_tax_reduction_applicant_or_partner", period)
        head_applies_alone = benunit("council_tax_reduction_head_applies_alone", period)
        any_over_SP_age = benunit.any(applicant & person("is_SP_age", period))
        eldest_age = benunit.max(where(applicant, person("age", period), -np.inf))
        older_age_threshold = p.age_threshold.older
        younger_age_threshold = p.age_threshold.younger
        u_18 = eldest_age < younger_age_threshold
        u_25 = eldest_age < older_age_threshold
        o_25 = (eldest_age >= older_age_threshold) & ~any_over_SP_age
        o_18 = (eldest_age >= younger_age_threshold) & ~any_over_SP_age
        # A head applying alone has no partner, and the benefit unit's
        # children are its claimant's and partner's.
        single = where(head_applies_alone, True, benunit("is_single_person", period))
        couple = where(head_applies_alone, False, benunit("is_couple", period))
        lone_parent = where(
            head_applies_alone, False, benunit("is_lone_parent", period)
        )
        single_personal_allowance = (
            u_25 * p.single.younger
            + o_25 * p.single.older
            + any_over_SP_age * p.single.aged
        )
        couple_personal_allowance = (
            u_18 * p.couple.younger
            + o_18 * p.couple.older
            + any_over_SP_age * p.couple.aged
        )
        lone_parent_personal_allowance = (
            u_18 * p.lone_parent.younger
            + o_18 * p.lone_parent.older
            + any_over_SP_age * p.lone_parent.aged
        )
        personal_allowance = (
            single * single_personal_allowance
            + couple * couple_personal_allowance
            + lone_parent * lone_parent_personal_allowance
        ) * WEEKS_IN_YEAR
        premiums = benunit("council_tax_reduction_premiums", period)
        return personal_allowance + premiums
