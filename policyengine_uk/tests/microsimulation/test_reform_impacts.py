"""
Test suite for PolicyEngine UK reform fiscal impacts.
This file tests that model changes don't unexpectedly change reform impacts.
"""

import pytest
import yaml
from pathlib import Path
from policyengine_uk import Microsimulation


# Load configuration from YAML file
config_path = Path(__file__).parent / "reforms_config.yaml"
with open(config_path, "r") as f:
    config = yaml.safe_load(f)

reforms_data = config["reforms"]

# Initialize baseline simulation
baseline = Microsimulation()


def get_fiscal_impact(reform: dict) -> float:
    """
    Calculate the fiscal impact of a reform in billions.

    Args:
        reform: Dictionary of reform parameters

    Returns:
        Fiscal impact in billions (positive = revenue increase)
    """
    baseline_revenue = baseline.calculate("gov_balance", 2029).sum()
    reform_simulation = Microsimulation(reform=reform)
    reform_revenue = reform_simulation.calculate("gov_balance", 2029).sum()
    return (reform_revenue - baseline_revenue) / 1e9


# Extract test parameters from configuration
test_params = [
    (reform["parameters"], reform["name"], reform["expected_impact"])
    for reform in reforms_data
]

reform_names = [reform["name"] for reform in reforms_data]


@pytest.mark.parametrize(
    "reform, reform_name, expected_impact",
    test_params,
    ids=reform_names,
)
def test_reform_fiscal_impacts(reform, reform_name, expected_impact):
    """Test that each reform produces the expected fiscal impact."""
    impact = get_fiscal_impact(reform)

    # Allow for small numerical differences (0.1 billion tolerance)
    assert (
        abs(impact - expected_impact) < 0.1
    ), f"Impact for {reform_name} is {impact:.1f} billion, expected {expected_impact:.1f} billion"


def test_config_file_exists():
    """Test that the configuration file exists and is valid."""
    assert config_path.exists(), "reforms_config.yaml file not found"
    assert "reforms" in config, "reforms key not found in configuration"
    assert len(config["reforms"]) > 0, "No reforms defined in configuration"


def test_all_reforms_have_required_fields():
    """Test that all reforms have the required fields."""
    required_fields = ["name", "expected_impact", "parameters"]

    for i, reform in enumerate(reforms_data):
        for field in required_fields:
            assert (
                field in reform
            ), f"Reform {i} missing required field: {field}"

        assert isinstance(
            reform["parameters"], dict
        ), f"Reform {i} parameters must be a dictionary"
        assert len(reform["parameters"]) > 0, f"Reform {i} has no parameters"
