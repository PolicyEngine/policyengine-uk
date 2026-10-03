from policyengine_uk.model_api import *


class carer_premium(Variable):
    value_type = float
    entity = BenUnit
    label = "Carer premium"
    documentation = (
        "The legacy benefits' carer premium: one amount for each claimant or "
        "partner entitled to Carer's Allowance or Carer Support Payment "
        "(is_entitled_to_carer_benefit), including an entitlement reduced to "
        "nil by an overlapping benefit. Caring hours alone, without a claim, "
        "do not qualify, and a child or young person in the family who cares "
        "does not qualify the family. A couple who are both entitled get the "
        "amount twice if they care for different people, and once if they "
        "care for the same severely disabled person "
        "(partners_care_for_same_severely_disabled_person, which by default "
        "treats them as caring for the same person unless both are entitled "
        "with a reported Carer's Allowance or Carer Support Payment award). "
        "Members flagged as claimant or partner "
        "beyond two (for example the partners of a polygamous marriage, "
        "supplied as inputs) each count, except that caring for the same "
        "person caps the benefit unit at one amount. The premium enters the "
        "Income Support, Housing Benefit and council tax reduction applicable "
        "amounts; the model takes income-based JSA and income-related ESA "
        "from reported awards."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/1987/1967/schedule/2/paragraph/14ZA",
        "https://www.legislation.gov.uk/uksi/1987/1967/schedule/2/paragraph/15",
        "https://www.legislation.gov.uk/uksi/1996/207/schedule/1/paragraph/17",
        "https://www.legislation.gov.uk/uksi/2008/794/schedule/4/paragraph/8",
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/3/paragraph/17",
        "https://www.legislation.gov.uk/uksi/2006/214/schedule/3/paragraph/9",
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/2/paragraph/9",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/2/paragraph/9",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/7/paragraph/14",
        "https://www.legislation.gov.uk/ssi/2012/319/schedule/1/paragraph/10",
        "https://www.legislation.gov.uk/ssi/2021/249/schedule/1/paragraph/5",
        "https://www.legislation.gov.uk/ukpga/1992/4/section/70",
        "https://www.legislation.gov.uk/ssi/2023/302/regulation/5",
    )
    unit = GBP

    def formula(benunit, period, parameters):
        # IS Regs 1987 Sch 2 para 14ZA(1): "the claimant or his partner is, or
        # both of them are, entitled to a carer's allowance ... or carer
        # support payment". Para 15(7) pays the premium "in respect of each
        # person who satisfied the condition". The JSA, ESA and HB schedules,
        # the English, Welsh and Scottish pension-age council tax reduction
        # schedules and Welsh working-age council tax reduction (WSI 2013/3029
        # Sch 7 para 14) use the same condition and amount; Scottish
        # working-age council tax reduction (SSI 2021/249 Sch 1 paras 5-6)
        # tests caring responsibilities, which include receiving either
        # allowance or being entitled to one reduced to nil by the overlapping
        # benefits rules, and pays each partner who qualifies.
        claimant_or_partner = benunit.members("is_claimant_or_partner", period)
        entitled = benunit.members("is_entitled_to_carer_benefit", period)
        qualifying_carers = benunit.sum(claimant_or_partner & entitled)
        # Two people caring for the same severely disabled person cannot both
        # be entitled to Carer's Allowance (SSCBA s.70(7ZA)) or Carer Support
        # Payment (SSI 2023/302 reg 5(3)); SSI 2021/249 Sch 1 para 5(3)-(4)
        # pays one premium in that case too.
        same_person = benunit("partners_care_for_same_severely_disabled_person", period)
        qualifying_carers = where(
            same_person, min_(qualifying_carers, 1), qualifying_carers
        )
        amount = parameters(period).gov.dwp.carer_premium.single
        return qualifying_carers * amount * WEEKS_IN_YEAR
