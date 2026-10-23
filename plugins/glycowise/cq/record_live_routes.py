"""用真 Qwen 给 golden.yaml 的 28 句口语录路由（record 端），并与人工转录 golden_routes.json 对账。

    python cq/record_live_routes.py --engine-root ../onto-fundary-plugins [--pin-ip 8.140.217.18]

--pin-ip：只在**本进程**内把 dashscope.aliyuncs.com 解析钉到给定 IP（socket.getaddrinfo 猴补丁），
用于绕开本机代理 fake-ip 误路由；不改系统 DNS / hosts / 代理配置。TLS 仍按主机名校验证书。

产出：cq/golden_routes.live.json（ReplayLLMClient 格式）与 cq/golden_routes.diff.md（逐句对账）。
"""
from __future__ import annotations

import argparse, importlib.util, json, socket, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent


def pin_dns(host: str, ip: str) -> None:
    real = socket.getaddrinfo

    def patched(h, *a, **kw):
        if h == host:
            return real(ip, *a, **kw)
        return real(h, *a, **kw)
    socket.getaddrinfo = patched


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine-root", required=True, type=Path)
    ap.add_argument("--llm-config", default=None, help="缺省 <engine-root>/llm.local.json")
    ap.add_argument("--pin-ip", default=None)
    ap.add_argument("--actor-role", default="医师")
    ap.add_argument("--repeat", type=int, default=1, help="每句录几次（看路由稳定性；写入 fixture 的是第 1 次）")
    ap.add_argument("--context-file", type=Path, default=None, help="会话上下文文本，作为 memory_text 喂给编译器（模拟会话里已知的患者/告警/内容 id）")
    ap.add_argument("--suffix", default="live", help="产出文件名后缀：golden_routes.<suffix>.json / .diff.md")
    a = ap.parse_args()
    if a.pin_ip:
        pin_dns("dashscope.aliyuncs.com", a.pin_ip)
    sys.path.insert(0, str(a.engine_root.resolve()))
    import yaml
    from clife_onto_engine.sdk import spi
    from clife_onto_engine.intent import IntentCompiler, OpenAICompatibleClient
    from clife_onto_engine.intent.llm import ReplayLLMClient

    td = HERE.parent
    spec = importlib.util.spec_from_file_location("onto_plugin_glycowise", td / "__init__.py", submodule_search_locations=[str(td)])
    mod = importlib.util.module_from_spec(spec); sys.modules["onto_plugin_glycowise"] = mod; spec.loader.exec_module(mod)

    client = OpenAICompatibleClient(config_path=a.llm_config or str(a.engine_root / "llm.local.json"))
    print(f"== 录制真 Qwen · model={client.model} · role={a.actor_role} · repeat={a.repeat} ==")

    class Rec:
        def __init__(self, inner): self.inner, self.rec, self.all = inner, {}, {}
        def complete_json(self, system, user):
            out = self.inner.complete_json(system, user)
            utt = ReplayLLMClient.utterance_of(user)
            self.rec.setdefault(utt, out); self.all.setdefault(utt, []).append(out)
            return out
    rec = Rec(client)
    compiler = IntentCompiler(rec, spi.registry)
    ctx_text = a.context_file.read_text(encoding="utf-8") if a.context_file else ""
    golden = yaml.safe_load((HERE / "golden.yaml").read_text(encoding="utf-8"))
    manual = json.loads((HERE / "golden_routes.json").read_text(encoding="utf-8"))

    lines = ["| # | 口语 | 期望 | 真 Qwen 路由 | 人工转录 | 一致 |", "|---|---|---|---|---|---|"]
    agree = 0
    for i, g in enumerate(golden, 1):
        q = g["q"]
        for vq in [v["q"] for v in (g.get("variants") or []) if v.get("q")]:  # variants 也录，供 runner 的 variant 行回放
            try:
                compiler.compile("glycowise", vq, actor_role=a.actor_role, memory_text=ctx_text)
            except Exception as e:
                print(f"  ✗ {i:02d} variant {vq[:30]} → {type(e).__name__}: {str(e)[:80]}")
            time.sleep(0.2)
        for _ in range(a.repeat):
            try:
                intent = compiler.compile("glycowise", q, actor_role=a.actor_role, memory_text=ctx_text)
            except Exception as e:
                print(f"  ✗ {i:02d} {q[:30]} → {type(e).__name__}: {str(e)[:80]}"); intent = None
                break
        raw = rec.rec.get(q, {})
        m = manual.get(q, {})
        live_desc = f"{raw.get('kind')}" + (f"({raw.get('action')})" if raw.get("kind") == "action" else "") + (f"·{intent.kind}" if intent and intent.kind != raw.get("kind") else "")
        man_desc = f"{m.get('kind')}" + (f"({m.get('action')})" if m.get("kind") == "action" else "")
        same = raw.get("kind") == m.get("kind") and raw.get("action") == m.get("action") and (raw.get("kind") != "query" or (raw.get("oql") or {}).get("start") == (m.get("oql") or {}).get("start"))
        agree += int(same)
        stab = ""
        if a.repeat > 1 and q in rec.all:
            keys = {(o.get("kind"), o.get("action"), (o.get("oql") or {}).get("start")) for o in rec.all[q]}
            stab = f" · {a.repeat} 次 {len(keys)} 种"
        lines.append(f"| {i:02d} | {q} | `{g['expect']}` | `{live_desc}`{stab} | `{man_desc}` | {'✓' if same else '✗'} |")
        print(f"  {'✓' if same else '△'} {i:02d} {live_desc:<32} ← {q[:28]}")
        time.sleep(0.2)
    (HERE / f"golden_routes.{a.suffix}.json").write_text(json.dumps(rec.rec, ensure_ascii=False, indent=1), encoding="utf-8")
    hdr = [f"# 真 Qwen 路由 vs 人工转录对账（model={client.model}，role={a.actor_role}，上下文={'有' if ctx_text else '无'}，{time.strftime('%Y-%m-%d')}）", "",
           f"kind/action/查询起点一致：{agree}/{len(golden)}。一致只看路由骨架，params 差异见 golden_routes.live.json。", ""]
    (HERE / f"golden_routes.{a.suffix}.diff.md").write_text("\n".join(hdr + lines) + "\n", encoding="utf-8")
    print(f"✓ {len(rec.rec)} 条录制 → golden_routes.{a.suffix}.json · 骨架一致 {agree}/{len(golden)} · 对账 → golden_routes.{a.suffix}.diff.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
