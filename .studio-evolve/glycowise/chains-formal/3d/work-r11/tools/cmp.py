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
