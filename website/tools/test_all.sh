#!/bin/sh
# Run the interaction test for every theme (server must be running on :8765); prints only failures.
cd "$(dirname "$0")/../.." || exit 1
for t in springboard glass ferro amber instrument trading; do
  node website/tools/interact.mjs "$t" 2>&1 | grep -v "^PASS" | sed "s/^/$t: /"
done
echo "interaction tests finished"
