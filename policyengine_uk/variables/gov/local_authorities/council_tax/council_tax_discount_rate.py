from policyengine_uk.model_api import *


class council_tax_discount_rate(Variable):
    value_type = float
    entity = Household
    label = "Council tax statutory discount rate"
    documentation = (
        "The statutory council tax discount as a proportion of the gross "
        "liability, applied across Great Britain. Northern Ireland uses "
        "domestic rates rather than council tax, so the rate is zero there.\n\n"
        "SINGLE-RESIDENT DISCOUNT. Each nation gives the same 25 per cent "
        "where there is only one resident who is not disregarded, but under "
        "three different provisions:\n"
        "- England: section 11(1) of the Local Government Finance Act 1992, "
        "the appropriate percentage being 25 per cent under section 11(3) "
        "unless the Secretary of State orders otherwise.\n"
        "- Scotland: section 79(1) of the same Act, the appropriate percentage "
        "being 25 per cent under section 79(3).\n"
        "- Wales: section 11(1) as it applied to England and Wales alike until "
        "31 March 2026. The Local Government Finance (Wales) Act 2024 inserted "
        "the words 'in England' into section 11 with effect from 1 April 2026 "
        "and inserted section 11E, under which the Welsh discounts are "
        "prescribed by regulations. Regulation 3 of the Council Tax "
        "(Discounts, Disregards and Exemptions) (Wales) Regulations 2026 "
        "prescribes the same 25 per cent, so the rate is continuous across "
        "that change.\n\n"
        "NO-RESIDENT DISCOUNT. Here the nations genuinely differ, so the "
        "doubling is a per-nation parameter rather than a constant:\n"
        "- England: section 11(2)(a) gives twice the appropriate percentage, "
        "so the familiar 50 per cent is derived as two times the parameter "
        "rather than set independently.\n"
        "- Scotland: section 79(2)(a) gave twice the appropriate percentage "
        "until it was repealed with effect from 1 April 2005 by regulation 2 "
        "of the Council Tax (Discount for Unoccupied Dwellings) (Scotland) "
        "Regulations 2005. From then on no discount arises under section 79 "
        "merely because a dwelling is unoccupied, so the multiple is zero.\n"
        "- Wales: section 11(2)(a) applied until 31 March 2026. From 1 April "
        "2026 the 2026 Regulations prescribe 50 per cent only where there are "
        "residents and every one of them is disregarded (regulation 4), and "
        "for an unoccupied dwelling only in the narrow caravan-pitch, "
        "boat-mooring and job-related cases (regulation 6). No general "
        "no-resident discount is prescribed, so the multiple is zero.\n\n"
        "THE NO-RESIDENT BRANCH IS UNREACHABLE ON SURVEY DATA. Every "
        "Family Resources Survey household has an adult reference person, so "
        "a household with no resident aged 18 or over does not occur in the "
        "microdata. The doubled rate therefore only ever fires on synthetic "
        "inputs, such as the household-level calculator or the policy tests "
        "below. It is retained because it is what the statute says, not "
        "because it changes any survey-based aggregate.\n\n"
        "WHO COUNTS AS A RESIDENT. Section 6(5) of the Act defines a resident "
        "as an individual aged 18 or over who has their sole or main residence "
        "in the dwelling, so counting residents as adults aged 18 or over is "
        "the statutory test rather than an approximation.\n\n"
        "WHAT IS APPROXIMATED. The disregarded-person categories (students, "
        "the severely mentally impaired, carers, and others) in Schedule 1 to "
        "the Act, and in Part 3 of the 2026 Regulations for Wales, are NOT "
        "yet modelled. Residents are therefore treated as never disregarded. "
        "This overstates the number of counting residents, so this variable "
        "understates discounts for households containing disregarded adults: a "
        "household of two adults where one is disregarded should receive the "
        "25 per cent discount and receives none here, and a household whose "
        "only adults are all disregarded should receive 50 per cent and "
        "receives none here. Adding the disregards will change these results."
    )
    definition_period = YEAR
    unit = "/1"

    def formula(household, period, parameters):
        # LGFA 1992 s.6(5): a resident is an individual aged 18 or over whose
        # sole or main residence is the dwelling. Disregards are not modelled,
        # so every resident adult is counted (see documentation).
        residents = household.sum(household.members("is_adult", period))
        discounts = parameters(period).gov.local_authorities.council_tax.discounts
        country = household("country", period).decode_to_str()

        # The appropriate percentage and the no-resident multiple are both
        # per-nation: the percentage happens to agree at 25 per cent, but the
        # multiple does not (see documentation).
        single_rate = np.zeros_like(residents, dtype=float)
        no_resident_rate = np.zeros_like(residents, dtype=float)
        for key, nation in (
            ("ENGLAND", "england"),
            ("WALES", "wales"),
            ("SCOTLAND", "scotland"),
        ):
            percentage = float(getattr(discounts.appropriate_percentage, nation))
            multiple = float(getattr(discounts.no_resident_multiple, nation))
            single_rate = np.where(country == key, percentage, single_rate)
            no_resident_rate = np.where(
                country == key, multiple * percentage, no_resident_rate
            )

        # s.11(1)/(2) for England, s.79(1)/(2) for Scotland, reg. 3 of the 2026
        # Regulations for Wales. Northern Ireland keeps the zero initialised
        # above, as it levies domestic rates rather than council tax.
        return where(
            residents == 0,
            no_resident_rate,
            where(residents == 1, single_rate, 0),
        )
