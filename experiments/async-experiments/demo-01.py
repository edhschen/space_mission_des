
import asyncio
from concurrent.futures import process
from dataclasses import dataclass


@dataclass
class Simulator:
    now: float
    future: list
    state: dict

    processes: list
    suspended: list

sim = Simulator(0, [], {"count":0}, [], [])



async def activity(event):
    print("start")

    await event

    print("end")


async def main():

    print("Start main()")

    event = asyncio.Event()

    coro = activity(event)
    task = asyncio.create_task(coro)

    print("schedule Task")

    # await task


    print("complete Task")


if __name__ == "__main__":


    main()

    
    print("DONE.")
