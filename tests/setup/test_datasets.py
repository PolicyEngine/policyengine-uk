import yaml
from openfisca_uk import REPO


def test_default_dataset_is_synth_frs():
    with open(REPO / "tools" / "datasets.yml") as f:
        data = yaml.safe_load(f)
        assert data["default"] == "synth_frs"


def test_default_dataset_is_usable():
    from openfisca_uk import Microsimulation

    sim = Microsimulation()
    sim.calc("in_poverty_bhc", map_to="person")
