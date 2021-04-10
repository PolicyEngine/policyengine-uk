from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_uk.tools.general import *


class benefit_cap(Variable):
    value_type = float
    entity = BenUnit
    label = u"Benefit cap"
    definition_period = WEEK

    def formula(benunit, period, parameters):
        children = benunit("has_children", period)
        region = benunit.max(benunit.members("person_region", period))
        in_london = region == region.possible_values.LONDON
        cap = parameters(period).benefits.benefit_cap
        rate = select(
            [
                children * in_london,
                children * not_(in_london),
                not_(children) * in_london,
                not_(children) * not_(in_london),
            ],
            [
                cap.london_children,
                cap.has_children,
                cap.london_no_children,
                cap.no_children,
            ],
        )
        exempt = benunit("is_benefit_cap_exempt", period.this_month)
        cap = where(exempt, np.inf * np.ones_like(children), rate)
        return cap


class is_benefit_cap_exempt(Variable):
    value_type = bool
    entity = BenUnit
    label = u"Whether exempt from the benefits cap"
    definition_period = MONTH

    def formula(benunit, period, parameters):
        QUAL_PERSONAL_BENEFITS = [
            "carers_allowance",
            "DLA_SC",
            "DLA_M",
            "ESA_contrib",
        ]
        QUAL_BENUNIT_BENEFITS = ["working_tax_credit", "ESA_income"]
        qualifying = (
            aggr(benunit, period, QUAL_PERSONAL_BENEFITS, options=[MATCH])
            + add(benunit, period, QUAL_BENUNIT_BENEFITS, options=[MATCH])
            > 0
        )
        earnings = aggr(benunit, period, ["post_tax_income"], options=[DIVIDE])
        earnings_qual = earnings > 604
        return earnings_qual + qualifying
