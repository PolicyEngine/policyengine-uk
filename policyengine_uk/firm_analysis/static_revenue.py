"""
Static Revenue Analysis for VAT Threshold Bunching
Uses pre-calculated VAT liability from synthetic data generation (turnover - input)
"""

import pandas as pd
import numpy as np
import os

# Get the current directory (analysis folder)
current_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(current_dir)

# Load the data with pre-calculated VAT liability
print("Loading data...")
synthetic_firms = pd.read_csv(os.path.join(current_dir, 'synthetic_firms_turnover.csv'))

weighted_total_firms = synthetic_firms['weight'].sum()
print(f"Loaded {weighted_total_firms:,.0f} firms with pre-calculated VAT liability")

# Check if VAT liability already exists in the data
if 'vat_liability_k' not in synthetic_firms.columns:
    print("ERROR: vat_liability_k column not found. Please run generate_synthetic_data.py first.")
    exit(1)

# Convert VAT liability from thousands to pounds for analysis
synthetic_firms['vat_liability'] = synthetic_firms['vat_liability_k'] * 1000

print(f"\nVAT Liability Statistics:")
print(f"  Total VAT liability: £{(synthetic_firms['vat_liability'] * synthetic_firms['weight']).sum() / 1_000_000:,.2f} million")
print(f"  Firms with positive VAT: {synthetic_firms[synthetic_firms['vat_liability'] > 0]['weight'].sum():,.0f}")
print(f"  Firms with negative VAT: {synthetic_firms[synthetic_firms['vat_liability'] < 0]['weight'].sum():,.0f}")
print(f"  Firms with zero VAT: {synthetic_firms[synthetic_firms['vat_liability'] == 0]['weight'].sum():,.0f}")

# Static revenue impact analysis
# Convert turnover from thousands to pounds for threshold comparison
synthetic_firms['annual_turnover'] = synthetic_firms['annual_turnover_k'] * 1000

# Identify firms in the bunching region (£85k to £90k)
affected = synthetic_firms[
    (synthetic_firms['annual_turnover'] >= 85000) & 
    (synthetic_firms['annual_turnover'] < 90000)
]

# Calculate total revenue loss (weighted VAT liability)
total_revenue_loss = (affected['vat_liability'] * affected['weight']).sum()
total_revenue_loss_millions = total_revenue_loss / 1_000_000

# Summary statistics (applying weights)
total_weighted_firms = synthetic_firms['weight'].sum()
affected_weighted_firms = affected['weight'].sum()

print("\n" + "="*60)
print("STATIC REVENUE IMPACT ANALYSIS")
print("="*60)
print(f"Total firms in dataset: {total_weighted_firms:,.0f}")
print(f"Firms in bunching region (£85k-£90k): {affected_weighted_firms:,.0f}")
print(f"Percentage of firms affected: {affected_weighted_firms/total_weighted_firms*100:.2f}%")
print(f"\nTotal VAT liability in bunching region: £{total_revenue_loss_millions:,.2f} million")
print(f"Average VAT per affected firm: £{total_revenue_loss/affected_weighted_firms:,.2f}" if affected_weighted_firms > 0 else "N/A")

# Additional analysis by sector
print("\n" + "="*60)
print("TOP 5 SECTORS BY VAT LIABILITY IN BUNCHING REGION")
print("="*60)
if len(affected) > 0:
    # Calculate weighted VAT liability by sector
    sector_impact = affected.groupby('sic_code').apply(
        lambda x: pd.Series({
            'weighted_vat_liability': (x['vat_liability'] * x['weight']).sum(),
            'weighted_firm_count': x['weight'].sum()
        })
    )
    sector_impact = sector_impact.sort_values('weighted_vat_liability', ascending=False).head(5)
    
    for idx, (sector, row) in enumerate(sector_impact.iterrows(), 1):
        vat_millions = row['weighted_vat_liability'] / 1_000_000
        print(f"{idx}. Sector {sector}")
        print(f"   Firms: {row['weighted_firm_count']:,.0f}, VAT: £{vat_millions:.2f} million")

