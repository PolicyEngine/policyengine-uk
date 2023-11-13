from policyengine_uk import Microsimulation
from policyengine_uk.data.datasets import UKMOD_FRS_2018
from policyengine_uk.data.storage import STORAGE_FOLDER
import pandas as pd
import numpy as np
import pytest

SKIP_UKMOD_TESTS = True

if not SKIP_UKMOD_TESTS:
    ukmod_output = pd.read_csv(
        STORAGE_FOLDER / "uk_2018_std.txt", delimiter="\t"
    )
    ukmod_input = pd.read_csv(
        STORAGE_FOLDER / "uk_2018_a4.txt", delimiter="\t"
    )
    output_columns = [
        column
        for column in ukmod_output.columns
        if column not in ukmod_input.columns
    ]
    ukmod = pd.merge(
        ukmod_output[output_columns + ["idperson"]],
        ukmod_input,
        on="idperson",
        how="right",
    )

    UKMOD_FRS_2018().generate()
    sim = Microsimulation(dataset="ukmod_frs_2018")


@pytest.mark.skip(reason="UKMOD data not publicly shareable")
def test_ni_class_1():
    # NI Class 1 income matches.
    assert np.allclose(
        sim.calculate("ni_class_1_income").values,
        ukmod.il_empniearns.values * 12,
        atol=1,
    )


@pytest.mark.skip(reason="UKMOD data not publicly shareable")
def test_ni_class_1_employee():
    # NI contributions are off by more because the thresholds change mid-year,
    # and PolicyEngine simulates over the full year while UKMOD simulates one
    # month.
    assert np.allclose(
        sim.calculate("ni_class_1_employee").values,
        ukmod.tscee_s.values * 12,
        atol=50,
    )


@pytest.mark.skip(reason="UKMOD data not publicly shareable")
def test_ni_self_employed():
    # NI self-employed contributions don't match entirely for people with both
    # self-employed and employment income. This might be due to a different
    # interpretation of the rules around capped NI contributions (our Class 4
    # maximum uses the legislation as a reference).

    error = np.abs(
        sim.calculate("ni_self_employed").values - ukmod.tscse_s.values * 12
    )

    assert (error < 50).mean() > 0.99
