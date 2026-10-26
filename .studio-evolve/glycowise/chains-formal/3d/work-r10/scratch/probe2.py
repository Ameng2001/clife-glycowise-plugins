import sys, json
sys.path.insert(0, "/Users/liuyameng/Codes/astra-studio-plugins/studio-evolve/scripts")
import runner_onto_engine as R
from pathlib import Path
R.freeze_date("2026-10-25")
spi = R.load_engine(Path("/Users/liuyameng/Codes/onto-fundary-plugins"))
plugin = R.load_plugin(Path(sys.argv[1]))
from clife_onto_engine.query import InMemoryStore
from clife_onto_engine.kernel import ActionEngine
from clife_onto_engine.sdk.context import Actor
store = InMemoryStore(); plugin.seed_reference_data(store)
eng = ActionEngine(spi.registry, store=store)
actor = Actor(id="u-doctor-01", role="医师")
for line in open(sys.argv[2], encoding="utf-8"):
    if not line.strip() or line.startswith("#"): continue
    action, params = line.split("\t", 1)
    pv = eng.validate("glycowise", action, json.loads(params), actor)
    print(("COMMIT" if pv.would_commit else "REJECT"), [v.rule for v in pv.violations], "|", action, params.strip()[:90])
