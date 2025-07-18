# Ubuntu vs macOS Parameter Uprating Fix

## Problem
Ubuntu and macOS were returning different results for parameter uprating. Some parameters were not being uprated on Ubuntu but were being uprated on macOS, causing inconsistent behavior across operating systems.

## Root Cause
The issue was a **dependency order problem** in the parameter processing pipeline that manifested differently on different operating systems due to timing differences in module imports and system initialization.

**Technical Issues**:
1. `BASELINE_GROWFACTORS = create_policyengine_uprating_factors_table()` was called at module import time before the system was fully initialized
2. The function depends on a fully initialized `CountryTaxBenefitSystem` with parameters created during the processing pipeline
3. Different operating systems have different import order/timing behavior, causing the function to run before system initialization on Ubuntu but after on macOS

## Solution
Implemented **deferred initialization** using a proxy object that maintains full backward compatibility while resolving timing issues.

### How It Works
1. **Import Time**: No computation happens, only object creation
2. **First Access**: When `BASELINE_GROWFACTORS` is accessed, it triggers computation
3. **Subsequent Access**: Cached result is returned without recomputation
