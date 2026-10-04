from policyengine_uk.model_api import *


class is_non_dependant_of_household_head(Variable):
    value_type = bool
    entity = Person
    label = "Non-dependant of the families liable for the household's rent"
    documentation = (
        "Whether this person lives in the household outside every family "
        "liable for its rent (the household head's family and any sharers) "
        "and is not liable for rent themselves. A joint tenant or other "
        "sharer of the rent, a boarder and a lodger are liable on a "
        "commercial basis for their occupation, so none is a non-dependant "
        "of anyone, and the household head's household is not a boarder's or "
        "lodger's. Universal Credit counts a non-dependant in one claim only "
        "(uc_non_dependants_counted); Housing Benefit and Council Tax "
        "Reduction apportion a non-dependant of several joint occupiers "
        "between them. Foster children and carers engaged through a charity "
        "are not identified."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2013/376/schedule/4/paragraph/9",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/3",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/3",
    )

    def formula(person, period, parameters):
        # UC Regs 2013 Sch 4 para 9(2)(d)-(f); HB Regs 2006 reg 3(2)(d)-(e)
        # and 3(4); HB (SPC) Regs 2006 reg 3.
        head_family = person.benunit.any(person("is_household_head", period))
        liable_for_rent = person.benunit("benunit_is_rent_liable", period)
        return ~head_family & ~liable_for_rent
