#!/usr/bin/env python3
"""
score_matrix.py v3 —— 三维评分聚合（trigger / compliance / boundary）。

输入：
  - --batch-dirs 直接给 batch_run_eval/runs/.../batch_<ts>_<task>_full 路径列表
  - 或 --auto-discover 在 batch_run_eval/runs/SF*/ 下扫所有 _full 目录
  （已不再支持 --modes noskill；v3 只评 with-skill 模式）

每个 task 自动决定 task_kind / target_skill / 用哪个 rubric：
  - SF01_t1 / SF01_t2  → kind=positive, target='fix',                  rubric=skill_01/rubric.yaml
  - SF01_t3_negative   → kind=negative, target='fix',                  rubric=skill_01/rubric_negative.yaml
  - SF02_t1 / SF02_t2  → kind=positive, target='systematic-debugging', rubric=skill_02/rubric.yaml
  - SF02_t3_negative   → kind=negative, target='systematic-debugging', rubric=skill_02/rubric_negative.yaml

target_skill 优先从 config.json 的 skill.name 自动读取（单一真相来源），
仅在 config.json 不存在时 fallback 到硬编码映射表。

输出：
  matrix_score.csv / matrix_score.json
"""
from __future__ import annotations
import argparse
import csv
import json
import os
import re as _re_module
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from score_trace import score, make_judge_caller  # type: ignore
from _postprocess_jobs import process_job_dir  # type: ignore


# ── config.json 自动读取：单一真相来源 ──
# 评测 config 路径：evaluation/tasks/<PREFIX>/configs/<task_id>.config.json
# config 中 skill.name 字段即为 run_task.sh 创建容器目录时使用的 skill 名称，
# 与 trace 中 system_init.skills 列表保持一致。

_EVAL_TASKS_ROOT: Path | None = None  # 延迟初始化
_config_cache: dict[str, dict] = {}   # task_id -> config dict


def _set_eval_tasks_root(mvp_root: Path) -> None:
    """根据 mvp_root 推断 evaluation/tasks 路径。"""
    global _EVAL_TASKS_ROOT
    # mvp_root 通常是 .../Skill-Following/benchmark
    project_root = mvp_root.parent
    candidate = project_root / "evaluation" / "tasks"
    if candidate.is_dir():
        _EVAL_TASKS_ROOT = candidate


def _load_config(task_id: str, sf_prefix: str = "") -> dict | None:
    """从 evaluation/tasks/<PREFIX>/configs/<task_id>.config.json 读取 config。

    支持多种命名风格：
      - <task_id>.config.json           （如 pr_creator_t1_feature_branch.config.json）
      - <SF前缀>_<suffix>.config.json   （如 SF03_t1_merge_unordered.config.json）
      - <task_id>.json                  （旧格式兼容）
    """
    if task_id in _config_cache:
        return _config_cache[task_id]

    if _EVAL_TASKS_ROOT is None:
        return None

    config = None

    # 构建候选文件名列表
    candidates = [
        f"{task_id}.config.json",
    ]
    # 如果 task_id 已经带有 SF 前缀，不需要额外添加
    # 如果 task_id 不带 SF 前缀，也生成带 SF 前缀的候选
    if sf_prefix and not task_id.startswith(sf_prefix):
        # 从 task_id 中提取 tN_xxx 后缀
        m = _re_module.search(r'(t\d+.*)', task_id)
        if m:
            candidates.append(f"{sf_prefix}_{m.group(1)}.config.json")

    def _try_load(dir_path: Path) -> dict | None:
        for cname in candidates:
            cfg_path = dir_path / cname
            if cfg_path.exists():
                try:
                    return json.loads(cfg_path.read_text(encoding="utf-8"))
                except Exception:
                    pass
        return None

    # 策略 1：精确路径（sf_prefix 已知）
    if sf_prefix:
        config = _try_load(_EVAL_TASKS_ROOT / sf_prefix / "configs")

    # 策略 2：遍历所有 SF* 目录
    if config is None:
        for prefix_dir in sorted(_EVAL_TASKS_ROOT.iterdir()):
            if not prefix_dir.is_dir():
                continue
            configs_dir = prefix_dir / "configs"
            if configs_dir.is_dir():
                config = _try_load(configs_dir)
                if config is not None:
                    break

    if config is not None:
        _config_cache[task_id] = config
    return config


