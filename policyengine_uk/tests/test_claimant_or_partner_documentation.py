from policyengine_uk import CountryTaxBenefitSystem


def test_claimant_or_partner_documentation_reaches_variable_metadata():
    variable = CountryTaxBenefitSystem().get_variable("is_claimant_or_partner")
    documentation = (variable.documentation or "").strip()
    assert documentation.startswith("The single adult or couple a benefit unit")
    assert "SSCBA 1992 s.137(1)" in documentation
    assert "Any further adults are neither claimant nor partner." in documentation
