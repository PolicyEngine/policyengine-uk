"""corporate_wealth's components share its entity, quantity type and uprating, so
a dataset's identity corporate_wealth == sum of components survives projection."""

from pathlib import Path

import yaml

from policyengine_uk import CountryTaxBenefitSystem

COMPONENTS = (
    "directly_held_shares",
    "unit_and_investment_trusts",
    "stocks_and_shares_isa",
)

system = CountryTaxBenefitSystem()
UPRATING_INDICES = yaml.safe_load(
    (Path(__file__).parents[1] / "data" / "uprating_indices.yaml").read_text()
)


def _uprating_index(variable):
    return [index for index, names in UPRATING_INDICES.items() if variable in names]


def test_components_match_corporate_wealth():
    corporate_wealth = system.variables["corporate_wealth"]
    for name in COMPONENTS:
        variable = system.variables[name]
        assert variable.is_input_variable()
        assert variable.entity.key == corporate_wealth.entity.key
        assert variable.quantity_type == corporate_wealth.quantity_type
        assert variable.uprating == corporate_wealth.uprating
        assert _uprating_index(name) == _uprating_index("corporate_wealth")


def test_cash_isa_is_uprated_with_savings():
    assert system.variables["cash_isa"].uprating == system.variables["savings"].uprating
    assert _uprating_index("cash_isa") == _uprating_index("savings")


def test_components_are_not_part_of_total_wealth():
    """total_wealth adds corporate_wealth, which already holds the components."""
    adds = system.variables["total_wealth"].adds
    assert "corporate_wealth" in adds
    assert not set(COMPONENTS) & set(adds)
