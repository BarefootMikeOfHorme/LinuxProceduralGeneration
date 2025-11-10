# test_async_dag.py
import asyncio
from vaultmind_forge.forge_executor.executor import DAG, Task, Executor

async def make_task(name, delay):
    async def f():
        await asyncio.sleep(delay)
        print(f"{name} done")
        return name
    return Task(name=name, func=f, deps=set())

async def main():
    dag = DAG()
    dag.add(await make_task("foundation", 1))
    dag.add(await make_task("generation", 2))
    dag.nodes["generation"].deps = {"foundation"}
    dag.add(await make_task("validation", 1))
    dag.nodes["validation"].deps = {"generation"}

    exec = Executor(dag)
    await exec.run()

if __name__ == "__main__":
    asyncio.run(main())
