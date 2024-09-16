from policyengine_uk.model_api import *


class TaxBand(Enum):
    NONE = "None"
    STARTER = "Starter (Scottish rates)"
    BASIC = "Basic"
    INTERMEDIATE = "Intermediate (Scottish rates)"
    HIGHER = "Higher"
    ADDITIONAL = "Additional"


class tax_band(Variable):
    value_type = Enum
    possible_values = TaxBand
    default_value = TaxBand.NONE
    entity = Person
    label = "Tax band of the individual"
    definition_period = YEAR
    reference = dict(
        title="Income Tax Act 2007, s. 10",
        href="https://www.legislation.gov.uk/ukpga/2007/3/section/10",
    )

    def formula(person, period, parameters):
        allowances = person("allowances", period)
        ani = person("adjusted_net_income", period)
        rates = parameters(period).gov.hmrc.income_tax.rates
        basic = allowances + rates.uk.thresholds[0]
        higher = allowances + rates.uk.thresholds[-2]
        add = allowances + rates.uk.thresholds[-1]
        return select(
            [ani >= add, ani >= higher, ani > basic],
            [TaxBand.ADDITIONAL, TaxBand.HIGHER, TaxBand.BASIC],
            default=TaxBand.NONE,
        )

    def formula_2017_04_06(person, period, parameters):
        allowances = person("allowances", period)
        ani = person("adjusted_net_income", period)
        rates = parameters(period).gov.hmrc.income_tax.rates
        scot = person("pays_scottish_income_tax", period)
        income = ani - allowances
        uk_band = select(
            [income < threshold for threshold in rates.uk.thresholds[:3]],
            [TaxBand.NONE, TaxBand.BASIC, TaxBand.HIGHER],
            default=TaxBand.ADDITIONAL,
        )
        scottish_band = select(
            [
                income < threshold
                for threshold in rates.scotland.rates.thresholds[:3]
            ],
            [TaxBand.NONE, TaxBand.BASIC, TaxBand.HIGHER],
            default=TaxBand.ADDITIONAL,
        )
        return where(scot, scottish_band, uk_band)

    def formula_2018_06_01(person, period, parameters):
        allowances = person("allowances", period)
        ani = person("adjusted_net_income", period)
        rates = parameters(period).gov.hmrc.income_tax.rates
        scot = person("pays_scottish_income_tax", period)
        income = ani - allowances
        uk_band = select(
            [income < threshold for threshold in rates.uk.thresholds[:3]],
            [TaxBand.NONE, TaxBand.BASIC, TaxBand.HIGHER],
            default=TaxBand.ADDITIONAL,
        )
        scottish_band = select(
            [
                income < threshold
                for threshold in rates.scotland.rates.thresholds[:5]
            ],
            [
                TaxBand.NONE,
                TaxBand.STARTER,
                TaxBand.BASIC,
                TaxBand.INTERMEDIATE,
                TaxBand.HIGHER,
            ],
            default=TaxBand.ADDITIONAL,
        )
        return where(scot, scottish_band, uk_band)
