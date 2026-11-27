from policyengine_uk.model_api import *
from policyengine_uk.entities import Firm


class firm_partial_exemption_recovery_share(Variable):
    label = "Share of input VAT recoverable"
    documentation = (
        "Share of the firm's input VAT it can recover under the partial "
        "exemption standard method: taxable supplies over taxable plus exempt "
        "supplies, expressed as a percentage and rounded up (SI 1995/2518 reg "
        "101(4)-(5)): to the next whole percent where input tax averages no "
        "more than £400,000 a month, otherwise to two decimal places. A firm "
        "with no supplies recovers all of its input VAT. The ratio is applied "
        "to residual input tax, which is all input VAT unless parts are "
        "supplied as directly attributable to taxable or exempt supplies, "
        "and the £400,000 test reads residual input tax (reg 101(5)). The "
        "de minimis tests are in firm_recoverable_input_vat. Special methods "
        "are not modelled; supply a value to override the default. "
        "Supplies are stored in single precision, so above about £16.7m a "
        "ratio that is a whole percentage can round one point high."
    )
    entity = Firm
    definition_period = YEAR
    value_type = float
    unit = "/1"
    reference = "https://www.legislation.gov.uk/uksi/1995/2518/regulation/101"

    def formula(firm, period, parameters):
        # Work in float64 so the rounding below is not disturbed by float32
        # error in the stored inputs' ratio.
        taxable = firm("firm_vat_taxable_turnover", period).astype(float)
        exempt = firm("firm_exempt_supplies", period).astype(float)
        total = taxable + exempt
        has_supplies = total > 0
        share = np.ones_like(total, dtype=float)
        share[has_supplies] = taxable[has_supplies] / total[has_supplies]
        # Round the percentage up to a whole number, or to two decimal places
        # above the monthly threshold. Subtract a small tolerance first so a
        # ratio that is a whole percentage in exact arithmetic is not pushed
        # up by float error.
        p = parameters(period).gov.hmrc.vat.partial_exemption
        input_vat = firm("firm_input_vat", period)
        taxable_direct = min_(
            max_(firm("firm_input_vat_attributable_to_taxable_supplies", period), 0),
            max_(input_vat, 0),
        )
        exempt_direct = min_(
            max_(firm("firm_input_vat_attributable_to_exempt_supplies", period), 0),
            max_(input_vat - taxable_direct, 0),
        )
        residual = input_vat - taxable_direct - exempt_direct
        monthly_input_vat = residual / MONTHS_IN_YEAR
        scale = where(monthly_input_vat > p.rounding_threshold, 1e4, 1e2)
        rounded = np.ceil(share * scale - 1e-6) / scale
        # Adding 0 turns the -0.0 from ceil(-1e-6) into 0.
        return np.clip(rounded, 0, 1) + 0.0
