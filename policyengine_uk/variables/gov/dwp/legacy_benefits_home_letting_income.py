from policyengine_uk.model_api import *


class legacy_benefits_home_letting_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Rent from letting part of the home counted in the legacy means tests"
    documentation = (
        "Rent the benefit unit receives for letting part of the home it lives "
        "in, after the weekly disregards. The legacy means tests treat other "
        "income derived from capital, such as rent from other property, "
        "interest and dividends, as capital, but the home is disregarded "
        "capital, so rent for part of it stays income. Three sources count. "
        "(1) Rent from a sub-tenant outside the household (sublet_income), "
        "less the sub-tenant disregard; the data give one annual amount and "
        "no count of occupiers, so the model assumes one. (2) Rent from "
        "lodgers in the household, paid to the household head, less the same "
        "disregard: per person for claimants over the qualifying age for "
        "State Pension Credit, whose rules disregard 'the amount paid by that "
        "person', and per lodger family for working-age claimants, whose "
        "rules aggregate payments by 'that person or a member of his family'. "
        "(3) Payments for board and lodging, paid to the household head, less "
        "the board and lodging disregard for each boarder: the first £20 a "
        "week and half the excess."
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        "https://www.legislation.gov.uk/uksi/1987/1967/schedule/9/paragraph/19",
        "https://www.legislation.gov.uk/uksi/1987/1967/schedule/9/paragraph/20",
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/5/paragraph/22",
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/5/paragraph/42",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/29",
        "https://www.legislation.gov.uk/uksi/2006/214/schedule/5/paragraph/9",
        "https://www.legislation.gov.uk/uksi/2006/214/schedule/5/paragraph/10",
        "https://www.legislation.gov.uk/uksi/2002/1792/regulation/15",
        "https://www.legislation.gov.uk/uksi/2002/1792/schedule/IV/paragraph/8",
        "https://www.legislation.gov.uk/uksi/2002/1792/schedule/IV/paragraph/9",
    ]

    def formula(benunit, period, parameters):
        p = parameters(period).gov.dwp.legacy_means_tests
        sub_tenant = p.sub_tenant_rent_disregard
        board = p.board_and_lodging_disregard
        person = benunit.members
        pension_age = benunit.any(person("is_SP_age", period))

        weekly_sublet = add(benunit, period, ["sublet_income"]) / WEEKS_IN_YEAR
        sublet_disregard = where(
            pension_age, sub_tenant.pension_age, sub_tenant.working_age
        )
        counted_sublet = max_(0, weekly_sublet - sublet_disregard)

        # Boarders and lodgers are household members outside the head's
        # benefit unit; what each pays is counted for the head's benefit unit.
        head = person("is_household_head", period)
        pays_head = ~person.benunit.any(head)
        boarder = person("rent_paid_as_boarder", period) / WEEKS_IN_YEAR * pays_head
        lodger = person("rent_paid_as_lodger", period) / WEEKS_IN_YEAR * pays_head
        counted_board = (1 - board.excess_rate) * max_(0, boarder - board.amount)
        counted_lodger_pension_age = max_(0, lodger - sub_tenant.pension_age)
        family_lodger = person.benunit.sum(lodger)
        family_share = np.divide(
            lodger,
            family_lodger,
            out=np.zeros_like(lodger),
            where=family_lodger > 0,
        )
        counted_lodger_working_age = (
            max_(0, family_lodger - sub_tenant.working_age) * family_share
        )
        household = person.household
        from_occupiers = where(
            pension_age,
            benunit.max(household.sum(counted_board + counted_lodger_pension_age)),
            benunit.max(household.sum(counted_board + counted_lodger_working_age)),
        )
        # The head's benefit unit receives it; split by heads if more than one.
        head_share = benunit.sum(head) / max_(benunit.max(household.sum(head)), 1)
        return (counted_sublet + from_occupiers * head_share) * WEEKS_IN_YEAR
