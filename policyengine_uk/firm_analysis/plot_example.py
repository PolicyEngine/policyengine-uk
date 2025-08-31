#!/usr/bin/env python3
"""
Simple turnover distribution plot from synthetic firm data.
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

def create_turnover_plot():
    """Create a simple turnover distribution chart."""
    
    # Load data
    data_path = Path(__file__).parent / 'synthetic_firms_turnover.csv'
    df = pd.read_csv(data_path)
    
    # Create bins from 1k to 300k
    bin_edges = np.arange(0.5, 300.5, 1.0)  # 1k intervals
    
    # Calculate weighted histogram
    hist, _ = np.histogram(df['annual_turnover_k'], bins=bin_edges, weights=df['weight'])
    
    # Create plot
    plt.figure(figsize=(15, 6))
    x_positions = np.arange(len(hist))
    
    plt.bar(x_positions, hist, color='lightblue', alpha=0.7, edgecolor='black', linewidth=0.1)
    
    plt.xlabel('Annual Turnover (£k)')
    plt.ylabel('Number of Firms (2023-24)')
    
    # Set x-axis labels every 10k
    label_positions = [i for i in range(9, len(hist), 10)]  # Start at 10k (index 9)
    label_texts = [f'{i+1}' for i in label_positions]
    plt.xticks(label_positions, label_texts)
    
    # Add vertical lines at 85k and 150k
    plt.axvline(x=84, color='red', linestyle='--', alpha=0.7, linewidth=2)  # 85k threshold
    plt.axvline(x=149, color='red', linestyle='--', alpha=0.7, linewidth=2)  # 150k threshold
    
    # Add labels for the vertical lines
    plt.text(85, max(hist) * 0.8, 'VAT Threshold', rotation=0, color='red', fontsize=8, ha='left')
    plt.text(150, max(hist) * 0.8, 'VAT Flat Rate Scheme', rotation=0, color='red', fontsize=8, ha='left')
    
    plt.grid(axis='y', alpha=0.3, linestyle='--')
    
    # Save chart
    output_path = Path(__file__).parent / 'turnover_distribution.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    
    print(f"Chart saved: {output_path}")

if __name__ == "__main__":
    create_turnover_plot()