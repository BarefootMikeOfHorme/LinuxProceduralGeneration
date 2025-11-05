# forge_executor

Async DAG (Directed Acyclic Graph) executor for VaultMind Forge.

## Features
- Topological sorting with circular dependency detection
- Parallel task execution with configurable parallelism
- Automatic retry with exponential backoff
- Lineage-aware logging with timestamps
- Clean error handling and reporting

## Usage

```python
import asyncio
from vaultmind_forge.forge_executor import DAG, Task, Executor

async def foundation_task():
    # Foundation layer work
    return "foundation_complete"

async def generation_task():
    # Generation layer work
    return "generation_complete"

async def main():
    dag = DAG()

    dag.add(Task(name="foundation", func=foundation_task, deps=set()))
    dag.add(Task(name="generation", func=generation_task, deps={"foundation"}))

    executor = Executor(dag, parallelism=3)
    results = await executor.run()

    print(results)

asyncio.run(main())
```
