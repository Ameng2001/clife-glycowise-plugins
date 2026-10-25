import json,sys
def load(f):
    out={}
    for l in open(f):
        d=json.loads(l); out[(d['case'],d['variant'])]=(d['pass'],d['actual'],d['expect'])
    return out
a=load(sys.argv[1]); b=load(sys.argv[2])
for k in sorted(set(a)|set(b), key=str):
    if k in a and k in b and (a[k][0]!=b[k][0] or a[k][1]!=b[k][1]):
        print(k, a[k][0],'->',b[k][0],'|',a[k][1],'=>',b[k][1],'| expect',a[k][2])
print('compared',len(set(a)&set(b)))
