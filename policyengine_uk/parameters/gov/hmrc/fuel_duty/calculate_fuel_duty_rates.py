"""
Calculates calendar year average fuel duty rates and updates petrol_and_diesel.yaml.

Reads base rates from petrol_and_diesel.yaml and RPI forecasts from yoy_growth.yaml,
then computes weighted averages accounting for the staggered 5p cut reversal and
RPI uprating from April 2027.

Usage:
    python calculate_fuel_duty_rates.py          # Print calculations only
    python calculate_fuel_duty_rates.py --update # Update the YAML file
"""

import argparse
import re
from datetime import date
from calendar import isleap
from pathlib import Path

import yaml


# Years to calculate rates for
CALCULATION_YEARS = range(2026, 2031)


def get_repo_root() -> Path:
    """Find the repository root by looking for policyengine_uk directory."""
    current = Path(__file__).resolve()
    while current != current.parent:
        if (current / "policyengine_uk").is_dir():
            return current
        current = current.parent
    raise RuntimeError("Could not find repository root")


def get_fuel_duty_yaml_path() -> Path:
    """Get the path to the fuel duty YAML file."""
    repo_root = get_repo_root()
    return (
        repo_root
        / "policyengine_uk/parameters/gov/hmrc/fuel_duty/petrol_and_diesel.yaml"
    )


def load_fuel_duty_rates() -> dict:
    """Load fuel duty rates from the YAML parameter file."""
    yaml_path = get_fuel_duty_yaml_path()
    with open(yaml_path) as f:
        return yaml.safe_load(f)


def load_rpi_forecasts() -> dict:
    """Load RPI year-on-year growth forecasts from economic assumptions."""
    repo_root = get_repo_root()
    yaml_path = (
        repo_root
        / "policyengine_uk/parameters/gov/economic_assumptions/yoy_growth.yaml"
    )
    with open(yaml_path) as f:
        data = yaml.safe_load(f)

    # Extract RPI values and convert to percentage format
    rpi_values = data["obr"]["rpi"]["values"]
    rpi_forecasts = {}
    for date_key, value in rpi_values.items():
        # Handle both string and datetime.date keys from YAML
        if hasattr(date_key, "year"):
            year = date_key.year
        else:
            year = int(str(date_key).split("-")[0])
        # Convert from decimal (0.0371) to percentage (3.71)
        rpi_forecasts[year] = value * 100
    return rpi_forecasts


def get_value_for_date(values: dict, target_date: str) -> float:
    """
    Get the value for a specific date from a YAML values dict.
    Handles both string and datetime.date keys.
    """
    for date_key, value in values.items():
        # Normalize date key to string for comparison
        if hasattr(date_key, "strftime"):
            key_str = date_key.strftime("%Y-%m-%d")
        else:
            key_str = str(date_key)

        if key_str == target_date:
            # Value might be a dict with 'value' key or a direct number
            if isinstance(value, dict):
                return value["value"]
            return value
    return None


def get_base_rate_with_cut(fuel_duty_data: dict) -> float:
    """
    Get the base fuel duty rate with the 5p cut still in place.
    This is the rate at 2022-03-23 (when the 5p cut was introduced).
    Returns rate in pence.
    """
    values = fuel_duty_data["values"]
    # The 5p cut rate is at 2022-03-23
    rate = get_value_for_date(values, "2022-03-23")
    if rate is None:
        raise ValueError("Could not find 2022-03-23 fuel duty rate")
    # Convert from GBP to pence
    return rate * 100


def get_pre_cut_rate(fuel_duty_data: dict) -> float:
    """
    Get the fuel duty rate before the 5p cut (the rate to restore to).
    This is the rate at 2021-01-01 (57.95p).
    Returns rate in pence.
    """
    values = fuel_duty_data["values"]
    rate = get_value_for_date(values, "2021-01-01")
    if rate is None:
        raise ValueError("Could not find 2021-01-01 fuel duty rate")
    return rate * 100


# Staggered reversal schedule (date, cumulative increase in pence)
REVERSAL_SCHEDULE = [
    (date(2026, 9, 1), 1.0),  # +1p
    (date(2026, 12, 1), 3.0),  # +2p more (total +3p)
    (date(2027, 3, 1), 5.0),  # +2p more (total +5p, full reversal)
]


