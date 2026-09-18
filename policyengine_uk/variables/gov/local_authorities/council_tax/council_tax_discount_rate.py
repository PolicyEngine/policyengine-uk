from policyengine_uk.model_api import *


class council_tax_discount_rate(Variable):
    value_type = float
    entity = Household
    label = "Council tax statutory discount rate"
    documentation = (
        "The statutory council tax discount as a proportion of the gross "
        "liability, under section 11 of the Local Government Finance Act 1992 "
        "(England). Section 11(1) gives the appropriate percentage where there "
        "is only one resident of the dwelling who is not disregarded, and "
        "section 11(2) gives twice the appropriate percentage where there is no "
        "such resident. The appropriate percentage is 25 per cent under section "
        "11(3) unless the Secretary of State orders otherwise, so the familiar "
        "50 per cent rate is derived here as twice the parameter rather than "
        "set independently.\n\n"
        "A resident is defined by section 6(5) as an individual aged 18 or over "
        "who has their sole or main residence in the dwelling, so the adult "
        "count is the statutory test rather than an approximation. However, the "
        "Schedule 1 disregarded-person categories (students, the severely "
        "mentally impaired, carers, and others) are NOT yet modelled. Residents "
        "are therefore treated as never disregarded. This overstates the number "
        "of counting residents, so this variable understates discounts for "
        "households containing disregarded adults: a household of two adults "
        "where one is disregarded should receive the 25 per cent discount and "
        "receives none here, and a household whose only adults are all "
        "disregarded should receive 50 per cent and receives none here. Adding "
        "Schedule 1 will change these results.\n\n"
        "Only England is in scope here. Part I of the Act also applies to "
        "Wales, but the Welsh provisions (sections 12 and 12A to 12B, giving "
        "Welsh Ministers separate powers over unoccupied and second homes) have "
        "not been verified in this work; Scotland is under section 79. The "
        "discount is therefore zero outside England pending that work."
    )
    definition_period = YEAR
    unit = "/1"

    def formula(household, period, parameters):
        # LGFA 1992 s.6(5): a resident is an individual aged 18 or over whose
        # sole or main residence is the dwelling. Schedule 1 disregards are not
        # modelled, so every resident adult is counted (see documentation).
        residents = household.sum(household.members("is_adult", period))
        p = parameters(
            period
        ).gov.local_authorities.council_tax.discounts.appropriate_percentage

        single_resident_rate = p  # s.11(1): the appropriate percentage
        no_resident_rate = 2 * p  # s.11(2): twice the appropriate percentage

        rate = where(
            residents == 0,
            no_resident_rate,
            where(residents == 1, single_resident_rate, 0),
        )
        country = household("country", period).decode_to_str()
        return where(country == "ENGLAND", rate, 0)
