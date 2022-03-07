from openfisca_uk.model_api import *


class hb_personal_allowance(Variable):
    label = "HB Personal Allowance"
    documentation = "The basic element of the Housing Benefit applicable amount"
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = "https://www.legislation.gov.uk/uksi/2006/213/schedule/3"

    def formula(benunit, period, parameters):
        family_type = benunit("family_type", period)
        families = family_type.possible_values
        age = benunit("eldest_adult_age", period)
        pa = parameters(period).dwp.housing_benefit.applicable_amount.personal_allowance
        return select([
            (family_type == families.SINGLE),
            (family_type == families.LONE_PARENT),
            (family_type == families.COUPLE_NO_CHILDREN),
            (family_type == families.COUPLE_WITH_CHILDREN),
        ], [
            pa.single.calc(age),
            pa.lone_parent.calc(age),
            pa.couple.calc(age),
            pa.couple.calc(age),
        ])