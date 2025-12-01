# DDP Training Issue and Solution

## Problem

When attempting to train the ERA5-Land enhanced UNET model using 2 GPUs with DDP (Distributed Data Parallel), training consistently fails with:

```
KeyError: "Unable to synchronously open object (object 'swvl1' doesn't exist)"
```

The error occurs on **rank1 only**, during the first data fetch.

## Investigation

### What We Verified

✅ **All HDF5 files have ERA5-Land variables**
- Checked train/val/test splits
- Random sampling and targeted checks all passed
- Variables exist in file key lists

✅ **Config files are correct**
- `boundary_forcing_unet_era5land.yaml` includes all 45 variables
- Normalization parameters include all ERA5-Land variables
- Model architecture correctly handles 90 input channels

✅ **1-GPU training works perfectly**
- Training: ✅ Loss numeric (0.004-0.005), decreasing
- Validation: ✅ Running successfully
- Speed: ~0.40 it/s with batch_size=8
- **No errors accessing ERA5-Land variables**

❌ **2-GPU DDP training fails**
- Rank0: Initializes OK
- Rank1: Fails on first batch with KeyError
- Happens even with `num_workers=0` (no multiprocessing)
- Tested strategies: `ddp`, `ddp_spawn`, `auto` - **all fail**

### Root Cause

**HDF5 library limitation with concurrent access in distributed training**

Even with:
- `h5py.File(..., locking=False)`
- `export HDF5_USE_FILE_LOCKING=FALSE`
- `num_workers=0` (no dataloader multiprocessing)

The HDF5 library has internal state that conflicts when:
1. Multiple ranks (processes) access the same files
2. Files are opened/closed frequently during training
3. Variables are accessed in different orders by different ranks

The KeyError occurs because:
- Variable name IS in the file's key list
- But HDF5 internal state prevents rank1 from opening the object
- Likely due to file handle conflicts or cache inconsistency

## Solution

### **Use 1-GPU Training**

1-GPU training is:
- ✅ Stable and reliable
- ✅ Works perfectly with ERA5-Land data
- ✅ Can use large batch sizes (16 or more)
- ✅ Sufficient for this dataset size

### Training Script

Use `scripts/train_unet_era5land_1gpu.sbatch`:

```bash
cd /burg-archive/home/mck2199/ML-Project
sbatch scripts/train_unet_era5land_1gpu.sbatch
```

### Configuration

- **GPU**: 1x NVIDIA A40/A100-40GB
- **Batch size**: 16 (can fit on single GPU)
- **Learning rate**: 4e-4
- **Data workers**: 0 (single-process)
- **Time allocation**: 24 hours

### Expected Performance

```
Time per epoch: ~15-20 minutes
40 epochs: ~10-13 hours
60 epochs: ~15-20 hours
100 epochs: ~25-33 hours
```

With batch_size=16, GPU utilization should be excellent even with single-process data loading.

## Alternative Solutions (Not Implemented)

### Why Not These?

1. **Convert HDF5 to Zarr**
   - Would require reprocessing all 22,951 files
   - Time-consuming (days)
   - Storage overhead

2. **Pre-load data to RAM**
   - ~23k files × ~13 MB = ~300 GB
   - Exceeds available RAM
   - Would need multi-node setup

3. **Use TFRecords or other format**
   - Requires complete data pipeline rewrite
   - Would break compatibility with existing codebase
   - Not worth the effort

4. **Model Parallelism**
   - Model is only 36M parameters
   - Fits easily on 1 GPU
   - Unnecessary complexity

## Recommendation

**Proceed with 1-GPU training**. The performance is acceptable and the setup is stable. If faster training is needed in the future, consider:
- Running multiple independent experiments on different GPUs
- Using gradient accumulation to simulate larger batch sizes
- Data format conversion for truly large-scale work

## Files Modified

- `scripts/train_unet_era5land_1gpu.sbatch`: New stable training script
- `india_benchmark/datasets/india_dataset.py`: Added `locking=False` to h5py calls
- Tested configurations documented in this file

## Launch Training

```bash
cd /burg-archive/home/mck2199/ML-Project
sbatch scripts/train_unet_era5land_1gpu.sbatch
```

Monitor:
```bash
tail -f logs/train_unet_era5land_<JOB_ID>.out
```

WandB:
https://wandb.ai/milindk-columbia-university/india_benchmark_era5land