def _resolve_target_from_config(task_id: str, sf_prefix: str = "") -> str | None:
    """从 config.json 读取 skill.name 作为 target_skill。"""
    config = _load_config(task_id, sf_prefix)
    if config is None:
        return None
    return config.get("skill", {}).get("name") or None


def _resolve_skill_dir_from_config(task_id: str, sf_prefix: str = "") -> str | None:
    """从 config.json 读取 mvp_skill_dir 作为 skill_dir。"""
    config = _load_config(task_id, sf_prefix)
    if config is None:
        return None
    raw = config.get("mvp_skill_dir", "")
    if raw:
        # "benchmark/skill_67_swiftui_view_refactor" -> "skill_67_swiftui_view_refactor"
        return raw.split("/")[-1]
    return None


# Task → (kind, target_skill, rubric_subpath)
#
# SF01/SF02 共用一份 positive rubric (rubric.yaml)，因为 t1/t2 同质（都是
# 一个 skill 下的不同 bug 任务，rubric 规则适用于全部）。
#
# SF03 (pdf) 不同：t1/t2/t3 子能力不同 (merge / table / chemistry-pdf)，
# 各 task 用独立 rubric (rubric_t1.yaml / rubric_t2.yaml / rubric_t3.yaml)。
#
# tasks/ 系列 task_id 形如 SF03_t<N>_<verb>_<noun>（例如
# SF03_t1_merge_unordered, SF03_t8_negative_no_trigger），rubric 文件
# 在 skill_03_pdf/rubrics/rubric_<suffix>.yaml。判定方法：
# task_id 第二段开头匹配 "t<digits>" 但后面还跟有下划线和文字
# （区分于旧的 "SF03_t1" / "SF03_t3_negative"）。
def _is_v2_task(task_id: str) -> bool:
    """v2 task: SF03_t<N>_<word>[_<word>...]，第二段后还有非空尾巴。
    
    排除规则：旧版负例 SF0X_t<N>_negative（仅一个尾段且就是 'negative'）
    走旧路径（rubric_negative.yaml），不算 v2。
    """
    parts = task_id.split("_")
    if len(parts) < 3:
        return False
    if not parts[0].startswith("SF"):
        return False
    second = parts[1]
    # second 形如 't1' / 't10'，且后面还有至少一个非空 token
    if not (len(second) >= 2 and second[0] == "t" and second[1:].isdigit()):
        return False
    tail_parts = parts[2:]
    if not tail_parts:
        return False
    # 旧版负例 'SF0X_tN_negative'：仅 1 个尾段且就是 'negative'
    if tail_parts == ["negative"]:
        return False
    return True


def _extract_sf_prefix(task_id: str) -> str:
    """从 task_id 提取 SF 前缀（如 'SF67_t1_xxx' → 'SF67'）。"""
    m = _re_module.match(r"(SF\d+)", task_id)
    return m.group(1) if m else ""


def _resolve_skill_dir_from_benchmark(sf_prefix: str, mvp_root: Path) -> str | None:
    """从 benchmark 目录中查找 skill_<N>_xxx 目录。"""
    if not sf_prefix:
        return None
    m = _re_module.match(r"SF(\d+)", sf_prefix)
    if not m:
        return None
    num = int(m.group(1))
    for d in mvp_root.iterdir():
        if d.is_dir():
            dm = _re_module.match(r"skill_(\d+)_(.*)", d.name)
            if dm and int(dm.group(1)) == num:
                return d.name
    return None


