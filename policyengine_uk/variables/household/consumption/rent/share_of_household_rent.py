from policyengine_uk.model_api import *


class share_of_household_rent(Variable):
    value_type = float
    entity = BenUnit
    label = "Share of the household's rent"
    documentation = (
        "The share of the household's rent this family is liable for: the "
        "people liable for it in this family over all the people liable for "
        "it (UC Regs 2013 Sch 4 para 24(4): A / B x C; HB Regs 2006 reg "
        "12B(4)). The household head's family has the whole rent unless other "
        "families are liable for a share."
    )
    definition_period = YEAR
    unit = "/1"
    reference = (
        "https://www.legislation.gov.uk/uksi/2013/376/schedule/4/paragraph/24",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/12B",
    )

    def formula(benunit, period, parameters):
        person = benunit.members
        liable = person("is_liable_for_household_rent", period)
        liable_people = benunit.max(person.household.sum(liable))
        head_family = benunit.any(person("is_household_head", period))
        return where(
            liable_people > 0,
            benunit.sum(liable) / max_(liable_people, 1),
            head_family,
        )
