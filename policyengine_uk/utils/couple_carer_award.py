"""Couple-only carer award selection, without reading its own final awards."""

import numpy as np

from policyengine_uk.utils.supplied_inputs import supplied_input


def _supplied_receipt(person, period, receipt_name, amount_name):
    receipt = supplied_input(person, receipt_name, period)
    if receipt is not None:
        return receipt
    amount = supplied_input(person, amount_name, period)
    return np.zeros(person.count, dtype=bool) if amount is None else amount > 0


def unlimited_carer_benefit_entitlement(person, period):
    """Keep the existing award inference independent of the couple limit.

    Direct inputs remain authoritative; cached formula results are not inputs.
    This mirrors the entitlement reader before the restriction, so the shared
    care-target default does not depend on the awards it now restricts.
    """
    supplied = supplied_input(person, "is_entitled_to_carer_benefit", period)
    if supplied is not None:
        return supplied
    amounts = []
    for name in ("carers_allowance", "carer_support_payment"):
        amount = supplied_input(person, name + "_pre_overlap", period)
        if amount is None:
            amount = person(name + "_pre_couple_limit", period)
        amounts.append(amount)
    receives = supplied_input(person, "receives_carer_benefit", period)
    if receives is None:
        receives = _supplied_receipt(
            person, period, "receives_carers_allowance", "carers_allowance"
        ) | _supplied_receipt(
            person, period, "receives_carer_support_payment", "carer_support_payment"
        )
    return (amounts[0] + amounts[1] > 0) | receives


def limit_carer_benefit_to_one_partner(person, period, candidate):
    """One candidate award for a same-target couple, before overlap reductions.

    Election/discretion is not observed. Prefer an eligible reported recipient,
    then an eligible benefit-unit head, then the eldest eligible partner (stable
    member order breaks age ties). Other members and units with other than two
    claimant/partner flags are outside this couple-only restriction.
    """
    benunit = person.benunit
    partner = person("is_claimant_or_partner", period)
    eligible = partner & (candidate > 0)
    reported = eligible & (person("carers_allowance_reported", period) > 0)
    preferred = np.where(benunit.any(reported), reported, eligible)
    head = preferred & person("is_benunit_head", period)
    preferred = np.where(benunit.any(head), head, preferred)
    rank = person.get_rank(benunit, -person("age", period), condition=preferred)
    selected = preferred & (rank == 0)
    restricted = (
        partner
        & (benunit.sum(partner) == 2)
        & benunit("partners_care_for_same_severely_disabled_person", period)
    )
    return np.where(restricted & ~selected, 0, candidate)
