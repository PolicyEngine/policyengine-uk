from policyengine_uk.model_api import *


class is_responsible_for_child_or_young_person_for_uc_or_housing_benefit(Variable):
    """Responsible for a child or young person under UC or Housing Benefit rules.

    The LHA shared accommodation tests read this. UC counts a child or
    qualifying young person (UC Regs 2013 regs 4-5); Housing Benefit counts a
    child or young person, whose young-person test follows Child Benefit (HB
    Regs 2006 regs 2, 19). A member who is a dependant under one scheme only
    is, under the other, a non-dependant (UC Sch 4 para 9; HB reg 3), which
    the household composition proxy (lha_renter_has_non_dependant) does not
    identify. Either way the renter is not limited to the shared
    accommodation rate (UC Sch 4 para 28(3)-(4); HB reg 13D(2)(a)(i)), so each
    scheme's test reads responsibility under either scheme. The benefit cap
    rates, where a non-dependant does not matter, read each scheme's own
    responsibility test.

    UC reg 5(1)(a) also makes every 16-year-old a qualifying young person until
    the 1 September after their 16th birthday, whatever their education. Annual
    ages cannot place that date, so a 16-year-old in the benefit unit who is not
    a claimant or partner counts here; the UC child element does not yet model
    reg 5(1)(a).
    """

    value_type = bool
    entity = BenUnit
    label = "Responsible for a child or young person (UC or Housing Benefit)"
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/5",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/19",
    )

    def formula(benunit, period, parameters):
        person = benunit.members
        age = person("age", period)
        sixteen = (age >= 16) & (age < 17) & ~person("is_claimant_or_partner", period)
        return (
            benunit(
                "is_responsible_for_child_or_qualifying_young_person_for_universal_credit",
                period,
            )
            | benunit(
                "is_responsible_for_child_or_young_person_for_legacy_benefits", period
            )
            | benunit.any(sixteen)
        )
