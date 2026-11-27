from policyengine_uk.model_api import *
from policyengine_uk.entities import Firm


class soft_drinks_industry_levy(Variable):
    value_type = float
    entity = Firm
    label = "Soft drinks industry levy"
    documentation = (
        "Soft drinks industry levy on the firm's chargeable soft drinks: "
        "the higher rate per litre on drinks with 8 grams or more of sugar "
        "per 100 millilitres and the lower rate on those with at least 5 "
        "grams (Finance Act 2017 s.30), from 6 April 2018. A small producer, "
        "whose and whose connected persons' chargeable drinks do not exceed "
        "1 million litres in the year, is exempt (ss.37-38); the test is "
        "applied to the firm's year. Rates are read at 30 April, so the "
        "rates from 1 April apply to the whole year. Not modelled: the "
        "milk-based drinks exemption and the reliefs for exports and "
        "dilution."
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        dict(
            title="Finance Act 2017 Part 2",
            href="https://www.legislation.gov.uk/ukpga/2017/10/part/2",
        ),
        dict(
            title="Finance Act 2025 s.79",
            href="https://www.legislation.gov.uk/ukpga/2025/8/section/79",
        ),
        dict(
            title="Finance Act 2026 s.108",
            href="https://www.legislation.gov.uk/ukpga/2026/11/section/108",
        ),
    ]

    def formula(firm, period, parameters):
        p = parameters(period).gov.hmrc.soft_drinks_industry_levy
        higher = max_(firm("firm_sdil_litres_higher_rate", period), 0)
        lower = max_(firm("firm_sdil_litres_lower_rate", period), 0)
        # A supplied 0 (for example a zero-filled column) means not supplied.
        supplied = firm("firm_sdil_annual_production_litres", period)
        production = where(supplied > 0, supplied, higher + lower)
        levy = higher * p.rate.higher + lower * p.rate.lower
        return where(production <= p.small_producer_threshold, 0, levy)