def task_meta(task_id: str, mvp_root: Path,
              sf_prefix: str = "", orig_task_id: str = "") -> tuple[str, str, Path]:
    """确定 task 的 (kind, target_skill, rubric_path)。

    target_skill 解析优先级：
      1. config.json 的 skill.name（单一真相来源，与 run_task.sh 创建容器目录一致）
      2. benchmark 目录名自动推导（无 config 时的兼容路径）

    skill_dir 解析优先级：
      1. config.json 的 mvp_skill_dir
      2. benchmark 目录名扫描

    参数：
      sf_prefix:     调用方已知的 SF 前缀（如 "SF67"），用于加速 config 查找。
      orig_task_id:  原始 task_id（route_key 转换前的值），用于 config 查找。
    """
    # ── 1. 确定 SF 前缀 ──
    if not sf_prefix:
        sf_prefix = _extract_sf_prefix(task_id)

    # ── 2. 从 config.json 读取 target_skill 和 skill_dir ──
    # 尝试用 orig_task_id（原始名称）和 task_id（route_key）分别查找
    lookup_ids = [orig_task_id, task_id] if orig_task_id and orig_task_id != task_id else [task_id]
    target = None
    skill_dir = None
    for lid in lookup_ids:
        if target is None:
            target = _resolve_target_from_config(lid, sf_prefix)
        if skill_dir is None:
            sd = _resolve_skill_dir_from_config(lid, sf_prefix)
            if sd:
                skill_dir = sd

    # ── 3. Fallback：从 benchmark 目录名推导 ──
    if skill_dir is None:
        skill_dir = _resolve_skill_dir_from_benchmark(sf_prefix, mvp_root)
    if skill_dir is None:
        # 最终 fallback：尝试已知的特殊前缀
        if task_id.startswith("pr_creator"):
            skill_dir = "skill_52_pr_creator"
            sf_prefix = sf_prefix or "SF52"

    if target is None and skill_dir:
        # 从 skill_dir 名称推导 target（去掉 skill_NN_ 前缀）
        dm = _re_module.match(r"skill_\d+_(.*)", skill_dir)
        if dm:
            target = dm.group(1)
            print(f"[warn] task={task_id}: target_skill fallback to dir suffix {target!r} "
                  f"(no config.json found, may differ from actual skill.name)")

    if skill_dir is None or target is None:
        raise ValueError(
            f"unknown task prefix in {task_id!r}: cannot resolve skill_dir={skill_dir!r} "
            f"target={target!r}. Please add a config.json under "
            f"evaluation/tasks/{sf_prefix}/configs/{task_id}.config.json"
        )

    # ── tasks 路由 ──
    # task_id 形如 SF03_t1_merge_unordered / SF03_t8_negative_no_trigger
    # 新路径: <skill_dir>/rubrics/rubric_<suffix>.yaml
    # 兼容路径: <skill_dir>/tasks/rubric_<suffix>.yaml
    # 负例由 task_id 中是否含 "_negative_" 段决定（不能用 endswith("_negative")
    # 因为 t8 的 task_id 是 SF03_t8_negative_no_trigger）。
    if _is_v2_task(task_id):
        suffix = task_id.split("_", 1)[1]   # 'tN_<verb>_<noun>'
        kind = "negative" if ("negative" in suffix.split("_") or task_id in (
            "SF53_t3_protocol_trace_cli",
            "SF52_t3_review_draft_only",
            "SF69_t3_release_note_boundary",
            "SF73_t4_release_notes_cleanup",
            "SF83_t3_warehouse_inventory_note",
            "SF92_t4_market_landscape",
            "SF98_t4_release_brief",
        )) else "positive"
        new_rubric = mvp_root / skill_dir / "rubrics" / f"rubric_{suffix}.yaml"
        old_rubric = mvp_root / skill_dir / "tasks" / f"rubric_{suffix}.yaml"
        # fallback: <PREFIX>_t<N>_rubric.yaml 格式（如 SF04_t1_rubric.yaml）
        prefix = task_id.split("_")[0]
        t_part = suffix.split("_")[0]  # 'tN'
        alt_rubric = mvp_root / skill_dir / "rubrics" / f"{prefix}_{t_part}_rubric.yaml"
        # fallback: 无 rubric_ 前缀的格式（如 skill_06_docx/rubrics/t1_create_report_docx.yaml）
        bare_rubric = mvp_root / skill_dir / "rubrics" / f"{suffix}.yaml"
        if new_rubric.exists():
            rubric = new_rubric
        elif alt_rubric.exists():
            rubric = alt_rubric
        elif bare_rubric.exists():
            rubric = bare_rubric
        else:
            rubric = old_rubric
        return kind, target, rubric

    # ── v1 / L2 路由 ──
    # 兼容老结构（rubric_*.yaml 在 skill_dir 根下）和新结构（在 rubrics/ 下）。
    # 新路径优先；找不到则 fallback 到旧路径。
    def _resolve(name: str) -> Path:
        new = mvp_root / skill_dir / "rubrics" / name
        old = mvp_root / skill_dir / name
        return new if new.exists() else old

    # ── pr_creator 任务特殊路由（task_id 形如 pr_creator_t1_feature_branch）──
    if task_id.startswith("pr_creator_"):
        suffix = task_id[len("pr_creator_"):]   # e.g. "t1_feature_branch"
        # t3 是负例任务（review_draft_only = 不应触发 PR 创建）
        kind = "negative" if suffix.startswith("t3") else "positive"
        rubric_name = f"rubric_{suffix}.yaml"
        rubric = mvp_root / skill_dir / "rubrics" / rubric_name
        return kind, target, rubric

    if task_id.endswith("_negative"):
        kind = "negative"
        rubric = _resolve("rubric_negative.yaml")
    elif "_L2R_" in task_id:
        # L2 real task（如 SF03_L2R_t1）→ rubric_l2_<last>_real.yaml
        kind = "positive"
        suffix = task_id.split("_")[-1]     # "t1"
        rubric = _resolve(f"rubric_l2_{suffix}_real.yaml")
    elif "_L2_" in task_id:
        # L2 synthetic task（如 SF01_L2_t1）→ rubric_l2_<last>.yaml
        kind = "positive"
        suffix = task_id.split("_")[-1]     # "t1"
        rubric = _resolve(f"rubric_l2_{suffix}.yaml")
    elif task_id.startswith("SF03"):
        kind = "positive"
        suffix = task_id.split("_", 1)[1]
        rubric = _resolve(f"rubric_{suffix}.yaml")
    else:
        # 通用 fallback：形如 <prefix>_t<N>_<suffix> 的 task_id
        # 优先命中 rubrics/rubric_t<N>_<suffix>.yaml（拆分版），
        # 若不存在再退回旧的合并 rubric.yaml，保证向后兼容。
        kind = "positive"
        m = _re_module.search(r"_(t\d+)_(.+)$", task_id)
        if m:
            suffix = f"{m.group(1)}_{m.group(2)}"
            candidate = _resolve(f"rubric_{suffix}.yaml")
            rubric = candidate if candidate.exists() else _resolve("rubric.yaml")
        else:
            rubric = _resolve("rubric.yaml")
    return kind, target, rubric


