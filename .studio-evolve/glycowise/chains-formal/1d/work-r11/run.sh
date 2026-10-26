#!/bin/bash
# 用法：run.sh <沙箱名或 state> <Di 文件或 cases-file> <out> [state 名]
W=/Users/liuyameng/Codes/clife-glycowise-plugins/.studio-evolve/glycowise
cd $W/chains-formal/1d/work-r11
if [ "$1" = state ]; then T=../state/plugins/glycowise; else T=sb/$1/plugins/glycowise; fi
python3 /Users/liuyameng/Codes/astra-studio-plugins/studio-evolve/scripts/runner_onto_engine.py run --engine-root /Users/liuyameng/Codes/onto-fundary-plugins \
  --target-dir $T --ontology glycowise --state ${4:-h_prime} --cases-dir $W/cases --cases-file $2 --repeat 1 --router manual \
  --recordings ../state/plugins/glycowise/cq/all_routes.json --family-override $W/sets/family-override.yaml --as-of 2026-10-25 --out $3 -v
