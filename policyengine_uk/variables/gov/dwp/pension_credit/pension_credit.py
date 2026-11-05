from policyengine_uk.model_api import *


class pension_credit(Variable):
    label = "Pension Credit"
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = GBP
    documentation = (
        "State Pension Credit the family receives: its entitlement where it "
        "would claim (would_claim_pc), and nil where the claimant or partner "
        "has income-related ESA (claimant_or_partner_esa_income above nil). "
        "Parliament allows income-related ESA only where neither the claimant "
        "nor the other member of the couple has an entitlement to State "
        "Pension Credit (Welfare Reform Act 2007 Sch 1 para 6(1)(c) and (d)), "
        "so the two awards never meet in one couple. The ESA screen "
        "(esa_income_eligible) refuses the couple's award where the family "
        "would get Pension Credit without it. Where the family gets Pension "
        "Credit only with the award, through the higher earnings disregard "
        "for a claimant or partner in receipt of ESA (SPC Regs 2002 Sch VI "
        "para 4(1)(a)(vii)), the model pays the award, and this formula "
        "pays no Pension Credit. A member outside the couple who claims "
        "income-related ESA in their own right leaves the couple's Pension "
        "Credit unchanged: in "
        "para 6(1)(d) Parliament named only the other member of the "
        "claimant's couple. Under gov.contrib.freeze_pension_credit, the "
        "formula returns the baseline's award."
    )
    reference = (
        "https://www.legislation.gov.uk/ukpga/2002/16/contents",
        "https://www.legislation.gov.uk/ukpga/2007/5/schedule/1/paragraph/6",
    )

    def formula(benunit, period, parameters):
        entitlement = benunit("pension_credit_entitlement", period)
        would_claim = benunit("would_claim_pc", period)
        # The formula pays nothing while the couple has income-related ESA,
        # so that no couple gets both: Parliament allows the award only where
        # neither member of the couple is entitled to State Pension Credit
        # (WRA 2007 Sch 1 para 6(1)(c) and (d)).
        couple_esa = benunit("claimant_or_partner_esa_income", period)
        amount = where(couple_esa > 0, 0, entitlement * would_claim)

        freeze = parameters(period).gov.contrib.freeze_pension_credit
        baseline = benunit.simulation.baseline
        if freeze and baseline is not None:
            return baseline.populations["benunit"]("pension_credit", period)
        else:
            return amount
