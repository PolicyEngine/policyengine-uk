import pytest
import numpy as np
from policyengine_uk import CountryTaxBenefitSystem


def test_firm_turnover_variable():
    """Test that firm_turnover variable exists and works correctly."""
    system = CountryTaxBenefitSystem()

    # Check variable exists
    assert "firm_turnover" in system.variables

    variable = system.variables["firm_turnover"]
    assert variable.value_type == float
    assert variable.entity.key == "firm"
    assert variable.label == "Firm turnover"


def test_firm_vat_registered_variable():
    """Test that firm_vat_registered variable exists and calculates correctly."""
    system = CountryTaxBenefitSystem()

    # Check variable exists
    assert "firm_vat_registered" in system.variables

    variable = system.variables["firm_vat_registered"]
    assert variable.value_type == bool
    assert variable.entity.key == "firm"


def test_vat_registration_threshold():
    """Test VAT registration threshold of £90,000."""
    from policyengine_uk.simulation import Simulation

    # Test firm below threshold
    sim_below = Simulation(
        situation={
            "firms": {"test_firm": {"firm_turnover": {"2024": 85_000}}},
            "people": {"p": {}},
            "benunits": {"b": {"members": ["p"]}},
            "households": {"h": {"members": ["p"]}},
        }
    )
    vat_registered = sim_below.calculate("firm_vat_registered", "2024")
    assert vat_registered[0] == False

    # Test firm above threshold
    sim_above = Simulation(
        situation={
            "firms": {"test_firm": {"firm_turnover": {"2024": 95_000}}},
            "people": {"p": {}},
            "benunits": {"b": {"members": ["p"]}},
            "households": {"h": {"members": ["p"]}},
        }
    )
    vat_registered = sim_above.calculate("firm_vat_registered", "2024")
    assert vat_registered[0] == True


def test_firm_vat_on_sales():
    """Test VAT calculation on firm sales."""
    from policyengine_uk.simulation import Simulation

    simulation = Simulation(
        situation={
            "firms": {
                "firm_1": {
                    "firm_turnover": {"2024": 100_000},
                    "firm_standard_rated_supplies": {"2024": 80_000},
                    "firm_reduced_rated_supplies": {"2024": 10_000},
                    "firm_zero_rated_supplies": {"2024": 10_000},
                }
            },
            "people": {"p": {}},
            "benunits": {"b": {"members": ["p"]}},
            "households": {"h": {"members": ["p"]}},
        }
    )

    vat_on_sales = simulation.calculate("firm_vat_on_sales", "2024")
    # Standard rate 20% on £80,000 = £16,000
    # Reduced rate 5% on £10,000 = £500
    # Zero rate 0% on £10,000 = £0
    # Total = £16,500
    expected = 16_500
    assert np.isclose(vat_on_sales[0], expected, rtol=0.01)


def test_firm_net_vat_liability():
    """Test net VAT liability calculation (output VAT - input VAT)."""
    from policyengine_uk.simulation import Simulation

    simulation = Simulation(
        situation={
            "firms": {
                "firm_1": {
                    "firm_turnover": {"2024": 100_000},
                    "firm_standard_rated_supplies": {"2024": 100_000},
                    "firm_vat_on_purchases": {"2024": 5_000},
                }
            },
            "people": {"p": {}},
            "benunits": {"b": {"members": ["p"]}},
            "households": {"h": {"members": ["p"]}},
        }
    )

    net_vat = simulation.calculate("firm_net_vat_liability", "2024")
    # Output VAT: 20% of £100,000 = £20,000
    # Input VAT: £5,000
    # Net liability: £20,000 - £5,000 = £15,000
    expected = 15_000
    assert np.isclose(net_vat[0], expected, rtol=0.01)
