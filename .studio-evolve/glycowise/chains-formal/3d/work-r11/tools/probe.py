import sys, json
sys.path.insert(0, "/Users/liuyameng/Codes/astra-studio-plugins/studio-evolve/scripts")
import runner_onto_engine as R
R.freeze_date("2026-10-25")
from pathlib import Path
spi = R.load_engine(Path("/Users/liuyameng/Codes/onto-fundary-plugins"))
plugin = R.load_plugin(Path(sys.argv[1]))
from clife_onto_engine.kernel import ActionEngine
from clife_onto_engine.query import InMemoryStore
from clife_onto_engine.sdk.context import Actor
store = InMemoryStore(); plugin.seed_reference_data(store)
eng = ActionEngine(spi.registry, store=store)
actor = Actor("probe", "医师")
for line in open(sys.argv[2]):
    line=line.strip()
    if not line or line.startswith("#"): continue
    act, params = json.loads(line)
    p = eng.validate("glycowise", act, params, actor)
    print(("commit " if p.would_commit else "REJECT ") + str([v.rule.split('_')[0] for v in p.violations]) + "  " + json.dumps(params, ensure_ascii=False)[:110])
