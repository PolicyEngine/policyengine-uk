from policyengine_uk.model_api import *


class wales_childcare_offer_per_child(Variable):
    value_type = float
    entity = Person
    label = "Childcare Offer for Wales funded childcare for this child"
    documentation = (
        "The annual value, at the Welsh Government's hourly rate to "
        "providers, of the childcare element of the Childcare Offer for "
        "Wales for this child. In the 39 term-time weeks the Offer's 30 "
        "hours include the local authority's nursery education hours, so "
        "the childcare element is the rest; in the 9 holiday weeks all 30 "
        "hours are childcare (guidance paras 6 to 9). Hours are limited by "
        "the child's weekly use of funded hours. Nursery education is "
        "funded by local authorities and is not counted here."
    )
    definition_period = YEAR
    unit = GBP
    defined_for = "wales_childcare_offer_eligible"
    reference = "https://www.gov.wales/sites/default/files/publications/2026-04/childcare-offer-for-wales-guidance-for-local-authorities-april-2026-english_0.pdf"

    def formula(person, period, parameters):
        p = parameters(period).gov.welsh_government.childcare_offer
        qualifying_child = person("wales_childcare_offer_qualifying_child", period)
        hours_used = min_(
            person("max_free_entitlement_hours_used", period), p.hours.total
        )
        term_time_childcare_hours = max_(hours_used - p.hours.nursery_education, 0)
        annual_hours = (
            term_time_childcare_hours * p.weeks.term_time + hours_used * p.weeks.holiday
        )
        return qualifying_child * annual_hours * p.hourly_rate
