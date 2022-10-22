from policyengine_uk.data import EnhancedFRS, SynthFRS, DATASETS
from pathlib import Path
import inquirer
import yaml
import argparse

REPO = Path(__file__).parent

NEWLINE = "\n"

DATASET_CONFIG_FILE = Path(__file__).parent / "tools" / "datasets.yml"

key_to_ds = {ds.name: ds for ds in DATASETS if ds.is_openfisca_compatible}


def set_default(dataset):
    with open(DATASET_CONFIG_FILE, "w+") as f:
        data = yaml.safe_load(f)
        if data is None:
            data = {}
        data["default"] = dataset.name
        yaml.dump(data, f)


def main():
    parser = argparse.ArgumentParser(
        description="Utility to set up OpenFisca-UK"
    )
    parser.add_argument("--set-default", help="The default dataset to use")
    args = parser.parse_args()

    if args.set_default is not None:
        set_default(key_to_ds[args.set_default])
        print("Just setting default dataset, skipping questions.")
    else:
        USE_FRS_2022 = "Use the enhanced 2022 FRS"
        USE_SYNTHETIC = "Just use the synthetic FRS"
        CUSTOM = "Use a specific dataset"
        setup_question = inquirer.List(
            "setup_mode",
            message="How would you like to set up OpenFisca-UK's default dataset?",
            choices=[USE_FRS_2022, USE_SYNTHETIC, CUSTOM],
        )
        setup_mode = inquirer.prompt([setup_question])["setup_mode"]
        if setup_mode == USE_SYNTHETIC:
            if len(SynthFRS.years) == 0:
                print("Couldn't find the synthetic dataset, downloading.")
                SynthFRS.download(2022)
            else:
                print(
                    f"You currently have the synthetic FRS dataset for: {', '.join(map(str, SynthFRS.years))}."
                )
            set_default(SynthFRS)
        elif setup_mode == USE_FRS_2022:
            if 2022 not in EnhancedFRS.years:
                print("Couldn't find the enhanced 2022 dataset, downloading.")
                EnhancedFRS.download(2022)
            set_default(EnhancedFRS)
        elif setup_mode == CUSTOM:
            dataset_question = inquirer.List(
                "default_dataset",
                message="Which dataset would you like OpenFisca-UK to use by default?",
                choices=list(
                    map(
                        lambda x: x.name,
                        filter(lambda x: x.is_openfisca_compatible, DATASETS),
                    )
                ),
            )
            default_dataset = inquirer.prompt([dataset_question])[
                "default_dataset"
            ]
            dataset = list(
                filter(lambda ds: ds.name == default_dataset, DATASETS)
            )[0]
            set_default(dataset)
            dataset_years = ", ".join(map(str, dataset.years))
            if len(dataset.years) == 0:
                print(
                    f"No dataset years stored for the {dataset.name} dataset."
                )
            else:
                print(
                    f"The {default_dataset} dataset has the following years stored: {dataset_years}."
                )
            other_years = [
                inquirer.List(
                    "dataset_year_check",
                    message="Do you want to import other years?",
                    choices=["yes", "no"],
                ),
            ]
            add_other_year = inquirer.prompt(other_years)["dataset_year_check"]
            if add_other_year == "yes":
                answers = inquirer.prompt(
                    [
                        inquirer.List(
                            "year",
                            message="Which year do you want to import?",
                            choices=list(map(str, range(2016, 2023))),
                        ),
                        inquirer.Path(
                            "file_path",
                            message="Please enter the filepath to the H5 file",
                            path_type=inquirer.Path.FILE,
                            normalize_to_absolute_path=True,
                        ),
                    ]
                )
                year = int(answers["year"])
                filepath = str(Path(answers["file_path"]).expanduser())
                dataset.save(filepath, year)
        print("Setup complete.")


if __name__ == "__main__":
    main()
