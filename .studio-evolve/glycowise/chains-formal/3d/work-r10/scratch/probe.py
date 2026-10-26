import sys
sys.path.insert(0, "/Users/liuyameng/Codes/astra-studio-plugins/studio-evolve/scripts")
import runner_onto_engine as R
from pathlib import Path
R.freeze_date("2026-10-25")
spi = R.load_engine(Path("/Users/liuyameng/Codes/onto-fundary-plugins"))
plugin = R.load_plugin(Path(sys.argv[1]))
from clife_onto_engine.query import InMemoryStore
store = InMemoryStore(); plugin.seed_reference_data(store)
def rows(t): return [dict(v, _key=k) for k, v in store.iter_objects(t)]
exec(sys.argv[2])
