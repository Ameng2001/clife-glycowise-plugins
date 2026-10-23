#!/usr/bin/env python3
"""网关样例：把口语真的喂给 clife-onto-engine（真 Qwen 路由 → Session.ask → ActionEngine.execute / OQL），
审计落 SqliteAuditStore，再从 sqlite 导出成管线要的 audit.jsonl（补 trace_id / ts / utterance / cost 四个键）。

    # 1) 跑一个窗口（真 LLM 路由；--pin-ip 只在本进程钉 DNS，绕本机代理 fake-ip）
    python3 record_window.py run --engine-root ../../../../onto-fundary-plugins --plugin ../../../plugins/glycowise \
        --utterances utterances.2026-W43.yaml --context-file ../../../plugins/glycowise/cq/session_context.txt \
        --audit-db engine-audit/audit.db --pin-ip 8.140.217.18
    # 2) 从 sqlite 导出窗口 JSONL（这一步就是「网关补四个键」）
    python3 record_window.py export --audit-db engine-audit/audit.db --window 2026-W43 --out trajectories/2026-W43/audit.jsonl

真实性约束（与 README「硬判据」一致）：
  * execute 行 = 引擎 AuditSnapshot.to_dict() 原样 + 四个键，一个字段都不手改；参数是 LLM 路由出来、引擎 guard 过的，越界会被引擎拒在 guard 前。
  * ask 行引擎不审计（只读），由网关记：编译出的 OQL 原文 + 行数。
  * 路由成 clarify / advise / reject 的口语不是轨迹，只进 routing.log.jsonl 备查。
  * 反馈标签不在这里产生——那是业务侧的事。
"""
from __future__ import annotations

import argparse, datetime as dt, importlib.util, json, socket, sqlite3, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
TZ = dt.timezone(dt.timedelta(hours=8))


def pin_dns(host: str, ip: str) -> None:
    real = socket.getaddrinfo

    def patched(h, *a, **kw):
        return real(ip if h == host else h, *a, **kw)
    socket.getaddrinfo = patched


class UsageClient:
    """与引擎 OpenAICompatibleClient 同参，多记一份 usage（token 数进 cost）。"""

    def __init__(self, config_path: str, temperature: float = 0.0):
        from clife_onto_engine.intent.llm import _load_config
        cfg = _load_config(config_path)
        from openai import OpenAI
        self._c = OpenAI(base_url=cfg["base_url"], api_key=cfg["api_key"])
        self.model, self.temperature, self.last_usage = cfg["model"], temperature, None

    def complete_json(self, system: str, user: str) -> dict:
        resp = self._c.chat.completions.create(
            model=self.model, messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            response_format={"type": "json_object"}, temperature=self.temperature, extra_body={"enable_thinking": False})
        u = getattr(resp, "usage", None)
        self.last_usage = (int(u.prompt_tokens or 0) + int(u.completion_tokens or 0)) if u else None
        return json.loads(resp.choices[0].message.content or "{}")


def load_plugin(target_dir: Path):
    target_dir = target_dir.resolve()
    spec = importlib.util.spec_from_file_location(f"onto_plugin_{target_dir.name}", target_dir / "__init__.py",
                                                  submodule_search_locations=[str(target_dir)])
    mod = importlib.util.module_from_spec(spec); sys.modules[spec.name] = mod; spec.loader.exec_module(mod)
    return mod


def ensure_gateway_table(db: sqlite3.Connection) -> None:
    # 网关侧补的四个键，与引擎 audit 表按 rowid 对齐；ask 行引擎不审计，整行由网关存在这里（audit_rowid 为空）
    db.execute("CREATE TABLE IF NOT EXISTS gateway_trace (trace_id TEXT PRIMARY KEY, window TEXT, ts TEXT, kind TEXT, "
               "utterance TEXT, actor TEXT, audit_rowid INTEGER, ask_doc TEXT, cost TEXT, reply_kind TEXT)")


def iso_week(d: dt.date) -> str:
    y, w, _ = d.isocalendar()
    return f"{y}-W{w:02d}"


