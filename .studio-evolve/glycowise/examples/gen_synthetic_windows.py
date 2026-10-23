#!/usr/bin/env python3
"""按正式 run 的数量门槛生成**合成**窗口，只用来验证接法与分层抽样是否跑得通；不是真实数据，不得混进 cases/real/。

用法：python3 gen_synthetic_windows.py [--target 200|900] [--seed 0] [--out synthetic]
  --target 200 → 正式 run 门槛（≥200 条有反馈轨迹，tier × time_half 8 个分层各 ≥16）
  --target 900 → 全程（15 轮 × 3 seed ≥ 900 条）
产物：synthetic/trajectories/{window}/audit.jsonl + feedback.yaml，每个 feedback.yaml 顶层 synthetic: true，reviewer=u-synthetic-00。
做法：以 trajectories/2026-W44 的 20 条真样例为模板，换患者（称呼与 id 一起换）、换对象 id 后缀、换时间戳；按 tier 轮转选模板，
      保证 4 个 tier 均衡，time_half 由窗口日期自然分前后半。标签与 truth 随模板同步替换。
"""
import argparse, copy, datetime as dt, json, os, random, re
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
PATIENTS = {"P0012": "刘阿姨", "P0031": "王叔", "P0007": "周先生", "P0023": "陈阿姨", "P0088": "李女士", "P0045": "黄伯", "P0066": "张阿姨"}
SYN_PATIENTS = {f"P1{i:03d}": n for i, n in enumerate(
    ["赵阿姨", "钱叔", "孙先生", "李阿姨", "周叔", "吴女士", "郑伯", "王阿姨", "冯先生", "陈叔", "褚女士", "卫伯", "蒋阿姨", "沈先生", "韩叔", "杨女士"], 1)}
WINDOW_SIZE = 20


def iso_week(d):
    y, w, _ = d.isocalendar()
    return f"{y}-W{w:02d}"


def tier_of(t, fb):
    if fb["label"] == "wrong":
        return 3
    if t["kind"] == "ask":
        return 2 if t["oql"].get("traverse") else 1
    if t["decision"] == "pending_hil":
        return 4
    return 3


def retarget(obj, pid_from, pid_to, name_from, name_to, suffix):
    """深拷贝后做一致替换：患者 id、称呼、对象 id 后缀。"""
    s = json.dumps(obj, ensure_ascii=False)
    s = s.replace(pid_from, pid_to)
    if name_from:
        s = s.replace(name_from, name_to)
    # 对象 id（r-/s-/d-/A-/plan-/sym-/ref-/th-/lab-/cce-/b-/c-promo-/pkg-）加后缀，避免跨窗口撞 id
    s = re.sub(r"\b((?:r|s|d|A|plan|sym|ref|th|lab|cce|b|hint|thlog)-[A-Za-z0-9\-]+?)(?=[\"\s,:）)])", lambda m: f"{m.group(1)}-{suffix}", s)
    return json.loads(s)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", type=int, default=200)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--template", default=os.path.join(HERE, "trajectories", "2026-W44"))
    ap.add_argument("--out", default=os.path.join(HERE, "synthetic"))
    ap.add_argument("--start", default="2026-11-02", help="第一个合成窗口的周一")
    a = ap.parse_args()
    rnd = random.Random(a.seed)

    traj = [json.loads(l) for l in open(os.path.join(a.template, "audit.jsonl"), encoding="utf-8") if l.strip()]
    fb = {i["trace_id"]: i for i in yaml.safe_load(open(os.path.join(a.template, "feedback.yaml"), encoding="utf-8"))["items"]}
    by_tier = {1: [], 2: [], 3: [], 4: []}
    for t in traj:
        f = fb[t["trace_id"]]
        by_tier[tier_of(t, f)].append((t, f))

    start = dt.date.fromisoformat(a.start)
    n_windows = -(-a.target // WINDOW_SIZE)
    total, strata = 0, {}
    tiers_cycle = [1, 2, 3, 4]
    for w in range(n_windows):
        monday = start + dt.timedelta(weeks=w)
        window = iso_week(monday)
        wdir = os.path.join(a.out, "trajectories", window)
        os.makedirs(wdir, exist_ok=True)
        rows, items = [], []
        for k in range(WINDOW_SIZE):
            tier = tiers_cycle[(w * WINDOW_SIZE + k) % 4]
            t, f = rnd.choice(by_tier[tier])
            pid_from = next((p for p in PATIENTS if p in json.dumps(t, ensure_ascii=False)), None)
            pid_to, name_to = rnd.choice(list(SYN_PATIENTS.items()))
            suffix = f"w{w:02d}k{k:02d}"
            t2 = retarget(t, pid_from or "P0000", pid_to, PATIENTS.get(pid_from), name_to, suffix) if pid_from else copy.deepcopy(t)
            f2 = retarget(f, pid_from or "P0000", pid_to, PATIENTS.get(pid_from), name_to, suffix) if pid_from else copy.deepcopy(f)
            day = monday + dt.timedelta(days=rnd.randrange(7))
            ts = dt.datetime.combine(day, dt.time(rnd.randrange(0, 24), rnd.randrange(0, 60), rnd.randrange(0, 60)))
            tid = f"t-{day:%Y%m%d}-{k + 1:04d}"
            t2["trace_id"], t2["ts"] = tid, ts.isoformat() + "+08:00"
            t2["synthetic"] = True
            f2["trace_id"] = tid
            f2.pop("reviewer", None)
            rows.append(t2); items.append(f2)
            total += 1
            strata.setdefault((tier, "H1" if w < n_windows / 2 else "H2"), 0)
            strata[(tier, "H1" if w < n_windows / 2 else "H2")] += 1
        rows.sort(key=lambda r: r["ts"])
        with open(os.path.join(wdir, "audit.jsonl"), "w", encoding="utf-8") as fo:
            for r in rows:
                fo.write(json.dumps(r, ensure_ascii=False) + "\n")
        with open(os.path.join(wdir, "feedback.yaml"), "w", encoding="utf-8") as fo:
            fo.write("# 合成数据：只用于验证接法 / 分层抽样，不得混入 cases/real/\n")
            yaml.safe_dump({"window": window, "synthetic": True, "template": "2026-W44", "seed": a.seed,
                            "reviewer": {"id": "u-synthetic-00", "role": "合成"}, "labeled_at": str(monday + dt.timedelta(days=7)),
                            "items": sorted(items, key=lambda i: i["trace_id"])}, fo, allow_unicode=True, sort_keys=False, width=200)
    print(f"合成 {n_windows} 个窗口，共 {total} 条有反馈轨迹 → {a.out}")
    print("tier × time_half（按窗口前后半）：")
    for tier in (1, 2, 3, 4):
        print(f"  tier {tier}: H1 {strata.get((tier, 'H1'), 0):>3}  H2 {strata.get((tier, 'H2'), 0):>3}")
    thin = [k for k, v in strata.items() if v < 16]
    print("每层 ≥16：", "满足" if not thin else f"不满足 {thin}")


if __name__ == "__main__":
    main()
