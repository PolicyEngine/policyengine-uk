from policyengine_uk.model_api import *
from policyengine_uk.variables.household.demographic.country import Country


class council_tax_reduction_pensioner_child_amounts(Variable):
    value_type = float
    entity = BenUnit
    label = "Council Tax Reduction pensioner child or young person amounts"
    documentation = (
        "The amounts for the children and young persons in a pensioner's "
        "family in the Council Tax Reduction applicable amount, one weekly "
        "amount for each. For the 2018-19 to 2024-25 schemes the Secretary of "
        "State limited England's to two children or young persons, unless "
        "the applicant's Child Tax Credit award included the individual "
        "element for more of them. We read an award from a positive final "
        "child_tax_credit, worked out or entered, or from the claim and "
        "eligibility the model reads from reports, which keeps an award at a "
        "nil rate. We do not model the transitional protection for families "
        "with more than two on 31 March 2018. Where the household head "
        "applies alone (council_tax_reduction_head_applies_alone), we assume "
        "the head has no children in their family, because we cannot "
        "identify their relationships. Nil for working-age families: we do "
        "not model their child amounts here."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/1/paragraph/6",
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/2/part/1/paragraph/2",
        "https://www.legislation.gov.uk/uksi/2017/1305/regulation/7/made",
        "https://www.legislation.gov.uk/uksi/2017/1305/regulation/17/made",
        "https://www.legislation.gov.uk/uksi/2025/39/regulation/5/made",
        "https://www.legislation.gov.uk/ukpga/2002/21/section/14",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/1/paragraph/1",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/2/paragraph/2",
        "https://www.legislation.gov.uk/ssi/2012/319/regulation/20",
        "https://www.legislation.gov.uk/ssi/2012/319/schedule/1/paragraph/3",
    )

    def formula(benunit, period, parameters):
        local_authorities = parameters(period).gov.local_authorities
        england = local_authorities.england.council_tax_reduction.pensioners
        wales = local_authorities.wales.council_tax_reduction.pensioners
        scotland = local_authorities.scotland.council_tax_reduction.pensioners
        country = benunit.household("country", period)
        in_england = country == Country.ENGLAND
        person = benunit.members
        child = person("is_child_or_young_person_for_council_tax_reduction", period)
        children = benunit.sum(child)
        counted = children
        limit = england.applicable_amount.child_limit
        if np.isfinite(limit):
            # SI 2012/2885 Sch 1 para 6(1)(b) and (1A) to (1C), from SI
            # 2017/1305 reg 7: up to two, or those whose individual element
            # an award of Child Tax Credit includes where that gives more.
            # Every child or young person has the same amount, so the
            # greatest total is the greatest count.
            # Para 6(1B)(a) needs an award of Child Tax Credit "whether or
            # not any amount is payable", and HMRC may award it at a nil rate
            # (TCA 2002 s.14(3)). A positive final child_tax_credit, worked
            # out or entered, is an award; so are the claim and eligibility
            # read from reports, whatever amount is payable.
            child_tax_credit_award = (benunit("child_tax_credit", period) > 0) | (
                benunit("would_claim_CTC", period) & benunit("is_CTC_eligible", period)
            )
            child_tax_credit_children = benunit.sum(
                child & person("is_CTC_child_element_included", period)
            )
            limited = min_(children, limit)
            counted = where(
                in_england & child_tax_credit_award,
                max_(limited, child_tax_credit_children),
                where(in_england, limited, children),
            )
        weekly_amount = select(
            [in_england, country == Country.WALES, country == Country.SCOTLAND],
            [
                england.applicable_amount.child_or_young_person,
                wales.applicable_amount.child_or_young_person,
                scotland.applicable_amount.child_or_young_person,
            ],
            default=0,
        )
        pensioner = benunit("council_tax_reduction_pensioner", period)
        applicant_family = ~benunit("council_tax_reduction_head_applies_alone", period)
        return pensioner * applicant_family * counted * weekly_amount * WEEKS_IN_YEAR