def find_jobs(batch_dir: Path) -> list[Path]:
    """查找所有包含 trace.jsonl 的 job 目录。
    
    兼容两种布局：
      - 旧：batch_dir/jobs/<model>/trace.jsonl
      - 新：batch_dir/<model>/trace.jsonl（SF14+ 新布局，full/ 就是 batch_dir）
    """
    jobs_dir = batch_dir / "jobs"
    if jobs_dir.exists():
        return [p for p in jobs_dir.iterdir() if p.is_dir() and (p / "trace.jsonl").exists()]
    # 新布局：模型目录直接在 batch_dir 下
    return [p for p in batch_dir.iterdir() if p.is_dir() and (p / "trace.jsonl").exists()]


def discover_full_batches(runs_root: Path) -> list[dict]:
    """Auto-discover latest full batch per task.

    兼容三种 runs 布局：
      - 旧：runs/<TASK_ID>/batch_<ts>_<TASK_ID>_full
      - 中：runs/<PREFIX>/<TASK_ID>/batch_<ts>_<TASK_ID>_full
      - 新：runs/<PREFIX>/<TASK_ID>/full  （SF14+ 使用的布局）
    """
    latest: dict[str, Path] = {}
    if not runs_root.exists():
        return []
    # 旧/中布局：batch_*_full 目录
    # 只扫最多 2 层（runs/<TASK>/batch_*_full 或 runs/<PREFIX>/<TASK>/batch_*_full）
    # 避免 rglob 下钻进 trace 目录里的 .codex_home/.tmp/plugins/... 数十万文件
    def _collect_batches(depth_root: Path) -> None:
        for child in depth_root.iterdir():
            if not child.is_dir():
                continue
            cname = child.name
            if cname.startswith("batch_") and cname.endswith("_full"):
                latest_key = cname[len("batch_"):-len("_full")]
                parts = latest_key.split("_", 1)
                tk = parts[1] if len(parts) > 1 else latest_key
                if tk not in latest or child.stat().st_mtime > latest[tk].stat().st_mtime:
                    latest[tk] = child
    # 第 1 层：runs/<TASK>/batch_*_full（旧布局）
    for lvl1 in runs_root.iterdir():
        if not lvl1.is_dir():
            continue
        # 第 2 层：runs/<PREFIX>/<TASK>/batch_*_full（中布局）
        if lvl1.name.startswith("SF"):
            for lvl2 in lvl1.iterdir():
                if lvl2.is_dir():
                    # 只看 batch_*_full 直接子目录，不进 full/
                    for c in lvl2.iterdir():
                        if c.is_dir() and c.name.startswith("batch_") and c.name.endswith("_full"):
                            key = c.name[len("batch_"):-len("_full")]
                            p = key.split("_", 1)
                            tk = p[1] if len(p) > 1 else key
                            if tk not in latest or c.stat().st_mtime > latest[tk].stat().st_mtime:
                                latest[tk] = c
        else:
            for c in lvl1.iterdir():
                if c.is_dir() and c.name.startswith("batch_") and c.name.endswith("_full"):
                    key = c.name[len("batch_"):-len("_full")]
                    p = key.split("_", 1)
                    tk = p[1] if len(p) > 1 else key
                    if tk not in latest or c.stat().st_mtime > latest[tk].stat().st_mtime:
                        latest[tk] = c
    # 新布局：runs/<PREFIX>/<TASK_ID>/full/ 目录（没有 batch_ 前缀）
    # sf_prefix_map: task_id -> SF前缀（如 SF52），用于 task_meta 路由
    sf_prefix_map: dict[str, str] = {}
    for prefix_dir in runs_root.iterdir():
        if not prefix_dir.is_dir() or not prefix_dir.name.startswith("SF"):
            continue
        for task_dir in prefix_dir.iterdir():
            if not task_dir.is_dir():
                continue
            full_dir = task_dir / "full"
            if full_dir.is_dir():
                task_id = task_dir.name
                # 检查是否有 trace.jsonl 文件（确认是有效的运行）
                has_traces = any(
                    (full_dir / m / "trace.jsonl").exists()
                    for m in full_dir.iterdir() if m.is_dir()
                )
                if has_traces and (task_id not in latest):
                    latest[task_id] = full_dir
                    sf_prefix_map[task_id] = prefix_dir.name
    return [
        {"task": task, "mode": "full", "batch_dir": str(path),
         "sf_prefix": sf_prefix_map.get(task, "")}
        for task, path in sorted(latest.items())
    ]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch-dirs", nargs="+", default=None,
                    help="batch_run_eval/runs/.../batch_<ts>_<task>_full 路径，可重复")
    ap.add_argument("--auto-discover", action="store_true",
                    help="在 batch_run_eval/runs/SF*/ 下自动找最新的 _full")
    ap.add_argument("--only-prefix", nargs="+", default=None,
                    help="只评指定 prefix 的 task（如 SF34 SF28），配合 --auto-discover 使用")
    ap.add_argument("--mvp-root", default="/data/workspace/Skill-Following/benchmark")
    ap.add_argument("--runs-root", default="/data/workspace/Skill-Following/evaluation/runs")
    ap.add_argument("--judge-model", default="gpt-5")
    ap.add_argument("--only-models", nargs="+", default=None,
                    help="只评指定模型的 trace（如 claude-opus-4-8-codex），配合 --auto-discover 使用")
    ap.add_argument("--out", default="/tmp/sf_matrix/matrix_score_v3")
    args = ap.parse_args()

    mvp = Path(args.mvp_root).resolve()
    _set_eval_tasks_root(mvp)

    items = []
    if args.batch_dirs:
        for bd in args.batch_dirs:
            bdp = Path(bd).resolve()
            name = bdp.name
            if name.endswith("_full"):
                # 旧布局：batch_<ts>_<task>_full
                mid = name[len("batch_"):-len("_full")] if name.startswith("batch_") else name[:-len("_full")]
                parts = mid.split("_", 1)
                task = parts[1] if len(parts) > 1 else mid
                items.append({"task": task, "mode": "full", "batch_dir": str(bdp)})
            elif name == "full":
                # 新布局：runs/<PREFIX>/<TASK_ID>/full/
                task = bdp.parent.name
                # 从 runs/<PREFIX>/<TASK>/full 的祖父目录反推 sf_prefix，
                # 保持与 --auto-discover 路径一致；否则非 SFxx_tN 命名的 task
                # （如 pr_creator_t1_...、ELG_t1_...）会 rubric missing。
                grandparent = bdp.parent.parent.name
                sf_prefix = grandparent if grandparent.startswith("SF") else ""
                items.append({"task": task, "mode": "full", "batch_dir": str(bdp),
                              "sf_prefix": sf_prefix})
            else:
                print(f"[warn] skip unrecognized dir: {bdp}")
                continue
    elif args.auto_discover:
        items = discover_full_batches(Path(args.runs_root).resolve())
    else:
        ap.error("must specify --batch-dirs or --auto-discover")

    # --only-prefix 过滤
    # 同时匹配 task 名前缀（如 SF52_t1_...）以及 batch_dir 路径中的 SF 父目录名（如 runs/SF52/pr_creator_t1_.../full）
    if args.only_prefix:
        prefixes = set(args.only_prefix)
        def _prefix_match(it: dict) -> bool:
            task = it["task"]
            if any(task.startswith(p) for p in prefixes):
                return True
            # 从 batch_dir 路径向上找 SFxx 风格目录名
            bd = Path(it["batch_dir"])
            for part in bd.parts:
                if any(part == p or part.startswith(p + "_") for p in prefixes):
                    return True
            return False
        items = [it for it in items if _prefix_match(it)]

    judge_call = make_judge_caller()

    # 收集所有待评分的 (task, job) 对
    score_jobs = []
    for it in items:
        bdp = Path(it["batch_dir"])
        if not bdp.exists():
            print(f"[warn] batch_dir missing: {bdp}")
            continue
        task = it["task"]
        # 若 task 名不以 SFxx 开头（如 pr_creator_t1_feature_branch），
        # 从 task 名中提取 tN_xxx 后缀，拼成 SFxx_tN_xxx 标准格式供 task_meta 路由
        sf_prefix = it.get("sf_prefix", "")
        if not task.startswith("SF") and sf_prefix:
            m = _re_module.search(r'(t\d+_.+)$', task)
            t_suffix = m.group(1) if m else task
            route_key = f"{sf_prefix}_{t_suffix}"
        else:
            route_key = task
        kind, target_skill, rubric = task_meta(route_key, mvp,
                                               sf_prefix=sf_prefix,
                                               orig_task_id=task)
        if not rubric.exists():
            print(f"[warn] rubric missing for task={task}: {rubric}")
            continue
        for job in find_jobs(bdp):
            model = job.name
            # --only-models 过滤：只评指定模型
            if args.only_models and model not in args.only_models:
                continue
            score_jobs.append({
                "task": task, "kind": kind, "target_skill": target_skill,
                "rubric": rubric, "job": job, "model": model,
            })

    SCORE_CONCURRENCY = int(os.environ.get("SF_SCORE_CONCURRENCY", "4"))
    print(f"[score] {len(score_jobs)} jobs to score, concurrency={SCORE_CONCURRENCY}")
    sys.stdout.flush()

    # ── 串行评分（多进程/多线程在 judge 客户端写 os.environ 时有竞态，
    #    改为串行调用，每个 job 独立创建 Api 实例）──
    rows = []
    for idx, sj in enumerate(score_jobs, 1):
        task, kind, target_skill = sj["task"], sj["kind"], sj["target_skill"]
        rubric_path, job, model = sj["rubric"], sj["job"], sj["model"]

        # ── 健康检查：跳过 API 异常（is_error=True）的 trace，不消耗 judge token ──
        trace_path = job / "trace.jsonl"
        meta_path = job / "meta.json"
        if trace_path.exists():
            try:
                _lines = trace_path.read_text(errors="replace").splitlines()
                _has_api_error = any(
                    json.loads(l).get("type") == "result" and json.loads(l).get("is_error")
                    for l in _lines if l.strip()
                )
                _tool_steps = sum(
                    1 for l in _lines if l.strip()
                    and json.loads(l).get("type") in ("tool_use", "tool_result")
                )
                if _has_api_error:
                    # 提取错误摘要
                    _err_msg = ""
                    for l in _lines:
                        try:
                            d = json.loads(l)
                            if d.get("type") == "result" and d.get("is_error"):
                                _err_msg = str(d.get("result", ""))[:80]
                                break
                        except Exception:
                            pass
                    print(f"[skip] task={task} model={model} — API error in trace, skipping. ({_err_msg})")
                    sys.stdout.flush()
                    continue
            except Exception:
                pass  # 解析失败则继续正常打分

        # ── meta.json 健康检查（仅打印警告，不跳过） ──
        # 注意：error_max_turns 和 timeout 的 trace 仍然可以产出有效评分，
        # 原始6模型评分时就没有跳过这些情况，为保持评分标准一致性，这里只打印警告。
        if meta_path.exists():
            try:
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
                _ok = meta.get("ok", True)
                _result_subtype = meta.get("result_subtype", "")
                _duration = meta.get("duration_sec", 0)

                if not _ok or _result_subtype == "error_max_turns":
                    print(f"[warn] task={task} model={model} — run not ok (meta.json ok={_ok}, "
                          f"result_subtype={_result_subtype!r}), scoring anyway.")
                    sys.stdout.flush()

                elif _duration >= 890 and _result_subtype == "":
                    print(f"[warn] task={task} model={model} — timeout ({_duration}s) with "
                          f"empty result_subtype, scoring anyway.")
                    sys.stdout.flush()
            except Exception:
                pass  # meta.json 解析失败则继续正常打分
        # 评分前预处理
        try:
            process_job_dir(job)
        except Exception as e:
            print(f"  [postproc] {model}: {type(e).__name__}: {e}")
        try:
            rep = score(job / "trace.jsonl", rubric_path,
                        job_dir=job, judge_model=args.judge_model,
                        judge_call_fn=judge_call,
                        task_kind=kind, target_skill=target_skill)
        except Exception as e:
            print(f"  ERROR: {task} {model}: {e}")
            sys.stdout.flush()
            continue

        # ── 一致性校验：target_skill 与 trace 中注册的 skills 列表对比 ──
        if (target_skill and kind == "positive"
                and not rep.get("trigger_detail", {}).get("skill_registered", True)):
            print(f"  [WARN] target_skill={target_skill!r} not found in trace "
                  f"registered skills for task={task} model={model}. "
                  f"Check config.json skill.name consistency.")
            sys.stdout.flush()

        row = {
            "task": task,
            "task_kind": kind,
            "target_skill": target_skill,
            "model": model,
            "skill_following_score": (round(rep["skill_following_score"], 3)
                                      if rep["skill_following_score"] is not None else "n/a"),
            "process_following_score": (round(rep["process_following_score"], 3)
                                        if rep["process_following_score"] is not None else "n/a"),
            "trigger_score": rep["trigger_score"],
            "trigger_verdict": rep["trigger_verdict"],
            "compliance_score": (round(rep["compliance_score"], 3)
                                 if rep["compliance_score"] is not None else "n/a"),
            "boundary_score": (round(rep["boundary_score"], 3)
                              if rep["boundary_score"] is not None else "n/a"),
            "gate_passed": rep["gate_passed"],
            "gate_failed_ids": ",".join(rep["gate_failed_ids"]),
            "task_completion_score": rep.get("task_completion_score", "n/a"),
            "task_failed_ids": ",".join(rep.get("task_failed_ids", [])),
            "task_items": rep.get("task_items_count", 0),
            "rubric_overall_score": round(rep["score"], 3),
            "passed": rep["passed_count"],
            "total": rep["rubric_total"],
            "scored_items": rep["compliance_items_count"] + rep["boundary_items_count"],
            "instruction_items": rep["instruction_items_count"],
            "hard_violations": rep["hard_violation_count"],
            "n_steps": rep["n_steps"],
            "skill_tool_calls_total": rep["trigger_detail"]["skill_tool_calls_total"],
            "skill_tool_calls_target": rep["trigger_detail"]["skill_tool_calls_target"],
            "skill_registered": rep["trigger_detail"]["skill_registered"],
            "trace": str(job / "trace.jsonl"),
        }
        for it2 in rep["items"]:
            row[f"r:{it2['id']}"] = "P" if it2["passed"] else "F"

        sf = "n/a" if rep["skill_following_score"] is None else f"{rep['skill_following_score']:.2f}"
        tg = "n/a" if rep["trigger_score"] is None else f"{rep['trigger_score']:.0f}"
        cs = "n/a" if rep["compliance_score"] is None else f"{rep['compliance_score']:.2f}"
        bs = "n/a" if rep["boundary_score"] is None else f"{rep['boundary_score']:.2f}"
        gp = "PASS" if rep["gate_passed"] else f"FAIL[{','.join(rep['gate_failed_ids'])}]"
        tc = "n/a" if rep.get("task_completion_score") is None else f"{rep['task_completion_score']:.0f}"
        print(f"[score] task={task} kind={kind} target={target_skill} model={model}")
        print(f"  SF={sf} TRIGGER={tg} ({rep['trigger_verdict']:<18}) "
              f"GATE={gp} TASK={tc} COMPLIANCE={cs} BOUNDARY={bs} steps={rep['n_steps']}")
        sys.stdout.flush()
        rows.append(row)

    if not rows:
        print("[score] no rows; nothing to write.")
        return 0

    out_csv = Path(args.out + ".csv")
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    all_keys = list(rows[0].keys())
    for r in rows[1:]:
        for k in r:
            if k not in all_keys:
                all_keys.append(k)
    with out_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=all_keys)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    out_json = Path(args.out + ".json")
    out_json.write_text(json.dumps(rows, ensure_ascii=False, indent=2),
                        encoding="utf-8")
    print(f"\n[score] DONE.")
    print(f"  CSV : {out_csv}")
    print(f"  JSON: {out_json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
