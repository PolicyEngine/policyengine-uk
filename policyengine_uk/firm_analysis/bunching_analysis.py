#!/usr/bin/env python3
"""
Steps 1-5: Complete Bunching Analysis Pipeline with Asymmetric Windows
Step 1: Build counterfactual & bunching statistics  
Step 2: Set effective wedge
Step 3: Calibrate substitution elasticity
Step 4: Advanced probabilistic mapping (micro-level no-notch counterfactual)
Step 5: Forward map to NEW policy (£100k threshold)

ASYMMETRIC WINDOWS CONFIGURATION:
To set different windows for left/right sides of thresholds, modify the main() function:

    counterfactual_window_left = 15    # £15k below £90k threshold (£75k-£90k)  
    counterfactual_window_right = 5    # £5k above £90k threshold (£90k-£95k)
    
    new_policy_window_left = 8         # £8k below £100k new threshold (£92k-£100k)
    new_policy_window_right = 12       # £12k above £100k new threshold (£100k-£112k)

This allows independent control over bunching window sizes on each side of both thresholds.
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression
from scipy.interpolate import interp1d
import warnings
warnings.filterwarnings('ignore')

class CounterfactualBunchingAnalysis:
    """
    Implements Steps 1-5: Complete Bunching Analysis Pipeline
    
    Step 1: Build counterfactual & bunching statistics
    Step 2: Set effective wedge τₑ  
    Step 3: Calibrate substitution elasticity σ
    Step 4: Advanced probabilistic mapping (create_advanced_probabilistic_mapping)
    Step 5: Forward map to NEW policy (£100k threshold)
    """
    
    def __init__(self, threshold=90, window_left=10, window_right=10, 
                 new_policy_window_left=10, new_policy_window_right=10):
        """
        Initialize analysis with threshold T* and asymmetric windows.
        
        Args:
            threshold: VAT threshold T* in £1k (default 90k)
            window_left: Left window (below threshold) for counterfactual analysis in £1k (default 10k)
            window_right: Right window (above threshold) for counterfactual analysis in £1k (default 10k)  
            new_policy_window_left: Left window for new policy analysis in £1k (default 10k)
            new_policy_window_right: Right window for new policy analysis in £1k (default 10k)
        """
        self.T_star = threshold
        self.W_left = window_left
        self.W_right = window_right
        self.T_lower = threshold - window_left   # T* - W_left
        self.T_upper = threshold + window_right  # T* + W_right
        
        # New policy window parameters
        self.new_policy_W_left = new_policy_window_left
        self.new_policy_W_right = new_policy_window_right
        
        # Storage for results
        self.bin_centers = None
        self.f_obs = None
        self.f_cf = None
        self.F_obs = None
        self.F_cf = None
        
        # Bunching statistics
        self.q_N_obs = None
        self.q_R_obs = None
        self.q_N_cf = None
        self.q_R_cf = None
        self.E = None  # Excess mass
        self.Delta_R = None  # Missing mass
        self.b = None  # Bunching ratio
        
        # Step 2: Effective wedge
        self.tau_e = None
        
        # Step 3: Substitution elasticity
        self.sigma = None
        
    # ========================================================================
    # STEP 1: BUILD COUNTERFACTUAL & BUNCHING STATISTICS
    # ========================================================================
    
    def load_and_prepare_data(self):
        """Load synthetic firm data and prepare binned distributions."""
        
        # Load data
        data_path = Path(__file__).parent / 'synthetic_firms_turnover.csv'
        df = pd.read_csv(data_path)
        
        # Focus on wider range for counterfactual estimation
        df_filtered = df[(df['annual_turnover_k'] >= 20) & (df['annual_turnover_k'] <= 140)].copy()
        
        # Create bins of £1k intervals
        bin_edges = np.arange(19.5, 140.5, 1.0)
        self.bin_centers = np.arange(20, 140)  # 20k to 139k
        
        # Calculate observed histogram (density)
        hist_counts, _ = np.histogram(df_filtered['annual_turnover_k'], 
                                    bins=bin_edges, weights=df_filtered['weight'])
        
        # Normalize to get density (f^obs)
        bin_width = 1.0
        self.f_obs = hist_counts / bin_width
        
        return df_filtered
        
    def fit_counterfactual(self):
        """
        Fit the counterfactual density f^cf(T) using the same methodology as bunching_analysis.py
        Excludes fixed range [80, 100] around threshold and uses degree 3 polynomial.
        """
        
        # Use same exclusion range as bunching_analysis.py: [80, 100]
        y_minus = 80  # Lower bound of excluded region
        y_plus = 100  # Upper bound of excluded region
        exclude_mask = (self.bin_centers >= y_minus) & (self.bin_centers <= y_plus)
        
        # Fit on data outside the window
        reg_mask = ~exclude_mask
        
        # Use distance from threshold as feature
        y_dist = self.bin_centers - self.T_star
        
        # Fit polynomial (degree 3 as in bunching_analysis.py)
        poly_features = PolynomialFeatures(degree=3, include_bias=True)
        X_poly = poly_features.fit_transform(y_dist[reg_mask].reshape(-1, 1))
        
        # Fit regression
        reg = LinearRegression(fit_intercept=False)
        reg.fit(X_poly, self.f_obs[reg_mask])
        
        # Predict counterfactual for all points
        X_all = poly_features.transform(y_dist.reshape(-1, 1))
        self.f_cf = reg.predict(X_all)
        
        # Ensure positive predictions (same as bunching_analysis.py)
        self.f_cf = np.maximum(self.f_cf, 0)
        
    def compute_cdfs(self):
        """Compute CDFs F^obs and F^cf."""
        
        # Simple cumulative sum for CDF (normalized by total mass)
        bin_width = 1.0
        
        # Observed CDF
        cumsum_obs = np.cumsum(self.f_obs * bin_width)
        self.F_obs = cumsum_obs / cumsum_obs[-1]
        
        # Counterfactual CDF
        cumsum_cf = np.cumsum(self.f_cf * bin_width)
        self.F_cf = cumsum_cf / cumsum_cf[-1]
        
    def compute_masses_in_window(self):
        """
        Compute masses in the window as per the formulas:
        q_N^obs, q_R^obs, q_N^cf, q_R^cf
        """
        
        # Find indices for integration bounds
        mask_N = (self.bin_centers >= self.T_lower) & (self.bin_centers < self.T_star)
        mask_R = (self.bin_centers >= self.T_star) & (self.bin_centers <= self.T_upper)
        
        bin_width = 1.0
        
        # Observed masses
        self.q_N_obs = np.sum(self.f_obs[mask_N] * bin_width)
        self.q_R_obs = np.sum(self.f_obs[mask_R] * bin_width)
        
        # Counterfactual masses  
        self.q_N_cf = np.sum(self.f_cf[mask_N] * bin_width)
        self.q_R_cf = np.sum(self.f_cf[mask_R] * bin_width)
        
    def compute_excess_missing_mass(self):
        """
        Compute excess mass E and missing mass Delta_R:
        E = ∫[f^obs - f^cf]_+ dT  (in left window)
        Delta_R = ∫[f^cf - f^obs]_+ dT  (in right window)
        """
        
        # Masks for left and right windows
        mask_N = (self.bin_centers >= self.T_lower) & (self.bin_centers < self.T_star)
        mask_R = (self.bin_centers >= self.T_star) & (self.bin_centers <= self.T_upper)
        
        bin_width = 1.0
        
        # Excess mass in left window: [f^obs - f^cf]_+
        excess_left = np.maximum(self.f_obs[mask_N] - self.f_cf[mask_N], 0)
        self.E = np.sum(excess_left * bin_width)
        
        # Missing mass in right window: [f^cf - f^obs]_+
        missing_right = np.maximum(self.f_cf[mask_R] - self.f_obs[mask_R], 0)
        self.Delta_R = np.sum(missing_right * bin_width)
        
    def compute_bunching_ratio(self):
        """
        Compute bunching ratio: b = (q_N^obs - q_N^cf) / q_N^cf
        """
        
        if self.q_N_cf > 0:
            self.b = (self.q_N_obs - self.q_N_cf) / self.q_N_cf
        else:
            self.b = 0
            
    # ========================================================================
    # STEP 2: SET EFFECTIVE WEDGE τₑ
    # ========================================================================
    
    def set_effective_wedge(self, tau_e=None, lambda_param=None, rho=None, tau=None, s_c=None, v=None):
        """
        Step 2: Set the (constant) effective wedge τₑ
        
        Args:
            tau_e: Direct value for effective wedge (if provided, overrides calculation)
            lambda_param: λ parameter for accounting build
            rho: ρ parameter for accounting build  
            tau: τ base tax rate
            s_c: s_c parameter
            v: v parameter
        """
        
        if tau_e is not None:
            # Direct specification
            self.tau_e = tau_e
            print(f"Step 2: Using given effective wedge τₑ = {self.tau_e:.4f}")
        elif all(param is not None for param in [lambda_param, rho, tau, s_c, v]):
            # Accounting build: τₑ = λ(1-ρ)τ - τs_c*v
            self.tau_e = lambda_param * (1 - rho) * tau - tau * s_c * v
            print(f"Step 2: Computed effective wedge τₑ = {self.tau_e:.4f}")
            print(f"  λ={lambda_param}, ρ={rho}, τ={tau}, s_c={s_c}, v={v}")
        else:
            # Default calibration for UK VAT
            # Reasonable estimates for UK VAT registration costs
            self.tau_e = 0.05  # 5% effective wedge
            print(f"Step 2: Using default effective wedge τₑ = {self.tau_e:.4f}")
            
    # ========================================================================
    # STEP 3: CALIBRATE SUBSTITUTION ELASTICITY σ
    # ========================================================================
    
    def calibrate_substitution_elasticity(self):
        """
        Step 3: Calibrate the substitution elasticity σ
        
        Uses CES/logit share equation:
        σ = ln(q_R^cf/q_N^cf / q_R^obs/q_N^obs) / ln(1 + τₑ)
        """
        
        if self.tau_e is None:
            raise ValueError("Must set effective wedge τₑ before calibrating elasticity")
            
        if self.q_N_obs <= 0 or self.q_R_obs <= 0 or self.q_N_cf <= 0 or self.q_R_cf <= 0:
            raise ValueError("All masses must be positive for elasticity calibration")
            
        # Calculate ratio of ratios
        observed_ratio = self.q_R_obs / self.q_N_obs
        counterfactual_ratio = self.q_R_cf / self.q_N_cf
        
        ratio_of_ratios = counterfactual_ratio / observed_ratio
        
        # Calculate elasticity: σ = ln(ratio_of_ratios) / ln(1 + τₑ)
        if ratio_of_ratios > 0 and (1 + self.tau_e) > 0:
            self.sigma = np.log(ratio_of_ratios) / np.log(1 + self.tau_e)
        else:
            self.sigma = 0
            print("Warning: Invalid values for elasticity calculation, setting σ = 0")
            
        print(f"Step 3: Calibrated substitution elasticity σ = {self.sigma:.4f}")
        print(f"  q_R^obs/q_N^obs = {observed_ratio:.4f}")
        print(f"  q_R^cf/q_N^cf = {counterfactual_ratio:.4f}")
        print(f"  Ratio of ratios = {ratio_of_ratios:.4f}")
        print(f"  ln(1 + τₑ) = {np.log(1 + self.tau_e):.4f}")
    
    # ========================================================================
    # STEP 4: ADVANCED PROBABILISTIC MAPPING (MICRO-LEVEL NO-NOTCH COUNTERFACTUAL)
    # ========================================================================
    
    def compute_aggregate_displaced_share(self):
        """
        Step 4a: Compute aggregate displaced share Π = 1 - (1 + τₑ)^(-σ)
        """
        if self.tau_e is None or self.sigma is None:
            raise ValueError("Must complete Steps 2-3 before computing displaced share")
            
        self.Pi = 1 - (1 + self.tau_e)**(-self.sigma)
        print(f"Step 4a: Aggregate displaced share Π = {self.Pi:.4f}")
        
    def compute_local_bunching_probability(self, T_obs):
        """
        Step 4b: Compute local bunching probability π(T^obs) for given turnover
        π(T^obs) = Π * [f^obs(T^obs) - f^cf(T^obs)]_+ / E
        
        Args:
            T_obs: Observed turnover (scalar or array)
            
        Returns:
            Local bunching probability (scalar or array)
        """
        if not hasattr(self, 'Pi'):
            self.compute_aggregate_displaced_share()
            
        # Create interpolation functions for densities
        f_obs_interp = interp1d(self.bin_centers, self.f_obs, kind='linear', 
                               bounds_error=False, fill_value=0)
        f_cf_interp = interp1d(self.bin_centers, self.f_cf, kind='linear', 
                              bounds_error=False, fill_value=0)
        
        # Compute excess density at T_obs
        excess_density = np.maximum(f_obs_interp(T_obs) - f_cf_interp(T_obs), 0)
        
        # Local bunching probability: what fraction of firms at T_obs are bunchers?
        # All excess density should be bunchers, so π = excess / observed
        pi_T_obs = excess_density / f_obs_interp(T_obs) if f_obs_interp(T_obs) > 0 else 0
        
        return pi_T_obs
        
    def compute_rank_among_bunchers(self, T_obs):
        """
        Step 4c: Compute rank among bunchers u(T^obs)
        u(T^obs) = ∫[T*-W to T^obs] [f^obs - f^cf]_+ dT / E
        
        Args:
            T_obs: Observed turnover (must be in [T*-W, T*])
            
        Returns:
            Rank among bunchers ∈ [0,1]
        """
        # Only valid for T_obs in [T*-W, T*]
        T_obs = np.clip(T_obs, self.T_lower, self.T_star)
        
        # Find integration bounds in our bin indices
        start_idx = np.searchsorted(self.bin_centers, self.T_lower, side='left')
        end_idx = np.searchsorted(self.bin_centers, T_obs, side='right')
        
        # Compute cumulative excess mass up to T_obs
        if end_idx <= start_idx:
            return 0.0
            
        # Get the relevant range
        bin_subset = self.bin_centers[start_idx:end_idx]
        f_obs_subset = self.f_obs[start_idx:end_idx]
        f_cf_subset = self.f_cf[start_idx:end_idx]
        
        # Compute excess mass in this range
        bin_width = 1.0
        excess_subset = np.maximum(f_obs_subset - f_cf_subset, 0)
        cumulative_excess = np.sum(excess_subset * bin_width)
        
        # Rank among bunchers
        u_T_obs = cumulative_excess / self.E if self.E > 0 else 0
        
        return np.clip(u_T_obs, 0, 1)
        
    def compute_counterfactual_mapping(self, T_obs):
        """
        Step 4d: Compute deterministic counterfactual mapping E[T^cf | T^obs]
        
        E[T^cf | T^obs] = (1 - π(T^obs)) * T^obs + π(T^obs) * (F^cf)^(-1)(F^cf(T*) + u(T^obs) * Δ_R)
        
        Args:
            T_obs: Observed turnover (scalar or array)
            
        Returns:
            Expected counterfactual turnover T^cf
        """
        T_obs = np.atleast_1d(T_obs)
        T_cf = np.zeros_like(T_obs, dtype=float)
        
        # Create CDF interpolation function
        # Normalize CDF to be between 0 and 1
        F_cf_normalized = self.F_cf
        F_cf_interp = interp1d(self.bin_centers, F_cf_normalized, kind='linear',
                              bounds_error=False, fill_value='extrapolate')
        
        # Inverse CDF function (approximate)
        cdf_values = F_cf_normalized
        inverse_cdf = interp1d(cdf_values, self.bin_centers, kind='linear',
                              bounds_error=False, fill_value='extrapolate')
        
        # Get F^cf(T*)
        F_cf_at_threshold = F_cf_interp(self.T_star)
        
        for i, T_obs_val in enumerate(T_obs):
            if self.T_lower <= T_obs_val <= self.T_star:
                # In bunching region - apply the mapping
                
                # Compute local bunching probability
                pi_val = self.compute_local_bunching_probability(T_obs_val)
                
                # Compute rank among bunchers
                u_val = self.compute_rank_among_bunchers(T_obs_val)
                
                # Compute the CDF argument
                cdf_arg = F_cf_at_threshold + u_val * self.Delta_R / np.sum(self.f_cf)
                cdf_arg = np.clip(cdf_arg, 0, 1)  # Ensure valid CDF value
                
                # Apply the mapping formula
                T_cf_displaced = inverse_cdf(cdf_arg)
                T_cf[i] = (1 - pi_val) * T_obs_val + pi_val * T_cf_displaced
                
            else:
                # Outside bunching region - no change
                T_cf[i] = T_obs_val
                
        return T_cf if len(T_cf) > 1 else T_cf[0]
        
    def run_step4_analysis(self, sample_turnovers=None):
        """
        Step 4: Run micro-level mapping analysis
        
        Args:
            sample_turnovers: Array of turnover values to analyze (optional)
        """
        
        if self.tau_e is None or self.sigma is None:
            raise ValueError("Must complete Steps 1-3 before running Step 4")
            
        print(f"\nStep 4: Micro-level elasticity-aware mapping")
        print("-" * 50)
        
        # Compute aggregate displaced share
        self.compute_aggregate_displaced_share()
        
        # Use default sample if none provided
        if sample_turnovers is None:
            # Sample firms in the bunching region
            sample_turnovers = np.linspace(self.T_lower, self.T_star, 11)  # 11 points from T*-W to T*
            
        print(f"Analyzing {len(sample_turnovers)} sample turnover points:")
        print(f"Sample range: £{sample_turnovers[0]:.1f}k to £{sample_turnovers[-1]:.1f}k")
        
        # Compute mappings for sample
        results = []
        for T_obs in sample_turnovers:
            pi_val = self.compute_local_bunching_probability(T_obs)
            u_val = self.compute_rank_among_bunchers(T_obs)
            T_cf_val = self.compute_counterfactual_mapping(T_obs)
            
            results.append({
                'T_obs': T_obs,
                'pi': pi_val,
                'u': u_val,
                'T_cf': T_cf_val,
                'displacement': T_cf_val - T_obs
            })
            
        # Create results DataFrame
        results_df = pd.DataFrame(results)
        
        # Print summary
        print(f"\nStep 4 Results Summary:")
        print(f"Average bunching probability: {results_df['pi'].mean():.4f}")
        print(f"Average displacement: £{results_df['displacement'].mean():.2f}k")
        print(f"Max displacement: £{results_df['displacement'].max():.2f}k")
        
        # Store results
        self.step4_results = results_df
        
        return results_df
    def run_analysis(self, tau_e=None, include_step4=False, **wedge_params):
        """Run the complete Steps 1-4 analysis."""
        
        step_range = "Steps 1-4" if include_step4 else "Steps 1-3"
        print(f"{step_range}: Counterfactual, Wedge, Elasticity" + 
              (", and Micro Mapping" if include_step4 else ""))
        print("=" * 70)
        
        # Step 1: Load and prepare data
        print("\nStep 1: Building counterfactual & bunching stats")
        print("-" * 50)
        df = self.load_and_prepare_data()
        print(f"Loaded {len(df):,} firm observations")
        
        # Fit counterfactual
        self.fit_counterfactual()
        print(f"Fitted counterfactual excluding window [{self.T_lower}, {self.T_upper}]")
        
        # Compute CDFs
        self.compute_cdfs()
        
        # Compute all masses and statistics
        self.compute_masses_in_window()
        self.compute_excess_missing_mass()
        self.compute_bunching_ratio()
        
        # Step 2: Set effective wedge
        print(f"\nStep 2: Setting effective wedge")
        print("-" * 50)
        self.set_effective_wedge(tau_e=tau_e, **wedge_params)
        
        # Step 3: Calibrate substitution elasticity
        print(f"\nStep 3: Calibrating substitution elasticity")
        print("-" * 50)
        self.calibrate_substitution_elasticity()
        
        # Step 4: Micro-level mapping (optional)
        if include_step4:
            self.run_step4_analysis()
        
        # Print results
        self.print_results()
        
        # Apply Step 5: Forward map to new policy (£100k threshold)
        if include_step4:  # Only do Step 5 if we're doing the full analysis
            self.step5_forward_map_to_new_policy(T_star_new=100)
        
        # Create firm mappings for Steps 6-7 (sample-based for demonstration)
        if include_step4:
            self.create_sample_firm_mappings()
            
            # Apply Steps 6-7: Revenue mapping and elasticity calculations
            if hasattr(self, 'firm_mappings'):
                # Step 6: Revenue mapping (old → new policy)  
                self.step6_revenue_mapping(tau_old=0.20, tau_new=0.20)  # Same rate, different threshold
                
                # Step 7: Elasticity calculations
                self.step7_elasticity_calculations(tau_old=0.20)
        
        # Create visualization with Step 4 and optionally Step 5
        include_step5_plot = include_step4 and hasattr(self, 'f_new_policy')
        self.plot_results(include_step5=include_step5_plot)
        
        # Apply Step 4 advanced mapping to synthetic firms and save results  
        self.apply_step4_to_synthetic_firms('synthetic_firms_step4_mapped.csv')
        
        return self.get_results_dict()
    
    # ========================================================================
    # STEP 5: FORWARD MAP TO NEW POLICY (£100K THRESHOLD)
    # ========================================================================
    
    def step5_forward_map_to_new_policy(self, T_star_new=100, tau_e_new=None):
        """
        Step 5: Forward map from no-notch counterfactual to new policy (£100k threshold)
        
        Pipeline: Real (£90k) → Counterfactual (no notch) → New Policy (£100k)
        
        Args:
            T_star_new: New threshold in £k (default 100k)
            tau_e_new: New effective wedge (default same as original)
        """
        
        print(f"\nStep 5: Forward mapping to NEW policy")
        print("=" * 50)
        print(f"New threshold: £{T_star_new}k (was £{self.T_star}k)")
        
        # Use same effective wedge if not specified
        if tau_e_new is None:
            tau_e_new = self.tau_e
            print(f"Using same effective wedge: τₑ' = {tau_e_new:.4f}")
        else:
            print(f"New effective wedge: τₑ' = {tau_e_new:.4f}")
        
        # Step 5a: New displaced share under new wedge
        Pi_new = 1 - (1 + tau_e_new)**(-self.sigma)
        print(f"New displaced share: Π' = {Pi_new:.4f}")
        
        # Step 5b: Recenter the no-notch density at new threshold
        # The counterfactual f_cf becomes the base for the new policy
        
        # Step 5c: Apply reverse mapping from counterfactual to new observed
        f_new_policy = self.create_new_policy_distribution(T_star_new, tau_e_new, Pi_new)
        
        # Store results
        self.T_star_new = T_star_new
        self.tau_e_new = tau_e_new
        self.Pi_new = Pi_new
        self.f_new_policy = f_new_policy
        
        print(f"Step 5 complete: Generated new policy distribution with bunching at £{T_star_new}k")
        
        return f_new_policy
    
    def create_new_policy_distribution(self, T_star_new, tau_e_new, Pi_new):
        """
        Create new policy distribution with bunching at new threshold.
        Uses reverse mapping from counterfactual to new observed distribution.
        """
        
        print(f"Creating new policy distribution with advanced mapping...")
        
        # Start with the counterfactual as base (no-notch world)
        f_new = self.f_cf.copy()
        
        # Apply reverse mapping to create bunching at new threshold
        # This is the inverse of Step 4: Counterfactual → New Policy
        
        # Use new policy window parameters
        W_left_new = self.new_policy_W_left
        W_right_new = self.new_policy_W_right  
        T_lower_new = T_star_new - W_left_new
        T_upper_new = T_star_new + W_right_new
        
        # Find bins corresponding to new threshold region
        new_region_mask = (self.bin_centers >= T_lower_new) & (self.bin_centers <= T_upper_new)
        above_threshold_mask = (self.bin_centers > T_star_new) & (self.bin_centers <= T_upper_new)
        
        if not np.any(above_threshold_mask):
            print(f"Warning: No bins above new threshold £{T_star_new}k in analysis range")
            return f_new
        
        # Calculate how much mass should move down to create bunching
        # Mass in region above new threshold in counterfactual
        mass_above = np.sum(self.f_cf[above_threshold_mask])
        
        # How much should move down (based on new displaced share)
        mass_to_move = Pi_new * mass_above
        
        print(f"  Mass above new threshold: {mass_above:.0f}")
        print(f"  Mass to move down (create bunching): {mass_to_move:.0f}")
        
        # Redistribute mass: move from above threshold to below (creating bunching)
        if mass_to_move > 0:
            # Reduce density above threshold
            reduction_factor = (1 - Pi_new)
            f_new[above_threshold_mask] *= reduction_factor
            
            # Add mass below threshold (distributed according to distance from threshold)
            below_threshold_mask = (self.bin_centers >= T_lower_new) & (self.bin_centers <= T_star_new)
            
            if np.any(below_threshold_mask):
                # Weight by inverse distance from new threshold (closer bins get more mass)
                distances = T_star_new - self.bin_centers[below_threshold_mask]
                distances = np.maximum(distances, 0.5)  # Minimum distance
                weights = 1.0 / distances
                weights = weights / np.sum(weights)  # Normalize
                
                # Distribute the moved mass
                f_new[below_threshold_mask] += mass_to_move * weights
                
                print(f"  Redistributed mass to {np.sum(below_threshold_mask)} bins below new threshold")
        
        # Apply smoothing to eliminate sharp changes
        f_new = self.apply_smoothing(f_new)
        
        return f_new
    
    def apply_smoothing(self, distribution):
        """Apply aggressive smoothing to eliminate sharp changes in Step 5 curve."""
        smooth_dist = distribution.copy()
        
        # Multiple passes of progressively wider smoothing
        
        # Pass 1: 3-point moving average
        for i in range(1, len(smooth_dist) - 1):
            smooth_dist[i] = 0.25 * smooth_dist[i-1] + 0.5 * smooth_dist[i] + 0.25 * smooth_dist[i+1]
        
        # Pass 2: 5-point moving average  
        for i in range(2, len(smooth_dist) - 2):
            smooth_dist[i] = 0.1 * smooth_dist[i-2] + 0.2 * smooth_dist[i-1] + 0.4 * smooth_dist[i] + 0.2 * smooth_dist[i+1] + 0.1 * smooth_dist[i+2]
        
        # # Pass 3: 7-point moving average (more aggressive)
        # for i in range(3, len(smooth_dist) - 3):
        #     smooth_dist[i] = (0.05 * smooth_dist[i-3] + 0.1 * smooth_dist[i-2] + 0.15 * smooth_dist[i-1] + 
        #                     0.4 * smooth_dist[i] + 0.15 * smooth_dist[i+1] + 0.1 * smooth_dist[i+2] + 0.05 * smooth_dist[i+3])
        
        # Pass 4: 9-point moving average (very aggressive)
        # for i in range(4, len(smooth_dist) - 4):
        #     weights = [0.03, 0.06, 0.09, 0.12, 0.4, 0.12, 0.09, 0.06, 0.03]
        #     smooth_dist[i] = sum(w * smooth_dist[i + j - 4] for j, w in enumerate(weights))
        
        # Pass 5: Final Gaussian-like smoothing
        for i in range(5, len(smooth_dist) - 5):
            # 11-point Gaussian-weighted average
            weights = [0.02, 0.03, 0.05, 0.08, 0.12, 0.4, 0.12, 0.08, 0.05, 0.03, 0.02]
            smooth_dist[i] = sum(w * smooth_dist[i + j - 5] for j, w in enumerate(weights))
        
        return smooth_dist
    
    # ========================================================================
    # STEP 6: REVENUE MAPPING OLD → NEW 
    # ========================================================================
    
    def step6_revenue_mapping(self, tau_old=0.20, tau_new=0.20):
        """
        Step 6: Revenue mapping from old to new policy
        Calculate VAT revenue under both regimes using firm-level mapping
        """
        print(f"\n" + "="*70)
        print("STEP 6: REVENUE MAPPING OLD → NEW")
        print("="*70)
        
        # Reasonable assumptions for missing parameters (imputed from typical UK firms)
        # These would ideally come from supply-use tables by sector
        theta_default = 0.85      # Share of taxable outputs (85% for typical firms)
        s_c_default = 0.45        # Input cost share (45% of turnover)
        v_default = 0.70          # VAT-able share of inputs (70%)
        
        print(f"Using imputed parameters:")
        print(f"  θ (taxable output share): {theta_default:.2f}")
        print(f"  s_c (input cost share): {s_c_default:.2f}") 
        print(f"  v (VAT-able input share): {v_default:.2f}")
        print(f"  Old VAT rate: {tau_old:.1%}")
        print(f"  New VAT rate: {tau_new:.1%}")
        
        # Load firm data and compute revenues
        if not hasattr(self, 'firm_mappings'):
            print("Error: Need Step 4 firm mappings. Run step4_advanced_mapping first.")
            return
            
        # Calculate firm-level revenues
        revenues_old = []
        revenues_new = []
        revenue_changes = []
        
        print(f"\nCalculating revenues for {len(self.firm_mappings)} firms...")
        
        for i, (T_old, T_new) in enumerate(self.firm_mappings):
            # Firm-level VAT parameters (in practice, would vary by sector)
            theta_i = theta_default
            s_c_i = s_c_default  
            v_i = v_default
            
            # Revenue under old regime: V_old = τ_old * (θ * T_old - v * s_c * T_old)
            V_old = tau_old * (theta_i * T_old - v_i * s_c_i * T_old)
            V_old = max(0, V_old)  # Non-negative revenue
            
            # Revenue under new regime: V_new = τ_new * (θ * T_new - v * s_c * T_new)  
            V_new = tau_new * (theta_i * T_new - v_i * s_c_i * T_new)
            V_new = max(0, V_new)  # Non-negative revenue
            
            revenues_old.append(V_old)
            revenues_new.append(V_new)
            revenue_changes.append(V_new - V_old)
        
        # Store results
        self.revenues_old = np.array(revenues_old)
        self.revenues_new = np.array(revenues_new) 
        self.revenue_changes = np.array(revenue_changes)
        
        # Aggregate results
        total_revenue_old = np.sum(self.revenues_old)
        total_revenue_new = np.sum(self.revenues_new)
        total_change = total_revenue_new - total_revenue_old
        
        print(f"\n" + "-"*50)
        print("STEP 6 RESULTS:")
        print("-"*50)
        print(f"Total VAT revenue (old policy): £{total_revenue_old:,.0f}k")
        print(f"Total VAT revenue (new policy): £{total_revenue_new:,.0f}k")
        print(f"Revenue change: £{total_change:,.0f}k ({100*total_change/total_revenue_old:+.2f}%)")
        
        # Distribution of revenue changes
        positive_changes = self.revenue_changes[self.revenue_changes > 0]
        negative_changes = self.revenue_changes[self.revenue_changes < 0]
        
        print(f"\nFirm-level revenue impacts:")
        print(f"  Firms with revenue increase: {len(positive_changes):,} ({100*len(positive_changes)/len(self.revenue_changes):.1f}%)")
        print(f"  Firms with revenue decrease: {len(negative_changes):,} ({100*len(negative_changes)/len(self.revenue_changes):.1f}%)")
        if len(positive_changes) > 0:
            print(f"  Average increase: £{np.mean(positive_changes):.2f}k")
        if len(negative_changes) > 0:
            print(f"  Average decrease: £{np.mean(negative_changes):.2f}k")
        
        return {
            'total_old': total_revenue_old,
            'total_new': total_revenue_new, 
            'total_change': total_change,
            'change_percent': 100*total_change/total_revenue_old
        }
    
    # ========================================================================
    # STEP 7: ELASTICITY CALCULATIONS
    # ========================================================================
    
    def step7_elasticity_calculations(self, tau_old=0.20, epsilon_tau=0.01, epsilon_threshold=5):
        """
        Step 7: Calculate elasticities (behavioural and revenue)
        """
        print(f"\n" + "="*70)
        print("STEP 7: ELASTICITY CALCULATIONS")  
        print("="*70)
        
        # Behavioral (odds) elasticity from Step 3 calibration
        behavioral_elasticity = -self.sigma
        
        print(f"1) Behavioral (odds) elasticity w.r.t wedge:")
        print(f"   d ln(q_R/q_N) / d ln(1+τ_e) = -σ = {behavioral_elasticity:.3f}")
        
        # Revenue elasticity w.r.t VAT rate (finite differences)
        print(f"\n2) Revenue elasticity w.r.t VAT rate:")
        print(f"   Computing finite differences with ε = {epsilon_tau:.1%}...")
        
        # Baseline revenue (from Step 6)
        if not hasattr(self, 'revenues_old'):
            print("   Error: Run step6_revenue_mapping first")
            return
            
        baseline_revenue = np.sum(self.revenues_old)
        
        # Simulate τ + ε 
        tau_plus = tau_old + epsilon_tau
        self.run_policy_simulation(tau_new=tau_plus)
        revenue_plus = self.calculate_revenue_for_rate(tau_plus)
        
        # Simulate τ - ε
        tau_minus = tau_old - epsilon_tau  
        self.run_policy_simulation(tau_new=tau_minus)
        revenue_minus = self.calculate_revenue_for_rate(tau_minus)
        
        # Revenue elasticity = (dV/V) / (dτ/τ)
        dV_dtau = (revenue_plus - revenue_minus) / (2 * epsilon_tau)
        revenue_elasticity_rate = (dV_dtau * tau_old) / baseline_revenue
        
        print(f"   dV/dτ = £{dV_dtau:,.0f}k per percentage point")
        print(f"   Revenue elasticity w.r.t rate = {revenue_elasticity_rate:.3f}")
        
        # Revenue elasticity w.r.t threshold (finite differences)
        print(f"\n3) Revenue elasticity w.r.t threshold:")
        print(f"   Computing finite differences with ε = £{epsilon_threshold}k...")
        
        # Simulate T* + ε
        threshold_plus = self.T_star + epsilon_threshold
        revenue_threshold_plus = self.calculate_revenue_for_threshold(threshold_plus)
        
        # Simulate T* - ε  
        threshold_minus = self.T_star - epsilon_threshold
        revenue_threshold_minus = self.calculate_revenue_for_threshold(threshold_minus)
        
        # Revenue elasticity = (dV/V) / (dT*/T*)
        dV_dthreshold = (revenue_threshold_plus - revenue_threshold_minus) / (2 * epsilon_threshold)
        revenue_elasticity_threshold = (dV_dthreshold * self.T_star) / baseline_revenue
        
        print(f"   dV/dT* = £{dV_dthreshold:,.0f}k per £1k threshold change")
        print(f"   Revenue elasticity w.r.t threshold = {revenue_elasticity_threshold:.3f}")
        
        print(f"\n" + "-"*50)
        print("STEP 7 RESULTS:")
        print("-"*50)
        print(f"Behavioral elasticity (σ): {-behavioral_elasticity:.3f}")
        print(f"Revenue elasticity w.r.t rate: {revenue_elasticity_rate:.3f}")  
        print(f"Revenue elasticity w.r.t threshold: {revenue_elasticity_threshold:.3f}")
        
        return {
            'behavioral_elasticity': behavioral_elasticity,
            'revenue_elasticity_rate': revenue_elasticity_rate,
            'revenue_elasticity_threshold': revenue_elasticity_threshold
        }
    
    def run_policy_simulation(self, tau_new):
        """Helper: Run quick policy simulation for elasticity calculation"""
        # Recompute effective wedge for new rate
        lambda_param = 0.75  # B2C share assumption
        rho = 0.50          # Pass-through assumption  
        s_c = 0.45          # Input cost share
        v = 0.70            # VAT-able input share
        
        tau_e_new = lambda_param * (1 - rho) * tau_new - tau_new * s_c * v
        
        # Recompute displaced share
        Pi_new = 1 - (1 + tau_e_new)**(-self.sigma)
        
        # Update firm mappings (simplified)
        self.Pi_simulation = Pi_new
    
    def calculate_revenue_for_rate(self, tau_rate):
        """Helper: Calculate total revenue for given VAT rate"""
        theta = 0.85
        s_c = 0.45  
        v = 0.70
        
        total_revenue = 0
        for T_old, T_new in self.firm_mappings[:10000]:  # Sample for speed
            V = tau_rate * (theta * T_new - v * s_c * T_new)
            total_revenue += max(0, V)
        
        # Scale up to full population
        scaling_factor = len(self.firm_mappings) / 10000
        return total_revenue * scaling_factor
    
    def calculate_revenue_for_threshold(self, new_threshold):
        """Helper: Calculate total revenue for given threshold"""
        # Simplified: assume threshold change affects firms near boundary
        threshold_effect = (new_threshold - self.T_star) / self.T_star
        
        total_revenue = 0
        tau_rate = 0.20
        theta = 0.85
        s_c = 0.45
        v = 0.70
        
        for T_old, T_new in self.firm_mappings[:10000]:  # Sample for speed
            # Adjust turnover based on threshold change (simplified)
            if 80 <= T_old <= 100:  # Firms near threshold
                T_adjusted = T_new * (1 + 0.1 * threshold_effect)  # Small adjustment
            else:
                T_adjusted = T_new
                
            V = tau_rate * (theta * T_adjusted - v * s_c * T_adjusted)
            total_revenue += max(0, V)
        
        # Scale up to full population  
        scaling_factor = len(self.firm_mappings) / 10000
        return total_revenue * scaling_factor
    
    def map_cf_to_new_policy(self, T_cf):
        """Helper: Map counterfactual turnovers to new policy turnovers using Step 5 distribution"""
        # Simplified mapping using the Step 5 new policy distribution
        T_new = np.zeros_like(T_cf)
        
        for i, turnover in enumerate(T_cf):
            # Find closest bin
            bin_idx = np.argmin(np.abs(self.bin_centers - turnover))
            
            # Use ratio of new policy to counterfactual at this point
            if self.f_cf[bin_idx] > 0:
                ratio = self.f_new_policy[bin_idx] / self.f_cf[bin_idx]
                # Apply small adjustment based on ratio
                T_new[i] = turnover * (0.95 + 0.1 * ratio)  # Conservative adjustment
            else:
                T_new[i] = turnover
        
        return T_new
    
    def create_sample_firm_mappings(self):
        """Create sample firm mappings for Steps 6-7 demonstration"""
        np.random.seed(42)  # Reproducible results
        
        # Create a realistic sample of UK firms 
        n_firms = 100000  # Sample size for demonstration
        
        # Generate realistic firm turnover distribution
        # UK firms: many small firms, few large ones
        turnovers_old = []
        turnovers_new = []
        
        for i in range(n_firms):
            # Generate old turnover with realistic distribution
            if np.random.random() < 0.7:  # 70% small firms
                T_old = np.random.lognormal(np.log(30), 0.8)  # Mean ~£50k
            elif np.random.random() < 0.9:  # 20% medium firms
                T_old = np.random.lognormal(np.log(80), 0.6)  # Mean ~£120k
            else:  # 10% large firms
                T_old = np.random.lognormal(np.log(200), 0.8)  # Mean ~£400k
            
            T_old = max(10, min(500, T_old))  # Constrain to £10k-£500k
            
            # Apply mapping based on Step 4/5 logic
            if 65 <= T_old <= 110:  # Near thresholds - apply bunching effects
                if hasattr(self, 'f_new_policy') and hasattr(self, 'f_cf'):
                    # Use Step 5 mapping
                    bin_idx = np.argmin(np.abs(self.bin_centers - T_old))
                    if self.f_cf[bin_idx] > 0:
                        ratio = self.f_new_policy[bin_idx] / self.f_cf[bin_idx]
                        T_new = T_old * (0.95 + 0.1 * ratio)  # Small adjustment
                    else:
                        T_new = T_old
                else:
                    # Default mapping for threshold change (90k → 100k)
                    if T_old < 90:
                        T_new = T_old * 1.02  # Small increase due to threshold change
                    else:
                        T_new = T_old * 0.98  # Small decrease
            else:
                # Outside bunching region - minimal change
                T_new = T_old * np.random.normal(1.0, 0.01)  # 1% noise
            
            turnovers_old.append(T_old)
            turnovers_new.append(max(10, T_new))  # Minimum £10k
        
        # Store mappings
        self.firm_mappings = list(zip(turnovers_old, turnovers_new))
        
        print(f"Created {len(self.firm_mappings):,} sample firm mappings for Steps 6-7")
        print(f"  Mean old turnover: £{np.mean(turnovers_old):.1f}k")
        print(f"  Mean new turnover: £{np.mean(turnovers_new):.1f}k")
        
    def print_results(self):
        """Print the analysis results."""
        
        has_step4 = hasattr(self, 'step4_results')
        step_range = "Steps 1-4" if has_step4 else "Steps 1-3"
        
        print(f"\n{step_range} Results Summary:")
        print("=" * 50)
        print(f"Threshold T*: £{self.T_star:,}k")
        print(f"Window: -£{self.W_left:,}k/+£{self.W_right:,}k")
        print(f"Analysis range: [{self.T_lower}, {self.T_upper}]")
        
        print(f"\nStep 1 - Bunching Statistics:")
        print("-" * 30)
        print(f"  Masses in window:")
        print(f"    q_N^obs = {self.q_N_obs:.3f}")
        print(f"    q_R^obs = {self.q_R_obs:.3f}")
        print(f"    q_N^cf  = {self.q_N_cf:.3f}")
        print(f"    q_R^cf  = {self.q_R_cf:.3f}")
        print(f"  Excess mass (E) = {self.E:.3f}")
        print(f"  Missing mass (Δ_R) = {self.Delta_R:.3f}")
        print(f"  Bunching ratio (b) = {self.b:.3f}")
        
        print(f"\nStep 2 - Effective Wedge:")
        print("-" * 30)
        print(f"  τₑ = {self.tau_e:.4f}")
        
        print(f"\nStep 3 - Substitution Elasticity:")
        print("-" * 30)
        print(f"  σ = {self.sigma:.4f}")
        
        if has_step4:
            print(f"\nStep 4 - Micro-level Mapping:")
            print("-" * 30)
            print(f"  Aggregate displaced share Π = {self.Pi:.4f}")
            print(f"  Sample firms analyzed: {len(self.step4_results)}")
            print(f"  Avg bunching probability: {self.step4_results['pi'].mean():.4f}")
            print(f"  Avg displacement: £{self.step4_results['displacement'].mean():.2f}k")
        
    def plot_results(self, include_step5=False):
        """Create visualization of Steps 1-4 complete analysis with advanced mapping, optionally including Step 5."""
        
        _, ax = plt.subplots(figsize=(12, 8))
        
        # Plot observed and counterfactual densities (exclude first point T=20k, x=-70)
        y_dist = self.bin_centers - self.T_star
        
        # Skip first point (index 0)
        plot_mask = slice(1, None)
        y_dist_plot = y_dist[plot_mask]
        
        ax.plot(y_dist_plot, self.f_obs[plot_mask], 'o-', color='blue', markersize=3, 
                linewidth=1, label='Original Observed f^obs(T) [£90k]', alpha=0.7)
        ax.plot(y_dist_plot, self.f_cf[plot_mask], '-', color='red', linewidth=2, 
                label='Counterfactual f^cf(T) [No Notch]')
        
        # Add Step 4 advanced mapping result (also skip first point)
        f_step4 = create_advanced_probabilistic_mapping(self)
        ax.plot(y_dist_plot, f_step4[plot_mask], '-', color='green', linewidth=2, 
                label='Step 4 Advanced Mapping Result', alpha=0.8)
        
        # Add Step 5 new policy result if available (also skip first point)
        if include_step5 and hasattr(self, 'f_new_policy'):
            ax.plot(y_dist_plot, self.f_new_policy[plot_mask], '-', color='purple', linewidth=2, 
                    label=f'Step 5 New Policy [£{self.T_star_new}k]', alpha=0.8)
        
        # Shade the window (also skip first point)
        window_mask = (self.bin_centers >= self.T_lower) & (self.bin_centers <= self.T_upper)
        window_mask_plot = window_mask[plot_mask]  # Apply same exclusion to window mask
        ax.fill_between(y_dist_plot[window_mask_plot], 0, self.f_obs[plot_mask][window_mask_plot], 
                       alpha=0.3, color='lightblue', label=f'Window -£{self.W_left}k/+£{self.W_right}k')
        
        # Add vertical lines  
        ax.axvline(x=0, color='black', linestyle='-', linewidth=2, label='Original Threshold £90k')
        ax.axvline(x=-self.W_left, color='gray', linestyle='--', alpha=0.5, label=f'£90k -£{self.W_left}k/+£{self.W_right}k')
        ax.axvline(x=self.W_right, color='gray', linestyle='--', alpha=0.5)
        
        # Add new threshold line if Step 5 is included
        if include_step5 and hasattr(self, 'T_star_new'):
            new_threshold_dist = self.T_star_new - self.T_star  # Distance from original
            ax.axvline(x=new_threshold_dist, color='purple', linestyle='-', linewidth=2, 
                      label=f'New Threshold £{self.T_star_new}k', alpha=0.8)
        
        # Add annotations
        ax.text(0.02, 0.95, f'Bunching ratio b = {self.b:.3f}', 
                transform=ax.transAxes, fontsize=11, 
                bbox=dict(boxstyle="round,pad=0.3", facecolor="lightblue"))
        ax.text(0.02, 0.89, f'Effective wedge τₑ = {self.tau_e:.3f}', 
                transform=ax.transAxes, fontsize=11, 
                bbox=dict(boxstyle="round,pad=0.3", facecolor="lightyellow"))
        ax.text(0.02, 0.83, f'Substitution elasticity σ = {self.sigma:.3f}', 
                transform=ax.transAxes, fontsize=11, 
                bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgreen"))
        ax.text(0.02, 0.77, f'Excess mass E = {self.E:.0f}', 
                transform=ax.transAxes, fontsize=11, 
                bbox=dict(boxstyle="round,pad=0.3", facecolor="lightcoral"))
        
        # Add Step 4 info
        pi_mean = np.mean([self.compute_local_bunching_probability(T) 
                          for T in self.bin_centers[window_mask]])
        ax.text(0.02, 0.71, f'Avg bunching prob π̄ = {pi_mean:.3f}', 
                transform=ax.transAxes, fontsize=11, 
                bbox=dict(boxstyle="round,pad=0.3", facecolor="lightpink"))
        
        # Add Step 5 info if included
        if include_step5 and hasattr(self, 'Pi_new'):
            ax.text(0.02, 0.65, f'New displaced share Π\' = {self.Pi_new:.3f}', 
                    transform=ax.transAxes, fontsize=11, 
                    bbox=dict(boxstyle="round,pad=0.3", facecolor="plum"))
        
        # Formatting
        ax.set_xlabel('Distance from Original Threshold £90k (£1,000)', fontsize=12)
        ax.set_ylabel('Density f(T)', fontsize=12)
        
        if include_step5:
            ax.set_title('Steps 1-5: Complete Pipeline with New Policy', fontsize=14, fontweight='bold')
        else:
            ax.set_title('Steps 1-4: Complete Analysis with Advanced Mapping', fontsize=14, fontweight='bold')
            
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=9)
        ax.set_xlim(-70, 50)
        
        # Save plot
        output_path = Path(__file__).parent / 'bunching_analysis.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"\nPlot saved: {output_path}")
        
    def apply_step4_to_synthetic_firms(self, output_file='synthetic_firms_step4_mapped.csv'):
        """
        Apply advanced Step 4 mapping to synthetic firms and save results.
        """
        
        print("\nApplying Step 4 Advanced Mapping to Synthetic Firms")
        print("=" * 60)
        
        # Load synthetic firms data
        try:
            df = pd.read_csv('synthetic_firms_turnover.csv')
            print(f"Loaded {len(df):,} synthetic firms from synthetic_firms_turnover.csv")
        except FileNotFoundError:
            print("Error: synthetic_firms_turnover.csv not found")
            return None
        
        # Apply Step 4 mapping to each firm's turnover
        print("Applying Step 4 mapping to individual firms...")
        
        # Get observed turnovers
        T_obs = df['annual_turnover_k'].values
        
        # Apply the advanced probabilistic mapping
        print("Creating advanced probabilistic mapping...")
        f_mapped = create_advanced_probabilistic_mapping(self)
        
        # For individual firms, we need to apply the mapping stochastically
        print("Computing counterfactual turnovers for each firm...")
        
        # Initialize counterfactual turnovers
        T_cf = np.zeros_like(T_obs)
        
        # Create mapping probabilities for each turnover level
        mapping_probs = {}
        bin_width = 1.0  # £1k bins
        
        for i, bin_center in enumerate(self.bin_centers):
            if self.T_lower <= bin_center <= self.T_star:
                # Compute bunching probability for this turnover level
                pi_val = self.compute_local_bunching_probability(bin_center)
                
                # Get displacement target
                T_cf_target = self.compute_counterfactual_mapping(bin_center)
                
                mapping_probs[bin_center] = {
                    'pi': pi_val,
                    'cf_target': T_cf_target,
                    'stay_prob': 1 - pi_val,
                    'displace_prob': pi_val
                }
            else:
                # Outside bunching region - no displacement
                mapping_probs[bin_center] = {
                    'pi': 0.0,
                    'cf_target': bin_center,
                    'stay_prob': 1.0,
                    'displace_prob': 0.0
                }
        
        # Apply mapping to each firm
        np.random.seed(42)  # For reproducible results
        n_displaced = 0
        
        for idx, turnover in enumerate(T_obs):
            # Find closest bin center
            bin_center = round(turnover)  # Round to nearest £1k
            
            if bin_center in mapping_probs:
                prob_info = mapping_probs[bin_center]
                
                # Determine if this firm gets displaced
                if np.random.random() < prob_info['displace_prob']:
                    # Firm gets displaced
                    T_cf[idx] = prob_info['cf_target']
                    n_displaced += 1
                else:
                    # Firm stays at original location
                    T_cf[idx] = turnover
            else:
                # Turnover outside our analysis range - no change
                T_cf[idx] = turnover
            
            # Progress indicator
            if (idx + 1) % 100000 == 0:
                print(f"  Processed {idx + 1:,}/{len(T_obs):,} firms...")
        
        # Add results to dataframe
        df_mapped = df.copy()
        df_mapped['step4_counterfactual_turnover_k'] = T_cf
        df_mapped['step4_displacement_k'] = T_cf - T_obs
        
        # Store firm mappings for Steps 6-7 (old_turnover, new_turnover)
        # For Step 5: use Step 5 new policy turnovers if available
        if hasattr(self, 'f_new_policy'):
            # Map counterfactual turnovers to new policy turnovers (simplified)
            T_new_policy = self.map_cf_to_new_policy(T_cf)
        else:
            T_new_policy = T_cf  # If no Step 5, use counterfactual as "new"
        
        self.firm_mappings = list(zip(T_obs, T_new_policy))
        
        # Save results
        df_mapped.to_csv(output_file, index=False)
        
        # Print summary statistics
        displacement = T_cf - T_obs
        nonzero_displacement = displacement[displacement != 0]
        
        print(f"\nStep 4 Advanced Mapping Complete!")
        print("=" * 40)
        print(f"Output file: {output_file}")
        print(f"Total firms processed: {len(df):,}")
        print(f"Firms displaced: {n_displaced:,} ({100*n_displaced/len(df):.2f}%)")
        print(f"Mean displacement: £{displacement.mean():.3f}k")
        if len(nonzero_displacement) > 0:
            print(f"Mean nonzero displacement: £{nonzero_displacement.mean():.3f}k")
            print(f"Max displacement: £{displacement.max():.3f}k")
            print(f"Min displacement: £{displacement.min():.3f}k")
        
        # Weighted statistics
        obs_mean = np.average(T_obs, weights=df['weight'])
        cf_mean = np.average(T_cf, weights=df['weight'])
        
        print(f"\nWeighted Statistics:")
        print(f"  Original mean turnover: £{obs_mean:.1f}k")
        print(f"  Step 4 mapped mean turnover: £{cf_mean:.1f}k")
        print(f"  Mean change: £{cf_mean - obs_mean:.3f}k")
        
        return df_mapped
        
    def get_results_dict(self):
        """Return results as dictionary for use in subsequent steps."""
        
        return {
            'T_star': self.T_star,
            'W_left': self.W_left,
            'W_right': self.W_right,
            'bin_centers': self.bin_centers,
            'f_obs': self.f_obs,
            'f_cf': self.f_cf,
            'F_obs': self.F_obs,
            'F_cf': self.F_cf,
            'q_N_obs': self.q_N_obs,
            'q_R_obs': self.q_R_obs,
            'q_N_cf': self.q_N_cf,
            'q_R_cf': self.q_R_cf,
            'E': self.E,
            'Delta_R': self.Delta_R,
            'b': self.b,
            'tau_e': self.tau_e,
            'sigma': self.sigma
        }


def main():
    """Run Steps 1-4 analysis."""
    
    # ==========================================================================
    # CONFIGURATION: Set your asymmetric windows here
    # ==========================================================================
    # Counterfactual analysis windows (around original £90k threshold)
    counterfactual_window_left = 25    # £10k below threshold (£80k-£90k)
    counterfactual_window_right = 20   # £10k above threshold (£90k-£100k)
    
    # New policy analysis windows (around new £100k threshold)  
    new_policy_window_left = 25        # £10k below new threshold (£90k-£100k)
    new_policy_window_right = 20       # £10k above new threshold (£100k-£110k)
    # ==========================================================================
    
    # Initialize analysis with asymmetric windows
    analysis = CounterfactualBunchingAnalysis(
        threshold=90, 
        window_left=counterfactual_window_left,
        window_right=counterfactual_window_right,
        new_policy_window_left=new_policy_window_left,
        new_policy_window_right=new_policy_window_right
    )
    
    # Run complete analysis with Steps 1-5
    print("STEPS 1-5: COMPLETE BUNCHING ANALYSIS PIPELINE")
    print("Step 1: Counterfactual & bunching statistics")
    print("Step 2: Effective wedge τₑ")
    print("Step 3: Substitution elasticity σ")  
    print("Step 4: Advanced probabilistic mapping (no-notch counterfactual)")
    print("Step 5: Forward map to NEW policy (£100k threshold)")
    print("="*70)
    results = analysis.run_analysis(tau_e=0.05, include_step4=True)
    
    # Show detailed Step 4 results
    if hasattr(analysis, 'step4_results'):
        print("\nDetailed Step 4 Results:")
        print("-" * 40)
        step4_df = analysis.step4_results
        print(step4_df.round(4).to_string(index=False))
        
        # Show example calculations for a few firms
        print(f"\nExample firm mappings:")
        example_firms = [82, 85, 88, 90]  # Firms at different positions
        
        for T_obs in example_firms:
            if analysis.T_lower <= T_obs <= analysis.T_star:
                pi = analysis.compute_local_bunching_probability(T_obs)
                u = analysis.compute_rank_among_bunchers(T_obs) 
                T_cf = analysis.compute_counterfactual_mapping(T_obs)
                
                print(f"  Firm at £{T_obs}k:")
                print(f"    π(T^obs) = {pi:.4f} (bunching probability)")
                print(f"    u(T^obs) = {u:.4f} (rank among bunchers)")
                print(f"    T^cf = £{T_cf:.2f}k (counterfactual turnover)")
                print(f"    Displacement = £{T_cf - T_obs:.2f}k")
                print()
    
    # Visualization removed as requested
    
    # Mapping check visualization removed as requested
    
    return results


# ============================================================================
# STEP 4: ADVANCED PROBABILISTIC MAPPING - MAIN FUNCTION
# ============================================================================

def create_advanced_probabilistic_mapping(analysis, decay_rate=0.01, spread_factor=3.0):
    """
    Step 4: Advanced Probabilistic Mapping - MAIN STEP 4 FUNCTION
    
    This is the primary Step 4 implementation that creates the smooth counterfactual
    distribution shown as the green curve in steps1234_complete_analysis.png.
    
    Creates comprehensive probabilistic mapping that redistributes firms across
    the full range to match the theoretical counterfactual distribution.
    """
    
    # Start with the observed distribution as base
    mapped_distribution = np.copy(analysis.f_obs)
    
    print(f"Creating advanced probabilistic mapping:")
    print(f"- Decay rate: {decay_rate} (controls displacement spread)")
    print(f"- Spread factor: {spread_factor} (controls overall redistribution)")
    
    # Skip first point (T=20k, x=-70) from all calculations
    print(f"Skipping first point (x=-70, T=20k) from mapping calculations")
    
    # For each bin, calculate how much it needs to change to match counterfactual
    deficit = analysis.f_cf - analysis.f_obs  # Positive = need more, negative = have excess
    
    # For each bin in the analysis (skip first point)
    for i, T_obs in enumerate(analysis.bin_centers):
        if i == 0:  # Skip first point (T=20k)
            continue
        original_density = analysis.f_obs[i]
        target_density = analysis.f_cf[i]
        
        if original_density > target_density:
            # This bin has excess firms - redistribute the excess
            excess_firms = original_density - target_density
            
            # Set this bin to its target density
            mapped_distribution[i] = target_density
            
            # Redistribute excess firms across range (excluding first point)
            if excess_firms > 0:
                # Find locations that need more firms (positive deficit, skip first point)
                deficit_mask = (deficit > 0) & (np.arange(len(deficit)) > 0)  # Exclude index 0
                target_locations = analysis.bin_centers[deficit_mask]
                target_deficits = deficit[deficit_mask]
                
                if len(target_locations) > 0:
                    # Create probability weights based on distance and deficit size
                    distances = np.abs(target_locations - T_obs)
                    distance_weights = np.exp(-decay_rate * distances)
                    deficit_weights = target_deficits * spread_factor
                    
                    # Combine distance and deficit weights
                    combined_weights = distance_weights * deficit_weights
                    probs = combined_weights / np.sum(combined_weights)
                    
                    # Distribute excess firms
                    for j, target_turnover in enumerate(target_locations):
                        target_idx = np.where(analysis.bin_centers == target_turnover)[0][0]
                        redistribution = excess_firms * probs[j]
                        mapped_distribution[target_idx] += redistribution
                        
                        # Update deficit to track progress
                        deficit[target_idx] -= redistribution
        # Bins without excess keep their observed density (already set in initialization)
    
    # Check first point before scaling
    print(f"Before scaling: First point mapped={mapped_distribution[0]:.1f}")
    
    # Final adjustment: scale to match total counterfactual mass
    total_cf = np.sum(analysis.f_cf)
    total_mapped = np.sum(mapped_distribution)
    scaling_factor = total_cf / total_mapped if total_mapped > 0 else 1.0
    print(f"Scaling factor: {scaling_factor:.4f}")
    
    if total_mapped > 0:
        mapped_distribution *= scaling_factor
    
    # Check first point after scaling
    print(f"After scaling: First point mapped={mapped_distribution[0]:.1f}")
    
    return mapped_distribution


# ============================================================================
# STEP 4: SUPPORTING FUNCTIONS FOR ADVANCED MAPPING
# ============================================================================

def optimize_advanced_parameters(analysis):
    """Optimize parameters for advanced probabilistic mapping."""
    
    from scipy.optimize import minimize
    
    def mapping_error(params):
        decay_rate, spread_factor = params
        mapped_dist = create_advanced_probabilistic_mapping(analysis, decay_rate, spread_factor)
        error = np.sum((mapped_dist - analysis.f_cf)**2)
        return error
    
    print("Optimizing advanced probabilistic mapping parameters...")
    
    # Optimize decay rate (0.001 to 0.1) and spread factor (0.5 to 5.0)
    result = minimize(mapping_error, x0=[0.01, 2.0], 
                     bounds=[(0.001, 0.1), (0.5, 5.0)],
                     method='L-BFGS-B')
    
    optimal_decay = result.x[0]
    optimal_spread = result.x[1]
    
    print(f"Optimal decay rate: {optimal_decay:.4f}")
    print(f"Optimal spread factor: {optimal_spread:.2f}")
    
    return optimal_decay, optimal_spread




if __name__ == "__main__":
    results = main()