#!/usr/bin/env python3
"""Dependency-graph analysis over the backend import graph.

Builds the module import graph for 01_source (resolving the projection's clean module
names via 11_build/00_runtime_projection/import_map.json), then runs:
  - Tarjan's Strongly-Connected-Components  -> CIRCULAR DEPENDENCY detection (any SCC > 1 module)
  - in-degree analysis                       -> ORPHAN / dead-module identification (0 importers, not an entrypoint)

Outputs a human report (stdout) plus machine artifacts: --json and --sarif (SARIF 2.1.0, so the
findings upload to GitHub code-scanning). Pure stdlib — no third-party deps, runs on host or in-container.

Usage:
    python 03_scripts/02_analysis/dep_graph_analysis.py [--root <backend_dir>] [--json out.json] [--sarif out.sarif] [--fail-on-cycles]
"""
from __future__ import annotations

import argparse
import ast
import json
import os
import re
import sys
from pathlib import Path

_NUMPREFIX = re.compile(r"^\d+_")  # the projection strips numeric dir prefixes (00_v3 -> v3)

ENTRYPOINT_HINTS = ("__init__", "main", "conftest", "asgi", "wsgi", "lifecycle", "app_factory")


def backend_root(explicit: str | None) -> Path:
    if explicit:
        return Path(explicit).resolve()
    # script lives at 03_scripts/02_analysis/ -> backend root is parents[2]
    return Path(__file__).resolve().parents[2]


def load_roots(be: Path) -> list[tuple[Path, str]]:
    """Return (physical_dir, clean_prefix) pairs from import_map.json, longest-dir first."""
    imap = be / "11_build" / "00_runtime_projection" / "import_map.json"
    pairs: list[tuple[Path, str]] = []
    if imap.exists():
        data = json.loads(imap.read_text(encoding="utf-8"))
        for clean, dirs in data.items():
            if clean.startswith("_"):
                continue
            for entry in dirs:
                p = entry.get("path") if isinstance(entry, dict) else entry
                if not p:
                    continue
                ap = (be / p)
                if ap.exists() and "01_source" in p:  # only the real source tree
                    pairs.append((ap.resolve(), clean))
    # fallback minimal roots if the map is missing
    if not pairs:
        pairs = [((be / "01_source" / "00_core").resolve(), "core"),
                 ((be / "01_source" / "01_application").resolve(), "app")]
    pairs.sort(key=lambda t: len(str(t[0])), reverse=True)
    return pairs


def file_to_module(path: Path, roots: list[tuple[Path, str]]) -> str | None:
    for d, clean in roots:
        try:
            rel = path.resolve().relative_to(d)
        except ValueError:
            continue
        parts = [_NUMPREFIX.sub("", p) for p in rel.with_suffix("").parts]
        if parts and parts[-1] == "__init__":
            parts = parts[:-1]
        return ".".join([clean] + parts) if parts else clean
    return None


def resolve_import(mod: str, nodes: set[str]) -> str | None:
    """Trim a dotted import path from the right until it matches a known node."""
    cur = mod
    while cur:
        if cur in nodes:
            return cur
        if "." not in cur:
            return None
        cur = cur.rsplit(".", 1)[0]
    return None


def tarjan(graph: dict[str, set[str]]) -> list[list[str]]:
    """Iterative Tarjan SCC. Returns list of components (each a list of nodes)."""
    index = {}
    low = {}
    on_stack = set()
    stack: list[str] = []
    sccs: list[list[str]] = []
    counter = [0]

    for start in graph:
        if start in index:
            continue
        work = [(start, iter(graph[start]))]
        index[start] = low[start] = counter[0]; counter[0] += 1
        stack.append(start); on_stack.add(start)
        while work:
            node, it = work[-1]
            advanced = False
            for succ in it:
                if succ not in graph:
                    continue
                if succ not in index:
                    index[succ] = low[succ] = counter[0]; counter[0] += 1
                    stack.append(succ); on_stack.add(succ)
                    work.append((succ, iter(graph[succ])))
                    advanced = True
                    break
                elif succ in on_stack:
                    low[node] = min(low[node], index[succ])
            if advanced:
                continue
            if low[node] == index[node]:
                comp = []
                while True:
                    w = stack.pop(); on_stack.discard(w); comp.append(w)
                    if w == node:
                        break
                sccs.append(comp)
            work.pop()
            if work:
                parent = work[-1][0]
                low[parent] = min(low[parent], low[node])
    return sccs


