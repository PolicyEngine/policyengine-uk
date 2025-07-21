import pandas as pd
from pathlib import Path
from policyengine_uk.data.dataset_schema import UKDataset

START_YEAR = 2022
END_YEAR = 2029


def create_policyengine_uprating_factors_table(print_diff=True):
    from policyengine_uk.system import system

    df = pd.DataFrame()

    variable_names = []
    years = []
    yoy_values = []

    parameter_by_variable = {}

    for variable in system.variables.values():
        if variable.uprating is not None:
            parameter = system.parameters.get_child(
                variable.uprating.replace("indices", "yoy_growth")
            )
            parameter_by_variable[variable.name] = parameter.name
            for year in range(START_YEAR, END_YEAR + 1):
                variable_names.append(variable.name)
                years.append(str(year))
                yoy_values.append(round(parameter(year), 3))

    df["Variable"] = variable_names
    df["Year"] = years
    df["Value"] = yoy_values

    # Convert to there is a column for each year
    df = df.pivot(index="Variable", columns="Year", values="Value")
    df = df.sort_values("Variable")

    file_path = Path(__file__).parent / "uprating_growth_factors.csv"

    # Read old CSV if it exists
    old_df = None
    if file_path.exists():
        old_df = pd.read_csv(file_path, index_col=0)
        # Ensure all columns are strings in old_df
        old_df.columns = old_df.columns.astype(str)

    # Prepare new dataframe
    df["Parameter"] = df.index.map(parameter_by_variable)
    df = df[
        ["Parameter"] + [str(year) for year in range(START_YEAR, END_YEAR + 1)]
    ]

    # Print diff if old CSV existed and print_diff is True
    if old_df is not None and print_diff:
        print_csv_diff(old_df, df)
        # Save new CSV
        df.to_csv(file_path)

    return pd.read_csv(file_path)


def print_csv_diff(old_df, new_df):
    """Print differences between old and new dataframes."""
    print("\n" + "=" * 80)
    print("CSV diff report")
    print("=" * 80)

    # Check for new rows
    new_rows = set(new_df.index) - set(old_df.index)
    if new_rows:
        print(f"\n✅ New rows added ({len(new_rows)}):")
        for row in sorted(new_rows):
            print(f"  - {row}")

    # Check for deleted rows
    deleted_rows = set(old_df.index) - set(new_df.index)
    if deleted_rows:
        print(f"\n❌ Rows deleted ({len(deleted_rows)}):")
        for row in sorted(deleted_rows):
            print(f"  - {row}")

    # Check for changed values
    common_rows = set(old_df.index) & set(new_df.index)
    common_cols = set(old_df.columns) & set(new_df.columns)

    changes = []
    for row in common_rows:
        for col in common_cols:
            old_val = old_df.loc[row, col]
            new_val = new_df.loc[row, col]

            # Handle NaN values
            if pd.isna(old_val) and pd.isna(new_val):
                continue
            elif pd.isna(old_val) or pd.isna(new_val):
                changes.append((row, col, old_val, new_val))
            elif old_val != new_val:
                changes.append((row, col, old_val, new_val))

    if changes:
        print(f"\n🔄 Value changes ({len(changes)}):")
        print(
            f"{'Variable':<30} {'Column':<15} {'Old value':<15} {'New value':<15}"
        )
        print("-" * 75)
        for row, col, old_val, new_val in sorted(changes):
            old_str = str(old_val) if not pd.isna(old_val) else "NaN"
            new_str = str(new_val) if not pd.isna(new_val) else "NaN"
            print(f"{row:<30} {str(col):<15} {old_str:<15} {new_str:<15}")

    # Check for new columns
    new_cols = set(new_df.columns) - set(old_df.columns)
    if new_cols:
        print(f"\n✅ New columns added ({len(new_cols)}):")
        for col in sorted(new_cols):
            print(f"  - {col}")

    # Check for deleted columns
    deleted_cols = set(old_df.columns) - set(new_df.columns)
    if deleted_cols:
        print(f"\n❌ Columns deleted ({len(deleted_cols)}):")
        for col in sorted(deleted_cols):
            print(f"  - {col}")

    if not (new_rows or deleted_rows or changes or new_cols or deleted_cols):
        print("\n✨ No changes detected - CSV is identical!")

    print("\n" + "=" * 80 + "\n")


def convert_yoy_growth_to_index(
    growth_factors: pd.DataFrame,
):
    """
    Convert year-on-year growth factors to an index.
    """
    growth_factors = growth_factors.copy()
    # Get the first year column (skip 'Variable' and 'Parameter' columns)
    year_columns = [
        col
        for col in growth_factors.columns
        if col not in ["Variable", "Parameter"]
    ]
    index = growth_factors[year_columns[0]] * 0 + 1
    for year in year_columns:
        index *= 1 + growth_factors[year]
        growth_factors[year] = index
    return growth_factors


def apply_growth_factors(
    dataset: UKDataset,
    growth_factors: pd.DataFrame,
    start_year: int,
    end_year: int,
):
    start_year = str(start_year)
    end_year = str(end_year)
    dataset = dataset.copy()
    growth_factors_indices = convert_yoy_growth_to_index(growth_factors)
    for i in range(len(growth_factors)):
        variable = growth_factors["Variable"].values[i]
        start_index = growth_factors_indices[start_year].values[i]
        end_index = growth_factors_indices[end_year].values[i]

        for table in dataset.tables:
            if variable in table.columns:
                table[variable] *= end_index / start_index

    return dataset


BASELINE_GROWFACTORS = create_policyengine_uprating_factors_table(
    print_diff=False
)


if __name__ == "__main__":
    # Print diff when running as script
    create_policyengine_uprating_factors_table(print_diff=True)
