import os

import pytest

DEFAULT_TEST_DATASET_URL = (
    "hf://policyengine/policyengine-uk-data-private/enhanced_frs_2023_24.h5@1.40.3"
)

if os.environ.get("HUGGING_FACE_TOKEN") and not os.environ.get(
    "POLICYENGINE_UK_DEFAULT_DATASET"
):
    os.environ["POLICYENGINE_UK_DEFAULT_DATASET"] = DEFAULT_TEST_DATASET_URL


def pytest_collection_modifyitems(config, items):
    has_default_dataset = bool(os.environ.get("POLICYENGINE_UK_DEFAULT_DATASET"))
    if has_default_dataset:
        return

    skip_microsimulation = pytest.mark.skip(
        reason=(
            "Requires POLICYENGINE_UK_DEFAULT_DATASET or HUGGING_FACE_TOKEN "
            "for microsimulation dataset access"
        )
    )
    for item in items:
        if "microsimulation" in item.keywords:
            item.add_marker(skip_microsimulation)