def cmd_run(a) -> None:
    sys.path.insert(0, str(a.engine_root.resolve()))
    if a.pin_ip:
        pin_dns("dashscope.aliyuncs.com", a.pin_ip)
    import yaml
    from clife_onto_engine.sdk import spi
    from clife_onto_engine.sdk.context import Actor
    from clife_onto_engine.intent.compiler import IntentCompiler
    from clife_onto_engine.kernel import ActionEngine
    from clife_onto_engine.query import InMemoryStore
    from clife_onto_engine.session import Session
    from clife_onto_engine.trust.sqlite_store import SqliteAuditStore, SqliteCommitJournal

    plugin = load_plugin(a.plugin)
    manifest = yaml.safe_load((a.plugin / "plugin.yaml").read_text(encoding="utf-8"))
    ontology = manifest["ontology"]; schema_version = f"{ontology}@{manifest.get('version', '?')}"
    store = InMemoryStore()
    plugin.seed_reference_data(store)
    a.audit_db.parent.mkdir(parents=True, exist_ok=True)
    audit = SqliteAuditStore(str(a.audit_db)); journal = SqliteCommitJournal(str(a.audit_db))
    engine = ActionEngine(spi.registry, store=store, audit=audit, journal=journal)
    client = UsageClient(a.llm_config or str(a.engine_root / "llm.local.json"))
    compiler = IntentCompiler(client, spi.registry)
    gw = sqlite3.connect(str(a.audit_db), isolation_level=None); ensure_gateway_table(gw)
    ctx_text = a.context_file.read_text(encoding="utf-8") if a.context_file else ""

    items = yaml.safe_load(a.utterances.read_text(encoding="utf-8"))["items"]
    sessions: dict[tuple, Session] = {}
    log = (a.utterances.parent / f"routing.log.{a.utterances.stem.split('.')[-1]}.jsonl").open("a", encoding="utf-8")
    print(f"== 真引擎 · 真 Qwen({client.model}) · 本体 {ontology} · schema {schema_version} · 审计库 {a.audit_db} ==")
    n_exec = n_ask = n_other = 0
    for i, it in enumerate(items, 1):
        actor = Actor(it.get("actor", {}).get("id", "u-doctor-01"), it.get("actor", {}).get("role", "医师"))
        key = (actor.id, actor.role)
        if key not in sessions:
            sessions[key] = Session(ontology_id=ontology, registry=spi.registry, store=store, compiler=compiler, actor=actor,
                                    engine=engine, schema_version=schema_version, session_id=f"gw-{actor.id}")
        sess = sessions[key]
        now = dt.datetime.now(TZ); ts = now.isoformat(timespec="seconds")
        trace_id = f"t-{now:%Y%m%d}-{a.seq_base + i:04d}"
        before = gw.execute("SELECT COALESCE(MAX(rowid),0) FROM audit").fetchone()[0]
        t0 = time.perf_counter()
        # 记忆接地由 Session 自己做；会话上下文（对象 id 对号表）从 CRITICAL 层注入一次
        if ctx_text and not getattr(sess, "_ctx_loaded", False):
            from clife_onto_engine.memory import Layer, MemoryItem
            sess.memory.add(MemoryItem(id=f"{sess.session_id}:ctx", ontology_id=ontology, session_id=sess.session_id,
                                       layer=Layer.CRITICAL, content=ctx_text, tags=("context",), source="gateway"))
            sess._ctx_loaded = True
        try:
            reply = sess.ask(it["utterance"], ts=ts)
            err = None
        except Exception as e:  # 引擎抛错（如 handler 未实现）也要留痕
            reply, err = None, f"{type(e).__name__}: {str(e)[:160]}"
        wall = round(time.perf_counter() - t0, 3)
        tokens = client.last_usage
        after = gw.execute("SELECT COALESCE(MAX(rowid),0) FROM audit").fetchone()[0]
        kind = reply.kind if reply else "error"
        row = {"trace_id": trace_id, "ts": ts, "utterance": it["utterance"], "actor": {"id": actor.id, "role": actor.role},
               "reply": kind, "tokens": tokens, "wall_s": wall, "error": err}
        if reply is not None and kind in ("committed", "pending_hil", "rejected") and after > before:
            n_exec += 1
            rules = [v.rule for v in (reply.violations or ())]
            cost = {"steps": 2 + len(rules), "tokens": tokens, "wall_s": wall}
            gw.execute("INSERT OR REPLACE INTO gateway_trace VALUES (?,?,?,?,?,?,?,?,?,?)",
                       (trace_id, iso_week(now.date()), ts, "execute", it["utterance"], json.dumps(row["actor"], ensure_ascii=False), after, None,
                        json.dumps(cost), kind))
            row["audit_rowid"] = after; row["violations"] = rules
        elif reply is not None and kind == "query":
            n_ask += 1
            cost = {"steps": 2 + int((reply.cost or {}).get("total", 0)), "tokens": tokens, "wall_s": wall}
            ask_doc = {"ontology_id": ontology, "kind": "ask", "utterance": it["utterance"], "actor": row["actor"],
                       "oql": compiler_raw_oql(reply), "decision": "answered", "rows": len(reply.rows or []),
                       "confidence": reply.confidence, "cost": cost, "schema_version": schema_version}
            gw.execute("INSERT OR REPLACE INTO gateway_trace VALUES (?,?,?,?,?,?,?,?,?,?)",
                       (trace_id, iso_week(now.date()), ts, "ask", it["utterance"], json.dumps(row["actor"], ensure_ascii=False), None,
                        json.dumps(ask_doc, ensure_ascii=False), json.dumps(cost), kind))
            row["rows"] = len(reply.rows or [])
        else:
            n_other += 1
            row["detail"] = (reply.question or reply.answer or reply.error) if reply else err
        log.write(json.dumps(row, ensure_ascii=False) + "\n"); log.flush()
        mark = {"committed": "✓", "pending_hil": "⏸", "rejected": "⛔", "query": "?"}.get(kind, "·")
        print(f"  {mark} {trace_id} {kind:<11} {it['utterance'][:44]}" + (f"  {row.get('violations')}" if row.get("violations") else "")
              + (f"  rows={row.get('rows')}" if "rows" in row else "") + (f"  [{row.get('detail')}]"[:90] if row.get("detail") else ""))
        time.sleep(a.sleep)
    print(f"完成：execute {n_exec} · ask {n_ask} · 非轨迹（clarify/advise/reject/error）{n_other} · 共 {len(items)}")


