#!/bin/bash
# usage: sb.sh new NAME   |  sb.sh check NAME DI_FILE
set -e
W=/Users/liuyameng/Codes/clife-glycowise-plugins/.studio-evolve/glycowise
C=$W/chains-formal/3d
STATE=$C/state
WK=$C/work-r11
OUT=$C/attribution/round-11
R=/Users/liuyameng/Codes/astra-studio-plugins/studio-evolve/scripts/runner_onto_engine.py
cmd=$1; name=$2
SB=$WK/sb/$name
if [ "$cmd" = new ]; then
  rm -rf $SB; mkdir -p $SB/plugins
  rsync -a --exclude __pycache__ $STATE/plugins/glycowise $SB/plugins/
  echo "sandbox $SB"; exit 0
fi

if [ "$cmd" = check ]; then
  di=$3
  P=$OUT/$name.patch; : > $P
  for f in _fde.py __init__.py; do
    diff -u --label a/plugins/glycowise/$f --label b/plugins/glycowise/$f $STATE/plugins/glycowise/$f $SB/plugins/glycowise/$f >> $P || true
  done
  echo "patch lines: $(wc -l < $P)  (+$(grep -c '^+[^+]' $P) -$(grep -c '^-[^-]' $P))"
  patch -p1 --dry-run -d $STATE < $P | sed 's/^/  dry-run: /'
  python3 -m py_compile $SB/plugins/glycowise/_fde.py $SB/plugins/glycowise/__init__.py && echo "  py_compile OK"
  find $SB -name __pycache__ -prune -exec rm -rf {} \; 2>/dev/null || true
  cd $WK
  python3 $R run --engine-root /Users/liuyameng/Codes/onto-fundary-plugins --target-dir $SB/plugins/glycowise --ontology glycowise --state h_prime --cases-dir $W/cases --cases-file $di --repeat 1 --router manual --recordings $STATE/plugins/glycowise/cq/all_routes.json --family-override $W/sets/family-override.yaml --as-of 2026-10-25 --out $WK/di-$name.jsonl -v 2>&1 | grep -v "^family"
  python3 -c "import json,sys;rs=[json.loads(l) for l in open('$WK/di-$name.jsonl')];print('  Dᵢ 全部行（含变体）pass', sum(1 for r in rs if r['pass']==1),'/',len(rs))"
  python3 $R run --engine-root /Users/liuyameng/Codes/onto-fundary-plugins --target-dir $SB/plugins/glycowise --ontology glycowise --state h_prime --cases-dir $W/cases --repeat 1 --router manual --recordings $STATE/plugins/glycowise/cq/all_routes.json --family-override $W/sets/family-override.yaml --as-of 2026-10-25 --out $WK/all-$name.jsonl 2>&1 | grep "原题"
  find $SB -name __pycache__ -prune -exec rm -rf {} \; 2>/dev/null || true
  python3 - $WK/base-all-h11.jsonl $WK/all-$name.jsonl <<'PY'
import json,sys
def load(p):
    d={}
    for l in open(p):
        r=json.loads(l)
        d[(r['case'],r['variant'])]=r
    return d
a,b=load(sys.argv[1]),load(sys.argv[2])
cases=sorted({k[0] for k in a})
gain,loss,vg,vl=[],[],[],[]
for k in sorted(a, key=lambda k:(k[0],str(k[1]))):
    pa,pb=a[k]['pass'],b.get(k,{}).get('pass')
    if pa==pb: continue
    (gain if k[1] is None else vg).append(k) if (pb==1) else (loss if k[1] is None else vl).append(k)
print(f"  vs h11 全案例：原题 +{len(gain)} -{len(loss)}；变体 +{len(vg)} -{len(vl)}")
for k in gain: print("    + ",k[0])
for k in loss: print("    - ",k[0],'|',b[k]['expect'],'|',b[k]['actual'],b[k]['flags'][-1:] )
for k in vl: print("    -v",k,'|',b[k]['actual'])
PY

python3 /private/tmp/claude-501/-Users-liuyameng-Codes-floppy/ee9bfa6a-aea1-4b64-afc6-29f9f9b14f54/scratchpad/setupdiff.py $WK/base-all-h11.jsonl $WK/all-$name.jsonl
fi
