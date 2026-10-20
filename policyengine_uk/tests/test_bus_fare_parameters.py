"""Bus fare parameters agree with each other and with the facts they encode."""

import datetime
from pathlib import Path

import pytest
import yaml

from policyengine_uk.system import system
from policyengine_uk.utils.scenario import Scenario
from policyengine_uk import Simulation

BUS_PARAMETERS = Path(__file__).parents[1] / "parameters" / "gov" / "dft" / "bus"


def last_published_quarter():
    """The first day of the last quarter in the published fares index, and
    the day after it ends."""
    raw = yaml.safe_load((BUS_PARAMETERS / "local_bus_fares_index.yaml").read_text())
    areas = {key: values for key, values in raw.items() if key.isupper()}
    starts = {max(values) for values in areas.values()}
    # DfT publishes every area's quarter in the same release.
    assert len(starts) == 1, starts
    (start,) = starts
    month = start.month + 3
    end = datetime.date(start.year + month // 13, (month - 1) % 12 + 1, 1)
    return start, end


def test_reference_cap_is_the_cap_the_published_index_reflects():
    start, end = last_published_quarter()
    assert (start, end) == (datetime.date(2026, 1, 1), datetime.date(2026, 4, 1))
    bus = system.parameters.gov.dft.bus
    changes = sorted(
        {
            datetime.date.fromisoformat(value.instant_str)
            for schedule in (bus.fares.cap, bus.reference_fares.cap)
            for value in schedule.values_list
        }
    )
    held = bus.reference_fares(start.isoformat()).cap
    for day in changes + [start, end]:
        reference = bus.reference_fares(day.isoformat()).cap
        if day < end:
            # Up to the last published quarter, the index reflects the cap
            # in force.
            assert reference == bus.fares(day.isoformat()).cap, day
        else:
            # After it, the index holds the cap of that quarter.
            assert reference == held, day


def test_removed_reference_year_gives_directions():
    with pytest.raises(ValueError) as error:
        Simulation(
            situation={"people": {"person": {"age": {2025: 30}}}},
            scenario=Scenario(
                parameter_changes={"gov.dft.bus.reference_year": {"2025": 2025}}
            ),
        )
    message = str(error.value)
    assert "gov.dft.bus.reference_year has been removed" in message
    assert "gov.dft.bus.benchmark_year" in message
    assert "gov.dft.bus.fares.cap" in message
