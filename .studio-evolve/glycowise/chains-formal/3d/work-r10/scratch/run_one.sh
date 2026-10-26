#!/bin/zsh
# run_one.sh <提案名> <Di|fallout>
W=/Users/liuyameng/Codes/clife-glycowise-plugins/.studio-evolve/glycowise
WK=$W/chains-formal/3d/work-r10
n=$1; kind=$2; g=${n%%[ab]*}
if [[ $kind == Di ]]; then CF=$W/chains-formal/3d/attribution/round-10/$g-Di.yaml; OUT=$WK/Di-$n.jsonl; else CF=$WK/scratch/fallout-ids.yaml; OUT=$WK/fallout-$n.jsonl; fi
python3 /Users/liuyameng/Codes/astra-studio-plugins/studio-evolve/scripts/runner_onto_engine.py run --engine-root /Users/liuyameng/Codes/onto-fundary-plugins --target-dir $WK/sb/$n/plugins/glycowise --ontology glycowise --state h_prime --cases-dir $W/cases --cases-file $CF --family-override $W/sets/family-override.yaml --router manual --recordings $WK/sb/$n/plugins/glycowise/cq/all_routes.json --as-of 2026-10-25 --repeat 1 --out $OUT > $WK/scratch/log-$kind-$n.txt 2>&1
find $WK/sb/$n -name __pycache__ -type d -prune -exec rm -rf {} +
