from policyengine_uk.model_api import *


class tax_free_childcare_work_condition(Variable):
    value_type = bool
    entity = Person
    label = "work conditions for tax-free childcare"
    documentation = (
        "The person applying and, if they have one, their partner must each "
        "be at least 16 and in qualifying paid work. A person counts as in "
        "qualifying paid work while on qualifying leave or statutory pay "
        "(regs 12 and 14), or while they receive a caring or incapacity "
        "benefit and their partner is in qualifying paid work (reg 13). "
        "Children in the family play no part."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/ukpga/2014/28/section/3",
        "https://www.legislation.gov.uk/ukpga/2014/28/section/6",
        "https://www.legislation.gov.uk/uksi/2015/448/regulation/3",
        "https://www.legislation.gov.uk/uksi/2015/448/regulation/9",
        "https://www.legislation.gov.uk/uksi/2015/448/regulation/13",
    )

    def formula(person, period, parameters):
        benunit = person.benunit
        # The person applying and their partner (Childcare Payments Act 2014
        # s.3(1), s.6; SI 2015/448 reg 3).
        claimant_or_partner = person("is_claimant_or_partner", period)

        in_qualifying_paid_work = person(
            "tax_free_childcare_treated_as_in_work", period
        ) | person("tax_free_childcare_regarded_as_in_paid_work", period)
        meets_condition = person("over_16", period) & in_qualifying_paid_work

        # Reported on the applicant and partner; their children play no part.
        return claimant_or_partner & benunit.all(meets_condition | ~claimant_or_partner)
