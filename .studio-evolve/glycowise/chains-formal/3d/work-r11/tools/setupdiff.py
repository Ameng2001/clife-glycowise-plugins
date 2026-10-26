import json,sys,yaml,glob,os
W='/Users/liuyameng/Codes/clife-glycowise-plugins/.studio-evolve/glycowise'
cases={}
for f in glob.glob(W+'/cases/**/*.yaml',recursive=True):
    c=yaml.safe_load(open(f))
    if isinstance(c,dict) and 'id' in c: cases[c['id']]=c
fb={}
for w in ('2026-W54','2026-W54b'):
    for it in yaml.safe_load(open(f'{W}/examples/trajectories/{w}/feedback.yaml'))['items']: fb[it['trace_id']]=it
def div(p):
    d={}
    for l in open(p):
        r=json.loads(l)
        if r['variant'] is None:
            d[r['case']]={f.split(':')[1] for f in r['flags'] if f.startswith('SETUP_DIVERGED')}
    return d
a,b=div(sys.argv[1]),div(sys.argv[2])
tr={}
for c in b:
    for i in b[c]-a.get(c,set()):
        st=cases[c]['setup'][int(i)]; t=st.get('trace_id')
        tr.setdefault(t,(st['action'],json.dumps(st.get('params'),ensure_ascii=False)[:90],set()))[2].add(c)
    for i in a.get(c,set())-b[c]:
        st=cases[c]['setup'][int(i)]; t=st.get('trace_id')
        tr.setdefault('(不再分叉)'+str(t),(st['action'],'',set()))[2].add(c)
print(f"  setup 新分叉的窗口步骤 {len(tr)} 个")
for t,(act,pp,cs) in sorted(tr.items()):
    it=fb.get(t,{})
    print(f"    {t} {act} 标注={it.get('label','(非W54)')} 窗口={it.get('engine_actual','')} 波及{len(cs)}案例 {pp}")
