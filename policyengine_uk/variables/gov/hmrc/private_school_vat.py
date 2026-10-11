from policyengine_uk.model_api import *


def private_school_vat_rate(gov):
    """VAT rate on private school fees under the parameters in `gov`.

    Finance Act 2025 s.47 takes education, vocational training and closely
    related board and lodging supplied by a private school out of the VAT
    Act 1994 Sch 9 Group 6 exemption (new Sch 9 Part 3), with effect for
    supplies on or after 1 January 2025 (s.49), so the fees bear the
    standard rate. The contributed reform rate can raise the rate on the
    fees but is never charged on top of the statutory rate: the fees bear
    VAT once, at the higher of the two.
    """
    vat = gov.hmrc.vat
    statutory_rate = 0 if vat.private_school_fees_exempt else vat.standard_rate
    return max_(statutory_rate, gov.contrib.labour.private_school_vat)


def private_school_vat_liability(household, period, gov):
    pupils = add(household, period, ["attends_private_school"])
    p = gov.simulation.private_school_vat
    return (
        pupils
        * p.private_school_fees
        * p.private_school_vat_basis
        * private_school_vat_rate(gov)
    )


class private_school_vat(Variable):
    label = "private school VAT"
    documentation = (
        "VAT on the household's private school fees: pupils times the mean "
        "fee times the share of fees that bears VAT net of the schools' "
        "input tax, at the standard rate from 1 January 2025."
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"
    reference = [
        "https://www.legislation.gov.uk/ukpga/2025/8/section/47/enacted",
        "https://www.legislation.gov.uk/ukpga/2025/8/section/49/enacted",
    ]

    def formula(household, period, parameters):
        return private_school_vat_liability(household, period, parameters(period).gov)
