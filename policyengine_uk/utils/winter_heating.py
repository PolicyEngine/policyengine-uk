"""Person-level rules shared by the Winter Fuel Payment and the Pension Age
Winter Heating Payment.

Both schemes entitle and pay a person, and set the amount from that person's
own circumstances:

- a person to whom a relevant benefit is paid receives the full amount, the
  higher amount if they or their partner have reached 80 (SI 2000/729 reg
  2(1)(i) and 2(3); SI 2024/869 reg 3; SI 2025/969 reg 3(1), (3) and (4);
  SSI 2024/351 reg 10, as made and as substituted by SSI 2025/282);
- a couple on a relevant benefit receives one payment: the partner of the
  person paid is not entitled (SI 2000/729 reg 3(1)(a)(i); SI 2024/869 reg
  4(1)(a)(i); SI 2025/969 reg 4(2)(a); SSI 2024/351 reg 9(d));
- anyone else receives a shared amount when they live with another person
  entitled to a payment (SI 2000/729 reg 2(1)(ii) and 2(2)(b); SI 2025/969
  reg 3(2), (5) and (6); SSI 2024/351 reg 10(5) and (6) as substituted).

Benefit units model couples and households model living together: everyone
in a household is taken to share it as their mutual home. Residential care,
long hospital stays and custody are not modelled.
"""

from policyengine_core.model_api import select, where


def is_excluded_relevant_benefit_partner(
    person, period, qualifies, on_relevant_benefit
):
    """Whether the person is the partner of the person paid for their couple.

    A couple on a relevant benefit receives one payment. The model pays the
    eldest member of the couple who qualifies (the claimant and partner of a
    benefit unit whose award is a relevant benefit) and excludes the other;
    the amount is the same whichever member is paid.
    """
    age = person("age", period)
    couple_member = (
        qualifies & person("is_claimant_or_partner", period) & on_relevant_benefit
    )
    payee = couple_member & (
        person.get_rank(person.benunit, -age, condition=couple_member) == 0
    )
    return couple_member & ~payee


def winter_heating_payment_amount(
    person, period, eligible, on_relevant_benefit, amount, higher_age
):
    """The amount payable to each eligible person.

    ``amount`` is the scheme's amount parameter node, with ``lower`` and
    ``higher`` (full amounts under and over the higher age), ``lower_shared``,
    ``higher_shared_with_under_80`` and ``higher_shared_with_80_or_over``.
    A person living with another eligible person who has reached the higher
    age receives ``higher_shared_with_80_or_over`` even if they also live with
    one who has not (SI 2025/969 reg 3(5) is subject to reg 3(6)).
    """
    age = person("age", period)
    aged_80 = age >= higher_age
    claimant_or_partner = person("is_claimant_or_partner", period)
    couple_aged_80 = claimant_or_partner & person.benunit.any(
        claimant_or_partner & aged_80
    )
    relevant_benefit_amount = where(
        aged_80 | couple_aged_80, amount.higher, amount.lower
    )
    others = person.household.sum(eligible) - eligible
    others_aged_80 = person.household.sum(eligible & aged_80) - (eligible & aged_80)
    under_80_amount = where(others > 0, amount.lower_shared, amount.lower)
    aged_80_amount = select(
        [others_aged_80 > 0, others > 0],
        [amount.higher_shared_with_80_or_over, amount.higher_shared_with_under_80],
        default=amount.higher,
    )
    other_amount = where(aged_80, aged_80_amount, under_80_amount)
    return eligible * where(on_relevant_benefit, relevant_benefit_amount, other_amount)