# Check data quality
print("\n" + "="*60)
print("DATA QUALITY CHECKS")
print("="*60)
print(f"Firms with missing SIC codes: {synthetic_firms[synthetic_firms['sic_code'].isna()]['weight'].sum():,.0f}")
print(f"Firms with zero/negative turnover: {synthetic_firms[synthetic_firms['annual_turnover_k'] <= 0]['weight'].sum():,.0f}")
print(f"Raw records with zero/negative weights: {(synthetic_firms['weight'] <= 0).sum()}")
print(f"Firms with non-zero VAT liability: {synthetic_firms[synthetic_firms['vat_liability'] != 0]['weight'].sum():,.0f}")

# Calculate total weighted VAT liability
total_weighted_vat = (synthetic_firms['vat_liability'] * synthetic_firms['weight']).sum()
total_vat_billions = total_weighted_vat / 1_000_000_000
print(f"Total weighted VAT liability across all firms: £{total_vat_billions:,.2f} billion")

# Show input/output statistics
print(f"\nInput/Output Statistics:")
print(f"Average input/output ratio: {(synthetic_firms['annual_input_k'] / synthetic_firms['annual_turnover_k']).mean():.2%}")
print(f"Firms with input > output (negative VAT): {synthetic_firms[synthetic_firms['annual_input_k'] > synthetic_firms['annual_turnover_k']]['weight'].sum():,.0f}")

# Generate multi-year revenue impact table
print("\n" + "="*100)
print("MULTI-YEAR REVENUE IMPACT ANALYSIS")
print("="*100)

# Define the fiscal years and parameters with correct baseline thresholds
# Based on RPI with 2-year lag: 2024-25=2.0%, 2025-26=2.5%, 2026-27=3.0%
fiscal_years = [
    {"year": "2024-25", "rpi": "— (frozen)", "baseline": 85000, "policy": 90000, "hmrc_impact": -150, "firm_growth": 1.031},      # 3.1%
    {"year": "2025-26", "rpi": "— (frozen)", "baseline": 85000, "policy": 90000, "hmrc_impact": -185, "firm_growth": 1.0516},     # 1.031 * 1.020
    {"year": "2026-27", "rpi": "2024-25: +2.0%", "baseline": 87000, "policy": 90000, "hmrc_impact": -125, "firm_growth": 1.0779},    # £85,000 * 1.020 = £87,000
    {"year": "2027-28", "rpi": "2025-26: +2.5%", "baseline": 89000, "policy": 90000, "hmrc_impact": -50, "firm_growth": 1.1102},     # £87,000 * 1.025 = £89,175 ≈ £89,000
    {"year": "2028-29", "rpi": "2026-27: +3.0%", "baseline": 92000, "policy": 90000, "hmrc_impact": 65, "firm_growth": 1.1424},      # £89,000 * 1.030 = £91,670 ≈ £92,000
]

# Calculate PolicyEngine estimates for each year
results = []
for fy in fiscal_years:
    # Apply growth factor to firm data for this year
    # Create a copy with adjusted turnover and VAT liability
    adjusted_firms = synthetic_firms.copy()
    adjusted_firms['annual_turnover'] = adjusted_firms['annual_turnover_k'] * 1000 * fy['firm_growth']
    adjusted_firms['vat_liability'] = adjusted_firms['vat_liability_k'] * 1000 * fy['firm_growth']
    
    # Determine the affected range based on baseline vs policy
    if fy['baseline'] > fy['policy']:
        # When baseline > policy (2028-29), firms between policy and baseline
        # are now required to register (they're above £90k policy but would have been below baseline)
        baseline_affected = adjusted_firms[
            (adjusted_firms['annual_turnover'] >= fy['policy']) & 
            (adjusted_firms['annual_turnover'] < fy['baseline'])
        ]
        # This is a revenue gain - these firms now must pay VAT
        pe_impact = (baseline_affected['vat_liability'] * baseline_affected['weight']).sum() / 1_000_000
    else:
        # When baseline < policy, firms between baseline and policy can avoid VAT
        baseline_affected = adjusted_firms[
            (adjusted_firms['annual_turnover'] >= fy['baseline']) & 
            (adjusted_firms['annual_turnover'] < fy['policy'])
        ]
        # This is a revenue loss - these firms avoid VAT
        pe_impact = -(baseline_affected['vat_liability'] * baseline_affected['weight']).sum() / 1_000_000
    
    results.append({
        "Fiscal Year": fy['year'],
        "Lagged RPI used": fy['rpi'],
        "Baseline": f"£{fy['baseline']:,}",
        "Policy": f"£{fy['policy']:,}",
        "HMRC Revenue Impact (£m)": fy['hmrc_impact'],
        "PolicyEngine Impact (£m)": round(pe_impact, 0),
        "Difference": round(pe_impact - fy['hmrc_impact'], 0)
    })

