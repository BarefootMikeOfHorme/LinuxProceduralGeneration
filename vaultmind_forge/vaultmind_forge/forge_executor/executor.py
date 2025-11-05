"""
VaultMind Forge Dependency Graph Executor
Simple async DAG runner with retry, lineage-aware logging.
"""

from __future__ import annotations
import asyncio
from dataclasses import dataclass, field
from typing import Callable, Coroutine, Dict, List, Optional, Set
from datetime import datetime

@dataclass
class Task:
    name: str
    func: Callable[[], Coroutine]
    deps: Set[str] = field(default_factory=set)
    retries: int = 1
    result: Optional[object] = None
    error: Optional[Exception] = None
    started: Optional[datetime] = None
    finished: Optional[datetime] = None

class DAG:
    def __init__(self):
        self.nodes: Dict[str, Task] = {}

    def add(self, task: Task):
        if task.name in self.nodes:
            raise ValueError(f"Duplicate task name {task.name}")
        self.nodes[task.name] = task

    def topo_sort(self) -> List[Task]:
        visited, stack = set(), []
        def visit(n: str):
            if n in visited:
                return
            visited.add(n)
            for d in self.nodes[n].deps:
                if d not in self.nodes:
                    raise KeyError(f"Unknown dependency {d} for {n}")
                visit(d)
            stack.append(self.nodes[n])
        for name in list(self.nodes.keys()):
            visit(name)
        return stack

class Executor:
    def __init__(self, dag: DAG, parallelism: int = 3):
        self.dag = dag
        self.parallelism = parallelism
        self.results: Dict[str, object] = {}

    async def run(self):
        pending: Dict[str, asyncio.Task] = {}
        done: Set[str] = set()
        sem = asyncio.Semaphore(self.parallelism)

        async def run_task(task: Task):
            async with sem:
                task.started = datetime.utcnow()
                for attempt in range(task.retries):
                    try:
                        task.result = await task.func()
                        task.finished = datetime.utcnow()
                        self.results[task.name] = task.result
                        print(f"[✓] {task.name}")
                        return
                    except Exception as e:
                        task.error = e
                        if attempt + 1 == task.retries:
                            print(f"[✗] {task.name} failed: {e}")
                        else:
                            print(f"[!] {task.name} retrying… ({attempt+1}/{task.retries})")
                            await asyncio.sleep(0.5)

        tasks_left = set(self.dag.nodes.keys())
        while tasks_left:
            ready = [n for n in tasks_left if self.dag.nodes[n].deps <= done]
            if not ready:
                raise RuntimeError("Deadlock or circular dependency detected.")
            coros = [run_task(self.dag.nodes[n]) for n in ready]
            for n in ready:
                tasks_left.remove(n)
            await asyncio.gather(*coros)
            done |= set(ready)
        return self.results
