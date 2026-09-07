"""Datasets must load from read-only files.

pandas opens ``HDFStore`` in append mode by default, which raises a
``PermissionError`` when the file is not writable. Datasets are routinely
read from such locations: Hugging Face cache snapshots are checked out
read-only, and shared datasets may live on read-only mounts. Loading a dataset
never writes to it, so every read path must open the store with ``mode="r"``.

The synthetic tests below need no network access. The microsimulation test
downloads the tiny enhanced FRS dataset, so it is skipped (via the
``microsimulation`` marker in ``conftest.py``) unless ``HUGGING_FACE_TOKEN``
or ``POLICYENGINE_UK_DEFAULT_DATASET`` is set.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import stat
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from policyengine_uk.data import UKMultiYearDataset, UKSingleYearDataset

TINY_DATASET_REPO = "policyengine/policyengine-uk-data-private"
TINY_DATASET_FILENAME = "enhanced_frs_2023_24_tiny.h5"
TINY_DATASET_VERSION = "1.57.2"
YEAR = 2025


def _make_read_only(path: Path) -> None:
    """Strip write permission from *path*, or skip if that has no effect.

    Running as root (some containers) ignores file permission bits, which
    would let the test pass without exercising the read-only code path.
    """
    path.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
    if os.access(path, os.W_OK):
        pytest.skip("Cannot make files read-only in this environment")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _synthetic_dataset(fiscal_year: int) -> UKSingleYearDataset:
    person = pd.DataFrame(
        {
            "person_id": [1, 2, 3],
            "person_benunit_id": [1, 1, 2],
            "person_household_id": [1, 1, 2],
            "age": [40.0, 38.0, 70.0],
        }
    )
    benunit = pd.DataFrame({"benunit_id": [1, 2]})
    household = pd.DataFrame({"household_id": [1, 2]})
    return UKSingleYearDataset(
        person=person,
        benunit=benunit,
        household=household,
        fiscal_year=fiscal_year,
    )


def test_single_year_dataset_loads_from_read_only_file(tmp_path: Path):
    path = tmp_path / "single_year.h5"
    _synthetic_dataset(YEAR).save(str(path))
    _make_read_only(path)
    digest = _sha256(path)

    loaded = UKSingleYearDataset(str(path))

    assert loaded.time_period == str(YEAR)
    assert list(loaded.person["person_id"]) == [1, 2, 3]
    assert list(loaded.household["household_id"]) == [1, 2]
    assert _sha256(path) == digest, "Loading must not modify the dataset file"


def test_multi_year_dataset_loads_from_read_only_file(tmp_path: Path):
    path = tmp_path / "multi_year.h5"
    UKMultiYearDataset(
        datasets=[_synthetic_dataset(YEAR), _synthetic_dataset(YEAR + 1)]
    ).save(str(path))
    _make_read_only(path)
    digest = _sha256(path)

    loaded = UKMultiYearDataset(str(path))

    assert loaded.years == [YEAR, YEAR + 1]
    assert list(loaded[YEAR + 1].person["age"]) == [40.0, 38.0, 70.0]
    assert _sha256(path) == digest, "Loading must not modify the dataset file"


@pytest.mark.microsimulation
def test_microsimulation_loads_read_only_tiny_dataset(tmp_path: Path):
    """Reproduces loading from a Hugging Face cache snapshot.

    Snapshot files are read-only on disk; before the fix,
    ``Microsimulation(dataset=path)`` raised a ``PermissionError`` on open.
    """
    from huggingface_hub import hf_hub_download

    from policyengine_uk import Microsimulation

    source = hf_hub_download(
        repo_id=TINY_DATASET_REPO,
        filename=TINY_DATASET_FILENAME,
        revision=TINY_DATASET_VERSION,
        token=os.environ.get("HUGGING_FACE_TOKEN") or None,
    )
    path = tmp_path / TINY_DATASET_FILENAME
    shutil.copyfile(source, path)
    _make_read_only(path)
    digest = _sha256(path)

    sim = Microsimulation(dataset=str(path))
    net_income = np.asarray(sim.calculate("household_net_income", YEAR).values)

    assert len(net_income) > 0
    assert np.isfinite(net_income).all()
    assert _sha256(path) == digest, "Loading must not modify the dataset file"
