from policyengine_uk.model_api import *


class tax_free_childcare_work_condition(Variable):
    value_type = bool
    entity = Person
    label = "work conditions for tax-free childcare"
    documentation = (
        "The person applying and, if they have one, their partner must each "
        "be at least 16 and in qualifying paid work. This includes ordinary "
        "paid work, explicitly qualified regulation 12 temporary absences, "
        "or caring or incapacity while a partner is in qualifying paid work "
        "under regulation 13. Legacy leave/pay facts and regulation 14's "
        "separate childcare-cost connection rule alone do not establish "
        "eligibility work. Children in the family play no part."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/ukpga/2014/28/section/3",
        "https://www.legislation.gov.uk/ukpga/2014/28/section/6",
        "https://www.legislation.gov.uk/uksi/2015/448/regulation/3",
        "https://www.legislation.gov.uk/uksi/2015/448/regulation/9",
        "https://www.legislation.gov.uk/uksi/2015/448/regulation/12",
        "https://www.legislation.gov.uk/uksi/2015/448/regulation/13",
        "https://www.legislation.gov.uk/uksi/2015/448/regulation/14",
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
