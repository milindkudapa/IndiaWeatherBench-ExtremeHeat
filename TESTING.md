# Testing Your Setup Before Full Training

Before running the full 100-epoch training (12-24 hours), verify everything works correctly.

## Option 1: Submit a Quick Test Job (Recommended)

This runs a fast test automatically on a GPU node:

```bash
sbatch scripts/test_setup.sbatch
```

This will:
- ✓ Check Python and PyTorch versions
- ✓ Verify GPU availability
- ✓ Test data loading
- ✓ Run 2 training batches
- ✓ Run 2 validation batches
- ✓ Verify the model can do forward/backward passes

**Time**: ~5-10 minutes

Check output:
```bash
tail -f logs/test_setup_*.out
```

## Option 2: Interactive Session

If you prefer to test interactively:

### Step 1: Request an interactive GPU node
```bash
salloc --partition=gpu --gres=gpu:1 --mem=32G --cpus-per-task=4 --time=01:00:00
```

### Step 2: Once on the GPU node, run the test
```bash
bash scripts/interactive_test.sh
```

## What Gets Tested?

1. **Environment check**: Python, PyTorch, CUDA versions
2. **GPU detection**: Can PyTorch see the GPU?
3. **Data loading**: Can it read from `data/indibench_h5/`?
4. **Model initialization**: Does the UNet build correctly?
5. **Forward pass**: Can it process data through the model?
6. **Backward pass**: Can it compute gradients?
7. **GPU memory**: Will it fit in GPU memory?

## Expected Output

You should see something like:

```
PyTorch: 2.9.1
CUDA available: True
GPU: NVIDIA A100-SXM4-40GB

Running fast_dev_run test...
Epoch 0:   0%|          | 0/2 [00:00<?, ?it/s]
Epoch 0:  50%|█████     | 1/2 [00:03<00:03,  3.45s/it]
Epoch 0: 100%|██████████| 2/2 [00:06<00:00,  3.21s/it]
...
Test complete!
```

## Troubleshooting

### GPU not available
```
CUDA available: False
```
**Fix**: Make sure you're on a GPU node and CUDA modules are loaded

### Out of memory
```
torch.cuda.OutOfMemoryError
```
**Fix**: Reduce batch size in config:
```bash
--data.batch_size=1
```

### Data not found
```
FileNotFoundError: data/indibench_h5/...
```
**Fix**: Check that data path is correct in config file

### Module import errors
```
ModuleNotFoundError: No module named 'india_benchmark'
```
**Fix**: Make sure you activated the virtual environment

## After Successful Test

Once the test passes, you're ready for full training:

```bash
sbatch scripts/train_unet.sbatch
```

The full training will take 12-24 hours depending on your GPU.

