"""
Script to update the expected impacts in reforms_config.yaml with current model values.
This should be run when you want to update the baseline expectations after model changes.
"""

import yaml
from pathlib import Path
from policyengine_uk import Microsimulation
import argparse
from datetime import datetime

baseline = Microsimulation()


def get_fiscal_impact(reform: dict) -> float:
    """
    Calculate the fiscal impact of a reform in billions.

    Args:
        reform: Dictionary of reform parameters

    Returns:
        Fiscal impact in billions (positive = revenue increase)
    """

    baseline_revenue = baseline.calculate("gov_balance", 2029).sum()
    reform_simulation = Microsimulation(reform=reform)
    reform_revenue = reform_simulation.calculate("gov_balance", 2029).sum()
    return float((reform_revenue - baseline_revenue) / 1e9)


def update_impacts(
    config_path: Path, dry_run: bool = False, verbose: bool = True
):
    """
    Update the expected impacts in the configuration file with current model values.

    Args:
        config_path: Path to the reforms_config.yaml file
        dry_run: If True, show changes without writing to file
        verbose: If True, show detailed output
    """
    # Load current configuration
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    if verbose:
        print(f"Loaded configuration from {config_path}")
        print(f"Found {len(config['reforms'])} reforms to update\n")

    # Track changes
    changes = []

    # Update each reform's expected impact
    for reform in config["reforms"]:
        print(f"Processing reform: {reform['name']}") if verbose else None
        old_impact = reform["expected_impact"]
        new_impact = round(get_fiscal_impact(reform["parameters"]), 1)

        if (
            abs(old_impact - new_impact) > 0.01
        ):  # Only record meaningful changes
            changes.append(
                {
                    "name": reform["name"],
                    "old": old_impact,
                    "new": new_impact,
                    "diff": new_impact - old_impact,
                }
            )

        reform["expected_impact"] = new_impact

        if verbose:
            print(f"Reform: {reform['name']}")
            print(f"  Old impact: {old_impact:.1f} billion")
            print(f"  New impact: {new_impact:.1f} billion")
            if abs(old_impact - new_impact) > 0.01:
                print(f"  Change: {new_impact - old_impact:+.1f} billion")
            print()

    # Show summary of changes
    if changes:
        print("\nSummary of changes:")
        print("-" * 70)
        for change in changes:
            print(
                f"{change['name']:<50} {change['old']:>6.1f} → {change['new']:>6.1f} ({change['diff']:+.1f})"
            )
        print("-" * 70)
        print(f"Total changes: {len(changes)}")
    else:
        print("\nNo significant changes detected.")

    # Write updated configuration
    if not dry_run:
        # Create backup
        backup_path = config_path.with_suffix(
            f".yaml.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        with open(backup_path, "w") as f:
            with open(config_path, "r") as original:
                f.write(original.read())

        # Remove backup
        backup_path.unlink(missing_ok=True)

        # Write updated config
        with open(config_path, "w") as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)

        print(f"\nConfiguration updated successfully!")
        print(f"Backup saved to: {backup_path}")
    else:
        print("\nDry run - no changes written to file.")


def main():
    parser = argparse.ArgumentParser(
        description="Update reform impact expectations with current model values"
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path(
            "policyengine_uk/tests/microsimulation/reforms_config.yaml"
        ),
        help="Path to the reforms configuration file (default: reforms_config.yaml)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without actually updating the file",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        default=True,
        help="Show detailed output for each reform",
    )

    args = parser.parse_args()

    if not args.config.exists():
        print(f"Error: Configuration file '{args.config}' not found!")
        return 1

    try:
        update_impacts(args.config, dry_run=args.dry_run, verbose=args.verbose)
        return 0
    except Exception as e:
        print(f"Error updating impacts: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
