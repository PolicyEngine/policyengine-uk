from openfisca_data import UK_DATASETS, FRS
from pathlib import Path
import inquirer
from openfisca_data.datasets.uk.frs.synth_frs import SynthFRS
import yaml

NEWLINE = "\n"

DATASET_CONFIG_FILE = Path(__file__).parent / "tools" / "datasets.yml"


def main():
    USE_SYNTHETIC = "Just use the synthetic FRS"
    USE_FRS_2018 = "Use the 2018 FRS"
    CUSTOM = "Use a specific dataset"
    setup_question = inquirer.List(
        "setup_mode",
        message="How would you like to set up OpenFisca-UK's default dataset?",
        choices=[USE_SYNTHETIC, USE_FRS_2018, CUSTOM],
    )
    setup_mode = inquirer.prompt([setup_question])["setup_mode"]
    if setup_mode == USE_SYNTHETIC:
        if len(SynthFRS.years) == 0:
            print("Couldn't find the synthetic dataset, downloading.")
            SynthFRS.save()
        else:
            print(
                f"You currently have the synthetic FRS dataset for: {', '.join(map(str, SynthFRS.years))}."
            )
    elif setup_mode == USE_FRS_2018:
        file_input = inquirer.Path(
            "file_path",
            message="Please enter the filepath to frs_2018.h5",
            path_type=inquirer.Path.FILE,
            normalize_to_absolute_path=True,
        )
        filepath = str(
            Path(inquirer.prompt([file_input])["file_path"]).expanduser()
        )
        FRS.save(filepath, 2018)
        set_default(FRS)
    elif setup_mode == CUSTOM:
        dataset_question = inquirer.List(
            "default_dataset",
            message="Which dataset would you like OpenFisca-UK to use by default?",
            choices=list(map(lambda x: x.name, UK_DATASETS)),
        )
        default_dataset = inquirer.prompt([dataset_question])[
            "default_dataset"
        ]
        dataset = list(
            filter(lambda ds: ds.name == default_dataset, UK_DATASETS)
        )[0]
        set_default(dataset)
        dataset_years = ", ".join(map(str, dataset.years))
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
                        message="Please enter the filepath to the H5 file:",
                        path_type=inquirer.Path.FILE,
                        normalize_to_absolute_path=True,
                    ),
                ]
            )
            year = int(answers["year"])
            filepath = str(Path(answers["file_path"]).expanduser())
            dataset.save(filepath, year)
    print("Setup complete.")


def set_default(dataset):
    with open(DATASET_CONFIG_FILE, "w+") as f:
        data = yaml.safe_load(f)
        if data is None:
            data = {}
        data["default"] = dataset.name
        yaml.dump(data, f)


if __name__ == "__main__":
    main()
