"""
Script to update the expected impacts in reforms_config.yaml with current model values.
This should be run when you want to update the baseline expectations after model changes.
"""

import yaml
from pathlib import Path
from policyengine_uk import Microsimulation
import argparse
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
)
from rich.panel import Panel
from rich import print as rprint
import traceback

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
    console = Console()

    # Load current configuration
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    if verbose:
        console.print(
            Panel.fit(
                f"[bold cyan]Loaded configuration from {config_path}[/bold cyan]\n"
                f"[green]Found {len(config['reforms'])} reforms to update[/green]",
                title="Configuration loaded",
            )
        )

    # Track changes
    changes = []

    # Update each reform's expected impact with progress bar
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task(
            "[cyan]Processing reforms...", total=len(config["reforms"])
        )

        for reform in config["reforms"]:
            progress.update(
                task, description=f"[cyan]Processing: {reform['name'][:40]}..."
            )
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
            progress.advance(task)

    # Show detailed output if verbose
    if verbose and changes:
        console.print("\n[bold]Detailed changes:[/bold]")
        for change in changes:
            color = "red" if change["diff"] < 0 else "green"
            console.print(
                f"  [yellow]{change['name']}[/yellow]\n"
                f"    Old impact: [dim]{change['old']:.1f} billion[/dim]\n"
                f"    New impact: [bold]{change['new']:.1f} billion[/bold]\n"
                f"    Change: [{color}]{change['diff']:+.1f} billion[/{color}]\n"
            )

    # Show summary of changes
    if changes:
        table = Table(
            title="Summary of changes",
            show_header=True,
            header_style="bold magenta",
        )
        table.add_column("Reform", style="cyan", no_wrap=False)
        table.add_column("Old impact (£bn)", justify="right")
        table.add_column("New impact (£bn)", justify="right")
        table.add_column("Change (£bn)", justify="right")

        for change in changes:
            color = "red" if change["diff"] < 0 else "green"
            table.add_row(
                change["name"],
                f"{change['old']:.1f}",
                f"{change['new']:.1f}",
                f"[{color}]{change['diff']:+.1f}[/{color}]",
            )

        console.print("\n", table)
        console.print(
            f"\n[bold cyan]Total changes: {len(changes)}[/bold cyan]"
        )
    else:
        console.print("\n[green]✓ No significant changes detected.[/green]")

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

        console.print(
            Panel.fit(
                f"[green]✓ Configuration updated successfully![/green]\n"
                f"[dim]Backup saved to: {backup_path}[/dim]",
                title="Success",
                border_style="green",
            )
        )
    else:
        console.print(
            "\n[yellow]⚠ Dry run - no changes written to file.[/yellow]"
        )


def main():
    console = Console()
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
        console.print(
            f"[bold red]Error:[/bold red] Configuration file '{args.config}' not found!"
        )
        return 1

    try:
        update_impacts(args.config, dry_run=args.dry_run, verbose=args.verbose)
        return 0
    except Exception as e:
        console.print(f"[bold red]Error updating impacts:[/bold red] {e}")
        console.print(traceback.format_exc())
        return 1


if __name__ == "__main__":
    exit(main())