def get_rate_on_date(
    d: date,
    base_rate_with_cut: float,
    pre_cut_rate: float,
    rpi_forecasts: dict,
) -> float:
    """Get the fuel duty rate (in pence) on a specific date."""
    # Start with the base rate (with 5p cut still in place)
    rate = base_rate_with_cut

    # Apply staggered reversal
    for reversal_date, increase in REVERSAL_SCHEDULE:
        if d >= reversal_date:
            rate = base_rate_with_cut + increase

    # Apply RPI uprating from April 2027
    if d >= date(2027, 4, 1):
        # Rate after full reversal (pre-cut rate)
        rate = pre_cut_rate

        # Apply cumulative RPI uprating
        for year in sorted(rpi_forecasts.keys()):
            if year < 2026:
                continue  # Only apply forecasts from 2026 onwards
            uprating_date = date(year + 1, 4, 1)
            if d >= uprating_date:
                rpi = rpi_forecasts[year]
                rate = rate * (1 + rpi / 100)

    return round(rate, 2)


def days_in_year(year: int) -> int:
    """Return number of days in a year."""
    return 366 if isleap(year) else 365


def calculate_annual_average(
    year: int,
    base_rate_with_cut: float,
    pre_cut_rate: float,
    rpi_forecasts: dict,
) -> float:
    """Calculate the weighted average fuel duty rate for a calendar year."""
    total_days = days_in_year(year)

    # Calculate daily rates and sum them
    total_rate = 0.0
    for month in range(1, 13):
        for day in range(1, 32):
            try:
                d = date(year, month, day)
                total_rate += get_rate_on_date(
                    d, base_rate_with_cut, pre_cut_rate, rpi_forecasts
                )
            except ValueError:
                # Invalid date (e.g., Feb 30)
                continue

    average = total_rate / total_days
    return round(average, 2)


def format_as_pounds(pence: float) -> str:
    """Convert pence to pounds string format for YAML."""
    return f"{pence / 100:.4f}"


def generate_year_breakdown(
    year: int,
    base_rate_with_cut: float,
    pre_cut_rate: float,
    rpi_forecasts: dict,
) -> list:
    """Generate period breakdown for a year, returns list of (start, end, rate, days)."""
    current_rate = None
    period_start = None
    periods = []

    for month in range(1, 13):
        for day in range(1, 32):
            try:
                d = date(year, month, day)
                rate = get_rate_on_date(
                    d, base_rate_with_cut, pre_cut_rate, rpi_forecasts
                )

                if rate != current_rate:
                    if current_rate is not None:
                        days = (prev_date - period_start).days + 1
                        periods.append(
                            (period_start, prev_date, current_rate, days)
                        )
                    current_rate = rate
                    period_start = d
                prev_date = d
            except ValueError:
                continue

    # Add final period
    if current_rate is not None:
        days = (prev_date - period_start).days + 1
        periods.append((period_start, prev_date, current_rate, days))

    return periods


def generate_note_for_year(
    year: int,
    avg_pence: float,
    base_rate_with_cut: float,
    pre_cut_rate: float,
    rpi_forecasts: dict,
) -> str:
    """Generate the note text for a year's YAML entry."""
    periods = generate_year_breakdown(
        year, base_rate_with_cut, pre_cut_rate, rpi_forecasts
    )
    total_days = days_in_year(year)
    year_type = "leap year" if isleap(year) else ""

    lines = []
    if year_type:
        lines.append(f"Calendar year {year} average ({year_type}):")
    else:
        lines.append(f"Calendar year {year} average:")

    for start, end, rate, days in periods:
        lines.append(
            f"- {start.strftime('%b %d')} - {end.strftime('%b %d')} "
            f"({days} days): {rate:.2f}p"
        )

    # Add formula
    formula_parts = [f"{rate:.2f}p * {days}" for _, _, rate, days in periods]
    lines.append(
        f"({' + '.join(formula_parts)}) / {total_days} = {avg_pence:.2f}p"
    )
    lines.append("Generated by calculate_fuel_duty_rates.py")

    return "\n".join(lines)


def update_yaml_file(
    calculated_rates: dict,
    rpi_forecasts: dict,
    base_rate_with_cut: float,
    pre_cut_rate: float,
) -> None:
    """Update the petrol_and_diesel.yaml file with calculated rates."""
    yaml_path = get_fuel_duty_yaml_path()

    # Read the current file content
    with open(yaml_path, "r") as f:
        content = f.read()

    # For each year, update or add the entry
    for year, avg_pence in calculated_rates.items():
        date_str = f"{year}-01-01"
        value_pounds = avg_pence / 100

        # Generate the note
        note = generate_note_for_year(
            year, avg_pence, base_rate_with_cut, pre_cut_rate, rpi_forecasts
        )
        # Indent note lines for YAML
        note_yaml = note.replace("\n", "\n        ")

        # Pattern to match existing entry for this year
        # Matches from the date line until the next date or metadata section
        pattern = (
            rf"(  {date_str}:.*?)(?=\n  \d{{4}}-\d{{2}}-\d{{2}}:|\nmetadata:)"
        )

        # New entry text
        new_entry = f"""  {date_str}:
    value: {value_pounds:.4f}
    metadata:
      reference:
        - title: OBR Economic and Fiscal Outlook November 2025
          href: https://obr.uk/efo/economic-and-fiscal-outlook-november-2025/
      note: |
        {note_yaml}"""

        # Try to replace existing entry
        if re.search(pattern, content, re.DOTALL):
            content = re.sub(pattern, new_entry, content, flags=re.DOTALL)
        else:
            # Entry doesn't exist, need to add it before metadata section
            # Find the metadata section and insert before it
            metadata_match = re.search(r"\nmetadata:", content)
            if metadata_match:
                insert_pos = metadata_match.start()
                content = (
                    content[:insert_pos]
                    + "\n"
                    + new_entry
                    + content[insert_pos:]
                )

    # Write the updated content back
    with open(yaml_path, "w") as f:
        f.write(content)

    print(f"Updated {yaml_path}")