def _node_targets(node, pkg: str, nodes: set) -> set:
    """Resolve the import targets of a single Import/ImportFrom node to known nodes."""
    raw = []
    if isinstance(node, ast.Import):
        raw = [a.name for a in node.names]
    elif isinstance(node, ast.ImportFrom):
        if node.level and node.level > 0:  # relative import
            base = pkg
            for _ in range(node.level - 1):
                base = base.rsplit(".", 1)[0] if "." in base else base
            raw = [f"{base}.{node.module}" if node.module else base]
        elif node.module:
            raw = [node.module]
    out = set()
    for t in raw:
        tgt = resolve_import(t, nodes)
        if tgt:
            out.add(tgt)
    return out


def _is_type_checking(test) -> bool:
    return (isinstance(test, ast.Name) and test.id == "TYPE_CHECKING") or \
           (isinstance(test, ast.Attribute) and test.attr == "TYPE_CHECKING")


def _hard_imports(body, pkg: str, nodes: set, out: set):
    """Collect only imports that execute at MODULE LOAD time.

    Recurses through module-level control flow (if/try/with/for/while/class) but NOT into
    function/method bodies (lazy imports) and NOT into `if TYPE_CHECKING:` blocks (type-only).
    These are the edges that can cause a real circular-import failure.
    """
    for stmt in body:
        if isinstance(stmt, (ast.Import, ast.ImportFrom)):
            out |= _node_targets(stmt, pkg, nodes)
        elif isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue  # lazy: runs only when called
        elif isinstance(stmt, ast.If):
            if _is_type_checking(stmt.test):
                continue  # type-only, no runtime edge
            _hard_imports(stmt.body, pkg, nodes, out)
            _hard_imports(stmt.orelse, pkg, nodes, out)
        elif isinstance(stmt, ast.Try):
            _hard_imports(stmt.body, pkg, nodes, out)
            for h in stmt.handlers:
                _hard_imports(h.body, pkg, nodes, out)
            _hard_imports(stmt.orelse, pkg, nodes, out)
            _hard_imports(stmt.finalbody, pkg, nodes, out)
        elif isinstance(stmt, (ast.With, ast.AsyncWith, ast.For, ast.AsyncFor, ast.While)):
            _hard_imports(stmt.body, pkg, nodes, out)
            _hard_imports(getattr(stmt, "orelse", []), pkg, nodes, out)
        elif isinstance(stmt, ast.ClassDef):
            _hard_imports(stmt.body, pkg, nodes, out)  # class body executes at import


