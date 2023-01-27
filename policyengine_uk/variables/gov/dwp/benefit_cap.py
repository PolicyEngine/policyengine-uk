from policyengine_uk.model_api import *


class benefit_cap(Variable):
    value_type = float
    entity = BenUnit
    label = "Benefit cap for the family"
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        has_children = benunit("num_children", period) > 0
        household_region = benunit.members.household("region", period)
        region = benunit.value_from_first_person(household_region)
        regions = household_region.possible_values
        in_london = region == regions.LONDON
        cap = parameters(period).gov.dwp.benefit_cap
        weekly_rate = select(
            [
                has_children & in_london,
                has_children & ~in_london,
                ~has_children & in_london,
                ~has_children & ~in_london,
            ],
            [
                cap.london_children,
                cap.has_children,
                cap.london_no_children,
                cap.no_children,
            ],
        )
        rate = weekly_rate * WEEKS_IN_YEAR
        exempt = benunit("is_benefit_cap_exempt", period)
        return where(exempt, np.inf * np.ones_like(has_children), rate)


class is_benefit_cap_exempt(Variable):
    value_type = bool
    entity = BenUnit
    label = "Whether exempt from the benefits cap"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        QUAL_PERSONAL_BENEFITS = [
            "carers_allowance",
            "dla",
            "ESA_contrib",
        ]
        QUAL_BENUNIT_BENEFITS = ["working_tax_credit", "ESA_income"]
        qualifying_benunit_benefits = add(
            benunit, period, QUAL_BENUNIT_BENEFITS
        )
        qualifying_personal_benefits = add(
            benunit, period, QUAL_PERSONAL_BENEFITS
        )
        return (qualifying_personal_benefits + qualifying_benunit_benefits) > 0


class benefit_cap_reduction(Variable):
    label = "benefit cap reduction"
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(benunit, period, parameters):
        CAPPED_BENEFITS = [
            "child_benefit",
            "child_tax_credit",
            "JSA_income",
            "income_support",
            "ESA_income",
            "universal_credit_pre_benefit_cap",
            "housing_benefit_pre_benefit_cap",
            "JSA_contrib",
            "incapacity_benefit",
            "ESA_contrib",
            "sda",
        ]
        return max_(
            add(benunit, period, CAPPED_BENEFITS)
            - benunit("benefit_cap", period),
            0,
        )
