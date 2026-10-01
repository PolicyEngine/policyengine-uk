from policyengine_uk.model_api import *


class carer_premium(Variable):
    value_type = float
    entity = BenUnit
    label = "Carer premium"
    documentation = (
        "The legacy benefits' carer premium: one amount for each of the "
        "claimant and partner who is entitled to Carer's Allowance or Carer "
        "Support Payment (is_carer_for_benefits). A child or young person in "
        "the family who cares does not qualify the family, and a couple who "
        "both qualify get the amount twice. Scottish Council Tax Reduction "
        "pays one premium when both partners care for the same person; the "
        "model does not know who is cared for, so it pays two."
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
    )
    unit = GBP

    def formula(benunit, period, parameters):
        # IS Regs 1987 Sch 2 para 14ZA(1): "the claimant or his partner is, or
        # both of them are, entitled to a carer's allowance ... or carer
        # support payment". Para 15(7) pays the premium "in respect of each
        # person who satisfied the condition"; the JSA, ESA, HB and CTR
        # schedules use the same words.
        claimant_or_partner = benunit.members("is_claimant_or_partner", period)
        carer = benunit.members("is_carer_for_benefits", period)
        qualifying_carers = benunit.sum(claimant_or_partner & carer)
        amount = parameters(period).gov.dwp.carer_premium.single
        return qualifying_carers * amount * WEEKS_IN_YEAR
