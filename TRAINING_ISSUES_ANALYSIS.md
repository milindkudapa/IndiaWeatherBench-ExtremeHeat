# TRAINING ISSUES - COMPREHENSIVE ANALYSIS

## 🔴 CRITICAL PROBLEMS IDENTIFIED

### 1. **NaN LOSS** - ROOT CAUSE: Missing Normalization Parameters

**Issue:**
- Loss is `nan.0` from the first batch
- Training is completely broken

**Root Cause:**
```
data/indibench_h5/norm_params.json only contains 8 entries:
- diff_mean, diff_std, lat, log_mean, log_std, lon, mean, std

Expected: 49 variables (43 IWB + 6 ERA5-Land)
Actual: 8 generic stat types
Missing: ALL 49 per-variable normalization parameters!
```

**Why This Causes NaN:**
1. Model tries to normalize input data for all 45 variables
2. No normalization params found → uses defaults or gets None
3. Division by zero or invalid operations → NaN
4. NaN propagates through model → NaN loss
5. NaN gradients → model can't train

**Fix Required:**
- Restore correct norm_params.json with ALL 49 variables
- Re-compute ERA5-Land normalization if needed
- Verify all variables present before training

---

### 2. **SLOW TRAINING SPEED** - 5-6x slower than expected

**Observed:**
- Current: ~0.5 it/s  
- Expected: ~2-3 it/s
- Time per epoch: ~42 min (should be ~7-10 min)

**Causes:**
1. **num_workers=0** - Single-threaded data loading
   - No parallel data loading
   - CPU becomes bottleneck
   - GPUs starved waiting for data

2. **HDF5 file locking** issues still present
   - h5clear running in background but incomplete
   - Files still have stale locks

3. **NaN training** overhead
   - Model doing useless computation on NaN values
   - Logging/checkpointing NaN values

**Performance Impact:**
```
Baseline (batch_size=2, num_workers=4): ~1.5 it/s
Current (batch_size=8, num_workers=0):  ~0.5 it/s

Larger batch + single worker = 3x SLOWER!
This is backwards - should be FASTER!
```

---

### 3. **RESUMING FROM CORRUPTED CHECKPOINT**

**Issue:**
```
Line 25: Restored from checkpoint at:
/burg-archive/home/mck2199/ML-Project/checkpoints_era5land/
india_benchmark_era5land/checkpoints/last.ckpt
```

**Problem:**
- Previous run also had NaN loss
- Checkpoint contains corrupted model state
- Training continues from broken state

**Fix:**
- Delete all checkpoints in `checkpoints_era5land/`
- Start fresh training from scratch

---

## 🛠️ COMPREHENSIVE FIX PLAN

### Step 1: Stop Current Training
```bash
# Cancel the broken training job
scancel 5059242
```

### Step 2: Restore Correct Normalization Parameters
```bash
# Check if we have the user-provided correct file
# If not, re-compute from scratch
```

### Step 3: Verify ERA5-Land Integration
```bash
# Validate that all ERA5-Land variables exist in HDF5 files
# Verify data quality (no NaN, reasonable ranges)
```

### Step 4: Delete Corrupted Checkpoints
```bash
rm -rf /burg-archive/home/mck2199/ML-Project/checkpoints_era5land/*
```

### Step 5: Fix Data Loading
```bash
# Wait for h5clear to complete, then test with num_workers=2
# Or use a more robust HDF5 reading approach
```

### Step 6: Restart Training with Fixes
```bash
# Clean start, correct normalization, efficient data loading
sbatch scripts/train_unet_era5land_2gpu.sbatch
```

---

## 📊 EXPECTED RESULTS AFTER FIX

**Training Speed:**
- Target: ~2-3 it/s with batch_size=8, num_workers=4
- Time per epoch: ~7-10 minutes
- Total training time: ~5-7 hours for 40 epochs

**Loss:**
- Should be numeric (not NaN)
- Should decrease over time
- Typical range: 0.001 - 0.1 for weather forecasting

**GPU Utilization:**
- Target: >90% with batch_size=8
- Memory: ~80% of 40GB per GPU

---

## 🎯 PRIORITY ACTIONS

1. **IMMEDIATE:** Cancel current training (wasting resources)
2. **URGENT:** Fix norm_params.json
3. **CRITICAL:** Delete corrupted checkpoints  
4. **IMPORTANT:** Verify ERA5-Land data integrity
5. **OPTIMIZE:** Fix num_workers after h5clear completes

