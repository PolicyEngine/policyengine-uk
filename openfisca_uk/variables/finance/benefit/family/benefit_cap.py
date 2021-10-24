from openfisca_uk.tools.general import *
from openfisca_uk.entities import *


class benefit_cap(Variable):
    value_type = float
    entity = BenUnit
    label = u"Benefit cap for the family"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        children = benunit("num_children", period) > 0
        region = benunit.value_from_first_person(
            benunit.members.household("region", period)
        )
        regions = benunit.members.household("region", period).possible_values
        in_london = region == regions.LONDON
        cap = parameters(period).benefit.benefit_cap
        rate = (
            select(
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
            * WEEKS_IN_YEAR
        )
        exempt = benunit("is_benefit_cap_exempt", period)
        cap = where(exempt, np.inf * np.ones_like(children), rate)
        return cap


class is_benefit_cap_exempt(Variable):
    value_type = bool
    entity = BenUnit
    label = u"Whether exempt from the benefits cap"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        QUAL_PERSONAL_BENEFITS = [
            "carers_allowance",
            "DLA_SC",
            "DLA_M",
            "ESA_contrib",
        ]
        qualifying = (
            add(benunit, period, ["working_tax_credit"])
            + add(benunit, period, ["ESA_income"])
            + aggr(benunit, period, QUAL_PERSONAL_BENEFITS)
            > 0
        )
        return qualifying
