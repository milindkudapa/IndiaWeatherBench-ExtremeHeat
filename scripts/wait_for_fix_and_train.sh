#!/bin/bash
# Monitor NaN fix completion and provide training launch command

echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                              ║"
echo "║            MONITORING NaN FIX - WAITING FOR COMPLETION                      ║"
echo "║                                                                              ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""

LOG_FILE="/burg-archive/home/mck2199/ML-Project/logs/fix_nan.log"

echo "Monitoring: $LOG_FILE"
echo "Press Ctrl+C to stop monitoring"
echo ""

# Wait for process to complete
while ps aux | grep -v grep | grep "fix_era5land_nan.py" > /dev/null; do
    # Show latest progress
    tail -3 "$LOG_FILE" 2>/dev/null | grep "Processing:" | tail -1
    sleep 10
done

echo ""
echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                              ║"
echo "║                    ✅ NaN FIX COMPLETED! ✅                                   ║"
echo "║                                                                              ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""

# Show final summary
echo "Final Summary:"
tail -20 "$LOG_FILE" | grep -A 10 "SUMMARY"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 READY TO TRAIN!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Verify data is clean:"
echo "  python scripts/check_era5land_data_quality.py"
echo ""
echo "Launch training:"
echo "  cd /burg-archive/home/mck2199/ML-Project"
echo "  sbatch scripts/train_unet_era5land_2gpu.sbatch"
echo ""
echo "Monitor training:"
echo "  # After sbatch returns job ID (e.g., 5059999)"
echo "  tail -f logs/train_unet_era5land_5059999.out"
echo ""
echo "WandB:"
echo "  https://wandb.ai/YOUR_USERNAME/india_benchmark_era5land"
echo ""

