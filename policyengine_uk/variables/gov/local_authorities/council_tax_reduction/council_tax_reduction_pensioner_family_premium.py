from policyengine_uk.model_api import *
from policyengine_uk.variables.household.demographic.country import Country


class council_tax_reduction_pensioner_family_premium(Variable):
    value_type = float
    entity = BenUnit
    label = "Council Tax Reduction pensioner family premium"
    documentation = (
        "The family premium in a pensioner's Council Tax Reduction applicable "
        "amount, where the family includes a child or young person. Wales "
        "keeps it. England's prescribed requirements make it nil for "
        "reduction weeks beginning after 1 May 2016, and Scotland removed it "
        "from 1 May 2016. Each saved it for families with a child who had a "
        "reduction on 30 April 2016 until they make a new application or "
        "have no child; that protection is not modelled. The model reads "
        "each year's amount on 30 April, so 2016-17 keeps the premium."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/1/paragraph/6",
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/2/part/2/paragraph/3",
        "https://www.legislation.gov.uk/uksi/2015/2041/regulation/3/made",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/1/paragraph/1",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/2/paragraph/3",
        "https://www.legislation.gov.uk/ssi/2016/81/regulation/2/made",
        "https://www.legislation.gov.uk/ssi/2016/81/regulation/18/made",
        "https://www.legislation.gov.uk/ssi/2012/319/regulation/20",
    )

    def formula(benunit, period, parameters):
        local_authorities = parameters(period).gov.local_authorities
        england = local_authorities.england.council_tax_reduction.pensioners
        wales = local_authorities.wales.council_tax_reduction.pensioners
        scotland = local_authorities.scotland.council_tax_reduction.pensioners
        country = benunit.household("country", period)
        weekly_premium = select(
            [
                country == Country.ENGLAND,
                country == Country.WALES,
                country == Country.SCOTLAND,
            ],
            [
                england.applicable_amount.family_premium,
                wales.applicable_amount.family_premium,
                scotland.applicable_amount.family_premium,
            ],
            default=0,
        )
        pensioner = benunit("council_tax_reduction_pensioner", period)
        # The head who applies alone has no children in their family.
        has_child = ~benunit(
            "council_tax_reduction_head_applies_alone", period
        ) & benunit(
            "is_responsible_for_child_or_young_person_for_council_tax_reduction", period
        )
        return pensioner * has_child * weekly_premium * WEEKS_IN_YEAR