# Create DataFrame for nice display
import pandas as pd
results_df = pd.DataFrame(results)

# Display the table
print("\n" + "-"*100)
print(f"{'Fiscal Year':<12} {'Lagged RPI':<20} {'Baseline':<12} {'Policy':<12} {'HMRC (£m)':<12} {'PE (£m)':<12} {'Diff (£m)':<10}")
print("-"*100)

for _, row in results_df.iterrows():
    print(f"{row['Fiscal Year']:<12} {row['Lagged RPI used']:<20} {row['Baseline']:<12} {row['Policy']:<12} "
          f"{row['HMRC Revenue Impact (£m)']:>10} {row['PolicyEngine Impact (£m)']:>10} "
          f"{row['Difference']:>10}")

print("-"*100)
print(f"\nNote: Negative values indicate revenue loss, positive values indicate revenue gain")
print(f"PE = PolicyEngine estimate based on firm-level VAT liability calculations")

# Create and save a plot
import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(12, 6))

# Extract data for plotting
years = [fy['year'] for fy in fiscal_years]
hmrc_impacts = [fy['hmrc_impact'] for fy in fiscal_years]
pe_impacts = [row['PolicyEngine Impact (£m)'] for row in results]

# Plot the data
x = range(len(years))
width = 0.35

bars1 = ax.bar([i - width/2 for i in x], hmrc_impacts, width, label='HMRC', color='#2E86AB')
bars2 = ax.bar([i + width/2 for i in x], pe_impacts, width, label='PolicyEngine', color='#A23B72')

# Add value labels on bars with padding
for bar in bars1:
    height = bar.get_height()
    # Add padding: 5 units above positive bars, 5 units below negative bars
    y_pos = height + 5 if height > 0 else height - 5
    ax.text(bar.get_x() + bar.get_width()/2., y_pos,
            f'£{int(height)}m', ha='center', va='bottom' if height > 0 else 'top')

for bar in bars2:
    height = bar.get_height()
    # Add padding: 5 units above positive bars, 5 units below negative bars
    y_pos = height + 5 if height > 0 else height - 5
    ax.text(bar.get_x() + bar.get_width()/2., y_pos,
            f'£{int(height)}m', ha='center', va='bottom' if height > 0 else 'top')

# Customize the plot
# ax.set_xlabel('Fiscal Year', fontsize=12)
ax.set_ylabel('£ millions', fontsize=12)
ax.set_title('Revenue Impact of Increasing the VAT Registration Threshold (2024-29)', fontsize=14, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(years)
ax.legend()
ax.grid(True, alpha=0.3, linestyle='--')
ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)

# Set y-axis from -250 to 100
ax.set_ylim(-250, 100)

# Add baseline/policy annotations
for i, fy in enumerate(fiscal_years):
    baseline_text = f"Baseline: £{fy['baseline']/1000:.0f}k"
    policy_text = f"Policy: £{fy['policy']/1000:.0f}k"
    ax.text(i, ax.get_ylim()[0] * 0.9, f"{baseline_text}\n{policy_text}", 
            ha='center', va='top', fontsize=10, color='gray')

plt.tight_layout()

# Save the plot
plot_path = os.path.join(current_dir, 'vat_threshold_revenue_impact.png')
plt.savefig(plot_path, dpi=150, bbox_inches='tight')
print(f"\nPlot saved to: {plot_path}")

# Display the plot
# plt.show()