def compiler_raw_oql(reply) -> dict:
    """把已校验的 OQLQuery 还原成 JSON（引擎 oql 对象 → 管线要的 dict）。"""
    q = reply.oql

    def node(n):
        if hasattr(n, "items") and not hasattr(n, "field"):
            key = "or" if type(n).__name__ == "Or" else "and"
            return {key: [node(x) for x in n.items]}
        return {"field": n.field, "op": n.op, "value": n.value}
    d = {"start": q.start, "where": [node(x) for x in q.where], "select": list(q.select)}
    if q.steps:
        d["steps"] = [{"link_type": s.link_type, "direction": s.direction, "where": [node(x) for x in s.where]} for s in q.steps]
    if q.aggregate:
        d["aggregate"] = {"func": q.aggregate.func, "field": q.aggregate.field}
    if q.order_by:
        d["order_by"] = [{"field": o.field, "desc": o.desc} for o in q.order_by]
    if q.limit != 100:
        d["limit"] = q.limit
    return d


def cmd_export(a) -> None:
    gw = sqlite3.connect(str(a.audit_db)); ensure_gateway_table(gw)
    rows = gw.execute("SELECT trace_id, ts, kind, utterance, actor, audit_rowid, ask_doc, cost FROM gateway_trace WHERE window=? ORDER BY ts, trace_id",
                      (a.window,)).fetchall()
    a.out.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with a.out.open("w", encoding="utf-8") as fo:
        for trace_id, ts, kind, utt, actor, audit_rowid, ask_doc, cost in rows:
            if kind == "execute":
                doc = json.loads(gw.execute("SELECT doc FROM audit WHERE rowid=?", (audit_rowid,)).fetchone()[0])  # 引擎原样
                line = {"trace_id": trace_id, "ts": ts, **{k: v for k, v in doc.items() if k != "ts"}, "kind": "execute", "utterance": utt, "cost": json.loads(cost)}
                # 字段顺序只为可读：trace_id, ts, ontology_id, kind, utterance, action, actor, inputs_snapshot, rules_evaluated, decision, confidence, evidence, cost, schema_version
                order = ["trace_id", "ts", "ontology_id", "kind", "utterance", "action", "actor", "inputs_snapshot", "rules_evaluated", "decision", "confidence", "evidence", "cost", "schema_version"]
                line = {k: line[k] for k in order if k in line} | {k: v for k, v in line.items() if k not in order}
            else:
                d = json.loads(ask_doc)
                line = {"trace_id": trace_id, "ts": ts, **d}
            fo.write(json.dumps(line, ensure_ascii=False) + "\n"); n += 1
    print(f"✓ 窗口 {a.window}：导出 {n} 条（execute 原样取自 audit 表，ask 取自网关表）→ {a.out}")


def main() -> None:
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--engine-root", required=True, type=Path); r.add_argument("--plugin", required=True, type=Path)
    r.add_argument("--utterances", required=True, type=Path); r.add_argument("--context-file", type=Path)
    r.add_argument("--audit-db", required=True, type=Path); r.add_argument("--llm-config"); r.add_argument("--pin-ip")
    r.add_argument("--seq-base", type=int, default=0); r.add_argument("--sleep", type=float, default=0.3)
    r.set_defaults(fn=cmd_run)
    e = sub.add_parser("export")
    e.add_argument("--audit-db", required=True, type=Path); e.add_argument("--window", required=True); e.add_argument("--out", required=True, type=Path)
    e.set_defaults(fn=cmd_export)
    a = ap.parse_args(); a.fn(a)


if __name__ == "__main__":
    main()
