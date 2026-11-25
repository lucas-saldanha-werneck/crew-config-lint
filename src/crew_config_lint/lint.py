"""Static checks for an agents.yaml / tasks.yaml pair.

Rules (all offline, no framework import needed):
  E001 agent missing role/goal/backstory
  E002 task missing description/expected_output
  E003 task points to an agent that is not defined
  E004 {placeholder} used in a prompt but not in the declared inputs
  E005 task context points to an unknown task, or to itself
  E006 task context cycle
  W001 agent defined but no task uses it
  W002 declared input never used in any prompt
  W003 task description is very short (< 5 words)
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import yaml

AGENT_FIELDS = ("role", "goal", "backstory")
TASK_FIELDS = ("description", "expected_output")
PLACEHOLDER = re.compile(r"(?<!\{)\{([A-Za-z_][A-Za-z0-9_]*)\}(?!\})")


@dataclass(frozen=True)
class Finding:
    code: str
    where: str
    message: str

    @property
    def level(self) -> str:
        return "error" if self.code.startswith("E") else "warning"

    def __str__(self) -> str:
        return f"{self.level.upper():7} {self.code} {self.where}: {self.message}"


def _placeholders(text: object) -> set[str]:
    return set(PLACEHOLDER.findall(text)) if isinstance(text, str) else set()


def _as_map(value: object) -> dict:
    return value if isinstance(value, dict) else {}


def _find_cycle(graph: dict[str, list[str]]) -> list[str] | None:
    state: dict[str, int] = {}
    stack: list[str] = []

    def visit(n: str) -> list[str] | None:
        state[n] = 1
        stack.append(n)
        for m in graph.get(n, []):
            if m not in graph or m == n:
                continue
            if state.get(m) == 1:
                return stack[stack.index(m):] + [m]
            if state.get(m) is None:
                found = visit(m)
                if found:
                    return found
        stack.pop()
        state[n] = 2
        return None

    for node in graph:
        if state.get(node) is None:
            found = visit(node)
            if found:
                return found
    return None


def lint_data(agents: object, tasks: object, inputs: list[str] | None = None) -> list[Finding]:
    agents, tasks = _as_map(agents), _as_map(tasks)
    out: list[Finding] = []
    used_agents: set[str] = set()
    used_vars: set[str] = set()

    for name, a in agents.items():
        a = _as_map(a)
        for f in AGENT_FIELDS:
            if not str(a.get(f, "") or "").strip():
                out.append(Finding("E001", f"agent {name}", f"missing '{f}'"))
            used_vars |= _placeholders(a.get(f))

    graph: dict[str, list[str]] = {}
    for name, t in tasks.items():
        t = _as_map(t)
        where = f"task {name}"
        for f in TASK_FIELDS:
            if not str(t.get(f, "") or "").strip():
                out.append(Finding("E002", where, f"missing '{f}'"))
        desc = str(t.get("description", "") or "")
        if desc.strip() and len(desc.split()) < 5:
            out.append(Finding("W003", where, "description has fewer than 5 words"))
        ag = t.get("agent")
        if ag is not None:
            used_agents.add(ag)
            if ag not in agents:
                out.append(Finding("E003", where, f"agent '{ag}' is not defined"))
        ctx = t.get("context") or []
        ctx = ctx if isinstance(ctx, list) else [ctx]
        graph[name] = [str(c) for c in ctx]
        for c in ctx:
            if c == name:
                out.append(Finding("E005", where, "context points to itself"))
            elif c not in tasks:
                out.append(Finding("E005", where, f"context task '{c}' is not defined"))
        for f in TASK_FIELDS:
            used_vars |= _placeholders(t.get(f))

    cycle = _find_cycle(graph)
    if cycle:
        out.append(Finding("E006", "tasks", "context cycle: " + " -> ".join(cycle)))

    for name in agents:
        if name not in used_agents:
            out.append(Finding("W001", f"agent {name}", "no task uses this agent"))

    if inputs is not None:
        declared = set(inputs)
        for v in sorted(used_vars - declared):
            out.append(Finding("E004", "inputs", f"{{{v}}} is used in a prompt but not declared"))
        for v in sorted(declared - used_vars):
            out.append(Finding("W002", "inputs", f"input '{v}' is declared but never used"))
    return out


def _load(path: Path) -> object:
    if not path.exists():
        raise FileNotFoundError(path)
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def lint_dir(directory: str | Path, inputs: list[str] | None = None) -> list[Finding]:
    d = Path(directory)
    for cand in (d / "config", d):
        if (cand / "agents.yaml").exists() and (cand / "tasks.yaml").exists():
            d = cand
            break
    else:
        raise FileNotFoundError(f"agents.yaml and tasks.yaml not found in {directory} or {directory}/config")
    return lint_data(_load(d / "agents.yaml"), _load(d / "tasks.yaml"), inputs)
