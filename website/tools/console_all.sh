#!/bin/sh
# Render every page in every theme and print console messages or failed renders (server on :8765).
cd "$(dirname "$0")/../.." || exit 1
for t in springboard glass ferro amber instrument trading; do
  python3 website/tools/check.py "index.html?theme=$t" "market.html?theme=$t" "model.html?theme=$t" "how-it-works.html?theme=$t" \
    "finding.html?theme=$t" "results.html?theme=$t" "about.html?theme=$t" "team.html?theme=$t" "references.html?theme=$t" | grep -v "ready=True  charts"
done
echo "console sweep finished"
