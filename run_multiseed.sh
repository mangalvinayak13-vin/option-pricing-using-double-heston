#!/bin/bash
# Five seeds per model. Answers whether the 0.796 vs 0.801 gap is signal or noise.
set -u
cd "$(dirname "$0")"
for seed in 0 1 2 3 4; do
  for model in 1 2; do
    out="outputs/seeds/seed_${seed}"
    mkdir -p "$out"
    echo "=== model $model seed $seed ==="
    python3 run_latent_training.py --model "$model" --epochs 300 --batch-size 128 \
      --seed "$seed" --output-dir "$out" 2>&1 | grep -E "mean skill|restored best"
  done
done
echo "ALL SEEDS DONE"
