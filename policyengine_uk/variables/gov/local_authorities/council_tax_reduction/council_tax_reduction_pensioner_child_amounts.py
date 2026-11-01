from policyengine_uk.model_api import *
from policyengine_uk.variables.household.demographic.country import Country


class council_tax_reduction_pensioner_child_amounts(Variable):
    value_type = float
    entity = BenUnit
    label = "Council Tax Reduction pensioner child or young person amounts"
    documentation = (
        "The amounts for the children and young persons in a pensioner's "
        "family in the Council Tax Reduction applicable amount, one weekly "
        "amount for each. England's prescribed requirements limited them to "
        "two children or young persons for the 2018-19 to 2024-25 schemes, "
        "unless the applicant's Child Tax Credit award included the "
        "individual element for more of them. The transitional protection "
        "for families with more than two on 31 March 2018 is not modelled. "
        "Nil where the household head applies alone "
        "(council_tax_reduction_head_applies_alone), since the head's family "
        "then has no children, and for working-age families, whose child "
        "amounts are not modelled."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/1/paragraph/6",
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/2/part/1/paragraph/2",
        "https://www.legislation.gov.uk/uksi/2017/1305/regulation/7/made",
        "https://www.legislation.gov.uk/uksi/2017/1305/regulation/17/made",
        "https://www.legislation.gov.uk/uksi/2025/39/regulation/5/made",
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
            child_tax_credit_award = benunit("would_claim_CTC", period) & benunit(
                "is_CTC_eligible", period
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
