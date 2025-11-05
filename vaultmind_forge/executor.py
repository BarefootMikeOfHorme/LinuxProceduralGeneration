"""
Simple async DAG executor for VaultMind Forge.
- Define TaskNodes with dependencies.
- Executor runs tasks respecting dependencies, with concurrency and retries.
- Each task is an async callable returning a result dict; failures can be retried.

Usage example available when run as a script.
"""

from __future__ import annotations
import asyncio
from dataclasses import dataclass, field
from typing import Callable, Any, Dict, List, Optional, Set
import time
import logging

logger = logging.getLogger("vaultmind_forge.executor")
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)

@dataclass
class TaskNode:
 id: str
 coro: Callable[..., Any] # async callable
 deps: List[str] = field(default_factory=list)
 retry: int =0
 retry_delay: float =1.0
 result: Any = None
 error: Optional[Exception] = None

class DAGExecutor:
 def __init__(self, max_concurrency: int =4):
 self.max_concurrency = max_concurrency
 self._nodes: Dict[str, TaskNode] = {}

 def add_node(self, node: TaskNode):
 if node.id in self._nodes:
 raise KeyError(f"Task {node.id} already exists")
 self._nodes[node.id] = node

 def _topo_sort(self) -> List[str]:
 # Kahn's algorithm
 indeg = {k:0 for k in self._nodes}
 graph = {k: [] for k in self._nodes}
 for nid, node in self._nodes.items():
 for d in node.deps:
 if d not in self._nodes:
 raise KeyError(f"Dependency {d} of {nid} not found")
 indeg[nid] +=1
 graph[d].append(nid)
 q = [n for n, deg in indeg.items() if deg ==0]
 order = []
 while q:
 n = q.pop(0)
 order.append(n)
 for m in graph[n]:
 indeg[m] -=1
 if indeg[m] ==0:
 q.append(m)
 if len(order) != len(self._nodes):
 raise RuntimeError("Cycle detected in DAG")
 return order

 async def run(self, timeout: Optional[float] = None) -> Dict[str, Any]:
 order = self._topo_sort()
 deps_map = {nid: set(self._nodes[nid].deps) for nid in order}
 pending: Set[str] = set(order)
 completed: Set[str] = set()
 sem = asyncio.Semaphore(self.max_concurrency)
 tasks_map: Dict[str, asyncio.Task] = {}

 async def run_node(nid: str):
 node = self._nodes[nid]
 attempt =0
 while True:
 try:
 async with sem:
 logger.info("Running task %s (attempt %d)", nid, attempt +1)
 start = time.time()
 # call the coro; assume it's an async callable with no args
 res = await node.coro()
 duration = time.time() - start
 logger.info("Task %s completed in %.2fs", nid, duration)
 node.result = res
 node.error = None
 return
 except Exception as e:
 node.error = e
 attempt +=1
 logger.warning("Task %s failed attempt %d: %s", nid, attempt, e)
 if attempt > node.retry:
 logger.error("Task %s exhausted retries", nid)
 raise
 await asyncio.sleep(node.retry_delay)

 loop = asyncio.get_event_loop()
 try:
 while pending:
 # find runnable nodes (deps satisfied)
 runnable = [nid for nid in pending if deps_map[nid].issubset(completed)]
 if not runnable:
 raise RuntimeError("No runnable nodes but pending remains (cycle?)")
 # schedule runnable nodes
 running_tasks = []
 for nid in runnable:
 task = loop.create_task(run_node(nid))
 tasks_map[nid] = task
 running_tasks.append((nid, task))
 pending.remove(nid)
 # wait for any to finish (or until all finish)
 done, _ = await asyncio.wait([t for _, t in running_tasks], return_when=asyncio.FIRST_COMPLETED, timeout=timeout)
 if not done:
 # timed out waiting for progress
 raise asyncio.TimeoutError("Timeout while executing DAG")
 # mark completed tasks, raise if failed
 for t in done:
 # find nid
 nid = None
 for key, tok in tasks_map.items():
 if tok is t:
 nid = key
 break
 if nid is None:
 continue
 exc = None
 try:
 _ = t.result()
 except Exception as e:
 exc = e
 if exc:
 raise exc
 completed.add(nid)
 # all done
 finally:
 # cancel any remaining
 for t in tasks_map.values():
 if not t.done():
 t.cancel()
 return {nid: self._nodes[nid].result for nid in order}


# Simple usage example when executed directly
if __name__ == "__main__":
 import asyncio

 async def step_a():
 await asyncio.sleep(0.1)
 return "A"

 async def step_b():
 await asyncio.sleep(0.2)
 return "B"

 async def run_example():
 e = DAGExecutor(max_concurrency=2)
 e.add_node(TaskNode(id="a", coro=step_a))
 e.add_node(TaskNode(id="b", coro=step_b, deps=["a"]))
 res = await e.run()
 print(res)

 asyncio.run(run_example())
