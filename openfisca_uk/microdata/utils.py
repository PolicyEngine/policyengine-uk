import logging
from pathlib import Path
import shutil
from typing import Callable, Tuple, Type
from openfisca_core.model_api import *
from pathlib import Path
import shutil
from typing import List
import pandas as pd
import re
import os
import subprocess
from functools import wraps
import h5py
import requests
from tqdm import tqdm
import numpy as np
import warnings
from google.cloud import storage

VERSION = "0.9.0"

UK = "openfisca_uk"


class classproperty(object):
    def __init__(self, f):
        self.f = f

    def __get__(self, obj, owner):
        return self.f(owner)


def dataset(cls):
    def generate():
        raise NotImplementedError("No dataset generation function specified")

    if not hasattr(cls, "model"):
        cls.model = None
        cls.data_dir = data_folder(DATA_DIR / "external")
    else:
        cls.data_dir = data_folder(DATA_DIR / cls.model)

    def years(cl):
        pattern = re.compile(f"\n{cl.name}_([0-9]+).h5")
        matches = list(
            map(
                int,
                pattern.findall(
                    "\n"
                    + "\n".join(
                        map(lambda path: path.name, cl.data_dir.iterdir())
                    )
                ),
            )
        )
        return matches

    cls.years = classproperty(years)

    def last_year(self):
        return sorted(cls.years)[-1]

    cls.last_year = property(last_year)

    def filename(year):
        return f"{cls.name}_{year}.h5"

    cls.filename = staticmethod(filename)

    def load(year, key: str = None) -> pd.DataFrame:
        try:
            year = int(year)
        except:
            pass
        if year not in cls.years:
            raise Exception(
                f"\n\nNo data available for year {year}. To download, run:\n\n\topenfisca-uk-data {cls.name} download {year}\n\nThis may require signing in with Google authentication if it is not publicly available."
            )
        file = cls.file(year)
        if cls.model:
            if key is None:
                return h5py.File(file, mode="r")
            else:
                with h5py.File(file, mode="r") as f:
                    values = np.array(f[key])
                return values
        else:
            if key is None:
                return pd.HDFStore(file)
            else:
                with pd.HDFStore(file) as f:
                    values = f[key]
                return values

    def remove(year=None):
        if year is None:
            filenames = map(cls.filename(year), cls.years)
        else:
            filenames = (cls.filename(year),)
        for filename in filenames:
            filepath = cls.data_dir / filename
            if filepath.exists():
                os.remove(filepath)

    cls.remove = staticmethod(remove)

    def remove_first_then(generate_func):
        def new_generate_func(year, *args):
            cls.remove(year)
            return generate_func(year, *args)

        return new_generate_func

    if hasattr(cls, "generate"):
        cls.generate = staticmethod(remove_first_then(cls.generate))
    else:
        cls.generate = staticmethod(generate)

    cls.load = staticmethod(load)

    if not hasattr(cls, "input_reform_from_year"):
        cls.input_reform_from_year = lambda year: ()

    cls.file = staticmethod(lambda year: cls.data_dir / cls.filename(year))

    def save(data_file: str, year: int):
        if "https://" in data_file:
            response = requests.get(data_file, stream=True)
            total_size_in_bytes = int(
                response.headers.get("content-length", 0)
            )
            block_size = 1024  # 1 Kibibyte
            progress_bar = tqdm(
                total=total_size_in_bytes, unit="iB", unit_scale=True
            )
            with open(cls.file(year), "wb") as file:
                for data in response.iter_content(block_size):
                    progress_bar.update(len(data))
                    file.write(data)
            progress_bar.close()
        else:
            shutil.copyfile(data_file, cls.file(year))

    if not hasattr(cls, "save"):
        cls.save = staticmethod(save)

    if not hasattr(cls, "upload"):

        def upload(year):
            bucket = get_storage_bucket()
            blob = bucket.blob(
                cls.file(year).name[:-3]
                + "_v"
                + VERSION.replace(".", "_")
                + ".h5"
            )
            with open(cls.file(year), "rb") as f:
                blob.upload_from_file(f)

        cls.upload = staticmethod(upload)

    if not hasattr(cls, "download"):

        def download(year):
            bucket = get_storage_bucket()
            filenames = list(map(lambda blob: blob.name, bucket.list_blobs()))
            selected_file, match_type = select_best_version(
                filenames, cls, year
            )
            if selected_file is None:
                raise Exception(
                    "No acceptable version of the dataset could be found."
                )
            if match_type != "exact":
                logging.warning(
                    f"Sub-optimal match type: {match_type}. Consider updating the openfisca-uk-data package version."
                )
            else:
                logging.info(
                    f"Found dataset with match type: {match_type}, saving..."
                )
            blob = bucket.blob(selected_file)
            with open(cls.file(year), "wb") as f:
                blob.download_to_file(f)
            logging.info("Successfully downloaded and saved dataset.")

        cls.download = staticmethod(download)

    return cls


def get_storage_bucket() -> storage.Bucket:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        try:
            client = storage.Client()
        except:
            logging.info(
                "Could not automatically authenticate with Google Cloud, prompting login..."
            )
            failed_login = subprocess.check_call(
                ["gcloud auth application-default login"],
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            if not failed_login:
                logging.info(
                    "Successfully logged in to Google Cloud, attempting to download..."
                )
                client = storage.Client()
            else:
                raise Exception("Could not authenticate with Google Cloud.")
    try:
        return client.get_bucket("policyengine-uk-data")
    except:
        raise Exception("Your account does not have sufficient permissions.")


def data_folder(path: str, erase=False) -> Path:
    folder = Path(path)
    folder.mkdir(exist_ok=True, parents=True)
    if erase:
        shutil.rmtree(folder)
        folder.mkdir()
    return folder


def safe_rmdir(path: str):
    if Path(path).exists():
        shutil.rmtree(path)


def extract_version_info(filename: str) -> Tuple[int, int, int]:
    filename = filename.split(".")[0]
    if "v" in filename:
        return (*tuple(map(int, filename.split("v")[1].split("_"))), filename)
    else:
        return None


def select_best_version(
    filenames: List[str], dataset: type, year: int
) -> Tuple[str, str]:
    pattern = r"{name}_{year}(|_v[0-9]+_[0-9]+_[0-9]+).h5".format(
        name=dataset.name, year=year
    )
    dataset_filenames = filter(lambda name: re.match(pattern, name), filenames)
    filenames_with_versions = map(extract_version_info, dataset_filenames)
    versions = sorted(filter(None, filenames_with_versions), reverse=True)
    current_major, current_minor, current_patch = map(int, VERSION.split("."))
    for major, minor, patch, filename in versions:
        # Go down the list sorted by version number descending
        if major == current_major:
            if minor == current_minor:
                if patch == current_patch:
                    match_type = "exact"
                else:
                    match_type = "minor"
            else:
                match_type = "major"
            return filename + ".h5", match_type
    general_name = dataset.file(year).name
    if general_name in filenames:
        return general_name, "general"
    return None, None


PACKAGE_DIR = Path(__file__).parent
DATA_DIR = PACKAGE_DIR / "microdata"
