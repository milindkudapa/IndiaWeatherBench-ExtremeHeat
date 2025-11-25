# Training Options for UNet

You have **2x NVIDIA A100-PCIE-40GB** GPUs. Here are your training options:

## Option 1: Single GPU (Recommended for First Run)

**Script**: `scripts/train_unet.sbatch`

```bash
sbatch scripts/train_unet.sbatch
```

**Configuration**:
- 1 GPU
- Batch size: 8 (optimized for A100)
- Estimated time: **6-8 hours**

**Best for**: Testing full training pipeline first

---

## Option 2: Dual GPU (Fastest)

**Script**: `scripts/train_unet_2gpu.sbatch`

```bash
sbatch scripts/train_unet_2gpu.sbatch
```

**Configuration**:
- 2 GPUs with DDP (Distributed Data Parallel)
- Batch size: 4 per GPU (8 total)
- Estimated time: **3-4 hours** ⚡

**Best for**: Fastest training after confirming single GPU works

---

## Comparison Table

| Option | GPUs | Batch Size | Time | Speed |
|--------|------|------------|------|-------|
| **Conservative** | 1 | 2 | ~24h | 1x |
| **Optimized Single** | 1 | 8 | ~6h | 4x |
| **Dual GPU** | 2 | 4×2=8 | ~3h | 8x |

---

## Custom Batch Size

You can adjust batch size based on your needs:

### Higher batch size (faster, more memory):
```bash
# Edit the .sbatch file and change:
--data.batch_size=16  # for single GPU
--data.batch_size=8   # per GPU for dual GPU (16 total)
```

### Lower batch size (if OOM errors):
```bash
--data.batch_size=4   # for single GPU
--data.batch_size=2   # per GPU for dual GPU (4 total)
```

---

## How Dual GPU Works

**DDP (Distributed Data Parallel)**:
1. Each GPU gets a copy of the model
2. Each GPU processes different data batches
3. Gradients are synchronized across GPUs
4. Nearly 2x speedup with 2 GPUs

**Key differences in the script**:
- `--gres=gpu:2` - Request 2 GPUs
- `--ntasks-per-node=2` - One task per GPU
- `srun python ...` - Launches distributed training
- `--trainer.devices=2` - Tell PyTorch Lightning to use 2 GPUs

---

## Monitoring

Both options log to the same place:

```bash
# Check job status
squeue -u $USER

# View output
tail -f logs/train_unet_*_JOBID.out

# View on WandB
# https://wandb.ai/milindk-columbia-university/india_benchmark
```

---

## Recommendation

1. **First time**: Use `train_unet.sbatch` (single GPU, batch_size=8)
   - Verify everything works end-to-end
   - ~6 hours completion time

2. **Future runs**: Use `train_unet_2gpu.sbatch` (dual GPU)
   - Maximum speed
   - ~3 hours completion time

Both will produce the same quality model!