def build(be: Path):
    roots = load_roots(be)
    src = be / "01_source"
    files = [p for p in src.rglob("*.py") if "__pycache__" not in p.parts]
    mod_of: dict[str, Path] = {}
    for f in files:
        m = file_to_module(f, roots)
        if m:
            mod_of[m] = f
    nodes = set(mod_of)
    # hard_graph = module-load-time edges (for cycle detection);
    # full_graph = all imports incl. lazy/function-local (for orphan/in-degree detection).
    hard_graph: dict[str, set[str]] = {m: set() for m in nodes}
    full_graph: dict[str, set[str]] = {m: set() for m in nodes}
    for m, f in mod_of.items():
        try:
            tree = ast.parse(f.read_text(encoding="utf-8", errors="replace"), filename=str(f))
        except SyntaxError:
            continue
        pkg = m.rsplit(".", 1)[0] if "." in m else m
        hard: set = set()
        _hard_imports(tree.body, pkg, nodes, hard)
        hard_graph[m] = {t for t in hard if t != m}
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                for tgt in _node_targets(node, pkg, nodes):
                    if tgt != m:
                        full_graph[m].add(tgt)
    return mod_of, hard_graph, full_graph


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Tarjan SCC circular-dependency + orphan analysis.")
    ap.add_argument("--root", default=None)
    ap.add_argument("--json", default=None)
    ap.add_argument("--sarif", default=None)
    ap.add_argument("--fail-on-cycles", action="store_true")
    args = ap.parse_args(argv)

    be = backend_root(args.root)
    mod_of, hard_graph, full_graph = build(be)
    n_nodes = len(hard_graph)
    n_edges = sum(len(v) for v in full_graph.values())
    n_hard = sum(len(v) for v in hard_graph.values())

    # Cycles use the module-load graph (lazy/function-local + TYPE_CHECKING imports excluded),
    # so only edges that can actually cause a circular-import failure are counted.
    cycles = [sorted(c) for c in tarjan(hard_graph) if len(c) > 1]
    cycles.sort(key=len, reverse=True)

    # Orphans use the full graph (a module imported only lazily is still used).
    indeg = {m: 0 for m in full_graph}
    for deps in full_graph.values():
        for d in deps:
            indeg[d] = indeg.get(d, 0) + 1
    orphans = sorted(
        m for m, d in indeg.items()
        if d == 0 and not any(h in m.rsplit(".", 1)[-1] for h in ENTRYPOINT_HINTS)
    )

    # ---- human report ----
    print(f"Dependency-graph analysis  ({n_nodes} modules, {n_edges} import edges, {n_hard} module-load edges)")
    print(f"  circular-dependency SCCs (module-load, size>1): {len(cycles)}")
    for i, c in enumerate(cycles[:20], 1):
        print(f"    cycle {i} ({len(c)} modules): {', '.join(c)}")
    print(f"  orphan modules (0 importers, not entrypoint): {len(orphans)}")
    for o in orphans[:30]:
        print(f"    orphan: {o}")

    rel = lambda m: str(mod_of[m].relative_to(be)).replace("\\", "/") if m in mod_of else m
    payload = {
        "modules": n_nodes, "edges": n_edges,
        "circular_dependencies": [{"modules": c, "files": [rel(x) for x in c]} for c in cycles],
        "orphans": [{"module": o, "file": rel(o)} for o in orphans],
    }
    if args.json:
        Path(args.json).write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"  wrote JSON -> {args.json}")

    if args.sarif:
        results = []
        for c in cycles:
            results.append({
                "ruleId": "circular-dependency",
                "level": "warning",
                "message": {"text": f"Circular import dependency among {len(c)} modules: {', '.join(c)}"},
                "locations": [{"physicalLocation": {"artifactLocation": {"uri": rel(c[0])}}}],
            })
        for o in orphans:
            results.append({
                "ruleId": "orphan-module",
                "level": "note",
                "message": {"text": f"Module {o} has no importers (orphan/dead candidate)."},
                "locations": [{"physicalLocation": {"artifactLocation": {"uri": rel(o)}}}],
            })
        sarif = {
            "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
            "version": "2.1.0",
            "runs": [{
                "tool": {"driver": {
                    "name": "hcie-dep-graph",
                    "informationUri": "https://github.com/",
                    "rules": [
                        {"id": "circular-dependency", "name": "CircularDependency",
                         "shortDescription": {"text": "Circular import dependency (Tarjan SCC > 1)"}},
                        {"id": "orphan-module", "name": "OrphanModule",
                         "shortDescription": {"text": "Module with zero importers"}},
                    ],
                }},
                "results": results,
            }],
        }
        Path(args.sarif).write_text(json.dumps(sarif, indent=2), encoding="utf-8")
        print(f"  wrote SARIF -> {args.sarif}")

    if args.fail_on_cycles and cycles:
        print("FAIL: circular dependencies present", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