def print_calculations(
    base_rate_with_cut: float,
    pre_cut_rate: float,
    rpi_forecasts: dict,
    calculated_rates: dict,
) -> None:
    """Print calculation details to stdout."""
    print("Loading data from repository files...")
    print(f"  Base rate with 5p cut (2022-03-23): {base_rate_with_cut:.2f}p")
    print(f"  Pre-cut rate (2021-01-01): {pre_cut_rate:.2f}p")
    print()

    print(
        "RPI forecasts from yoy_growth.yaml (applied in April of next year):"
    )
    for year in CALCULATION_YEARS:
        rpi = rpi_forecasts.get(year, 0)
        print(f"  {year}: {rpi:.2f}%")
    print()

    print("=" * 60)
    print("Fuel Duty Rate Calculations")
    print("=" * 60)
    print()

    # Show the rate schedule
    print("Rate Schedule (actual policy dates):")
    print("-" * 40)
    key_dates = [
        date(2026, 1, 1),
        date(2026, 9, 1),
        date(2026, 12, 1),
        date(2027, 3, 1),
        date(2027, 4, 1),
        date(2028, 4, 1),
        date(2029, 4, 1),
        date(2030, 4, 1),
    ]
    for d in key_dates:
        rate = get_rate_on_date(
            d, base_rate_with_cut, pre_cut_rate, rpi_forecasts
        )
        print(f"  {d}: {rate:.2f}p ({format_as_pounds(rate)} GBP)")

    print()
    print("Calendar Year Averages (for YAML parameter file):")
    print("-" * 40)

    for year in CALCULATION_YEARS:
        avg = calculated_rates[year]
        print(f"  {year}-01-01:")
        print(f"    value: {format_as_pounds(avg)}")
        print(f"    # Average rate: {avg:.2f}p")
        print()

    # Show detailed breakdown for each year
    print()
    print("Detailed Breakdown:")
    print("=" * 60)

    for year in CALCULATION_YEARS:
        year_type = "leap year" if isleap(year) else "regular year"
        print(f"\n{year} ({year_type}):")
        print("-" * 40)

        periods = generate_year_breakdown(
            year, base_rate_with_cut, pre_cut_rate, rpi_forecasts
        )
        total_days = days_in_year(year)
        weighted_sum = 0.0

        for start, end, rate, days in periods:
            weighted_sum += rate * days
            print(
                f"  {start.strftime('%b %d')} - {end.strftime('%b %d')}: "
                f"{days:3d} days @ {rate:.2f}p"
            )

        avg = weighted_sum / total_days
        print(f"  Average: {avg:.2f}p ({format_as_pounds(avg)} GBP)")


def main():
    parser = argparse.ArgumentParser(
        description="Calculate fuel duty rates based on Autumn Budget 2025 policy."
    )
    parser.add_argument(
        "--update",
        action="store_true",
        help="Update the petrol_and_diesel.yaml file with calculated rates",
    )
    args = parser.parse_args()

    # Load data from repository files
    fuel_duty_data = load_fuel_duty_rates()
    rpi_forecasts = load_rpi_forecasts()

    base_rate_with_cut = get_base_rate_with_cut(fuel_duty_data)
    pre_cut_rate = get_pre_cut_rate(fuel_duty_data)

    # Calculate rates for each year
    calculated_rates = {}
    for year in CALCULATION_YEARS:
        avg = calculate_annual_average(
            year, base_rate_with_cut, pre_cut_rate, rpi_forecasts
        )
        calculated_rates[year] = avg

    # Print calculations
    print_calculations(
        base_rate_with_cut, pre_cut_rate, rpi_forecasts, calculated_rates
    )

    # Update YAML file if requested
    if args.update:
        print()
        print("=" * 60)
        print("Updating YAML file...")
        print("=" * 60)
        update_yaml_file(
            calculated_rates, rpi_forecasts, base_rate_with_cut, pre_cut_rate
        )


if __name__ == "__main__":
    main()
