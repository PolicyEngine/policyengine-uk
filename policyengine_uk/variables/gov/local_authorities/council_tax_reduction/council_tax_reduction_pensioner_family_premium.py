from policyengine_uk.model_api import *
from policyengine_uk.variables.household.demographic.country import Country


class council_tax_reduction_pensioner_family_premium(Variable):
    value_type = float
    entity = BenUnit
    label = "Council Tax Reduction pensioner family premium"
    documentation = (
        "Councils add the family premium to a pensioner's applicable amount "
        "when their family includes a child or young person. The Welsh "
        "Ministers retain it. The Secretary of State made England's nil for "
        "reduction weeks beginning after 1 May 2016, and the Scottish "
        "Ministers removed Scotland's from 1 May 2016. Each kept it for "
        "families with a child who had a reduction on 30 April 2016 until "
        "they make a new application or have no child; we do not model that "
        "protection. We read each year's amount on 30 April, so we keep the "
        "premium for the whole of model year 2016."
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
        # We assume the head who applies alone has no children in their family.
        has_child = ~benunit(
            "council_tax_reduction_head_applies_alone", period
        ) & benunit(
            "is_responsible_for_child_or_young_person_for_council_tax_reduction", period
        )
        return pensioner * has_child * weekly_premium * WEEKS_IN_YEAR
