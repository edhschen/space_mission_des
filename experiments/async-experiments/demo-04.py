
import asyncio
from dataclasses import dataclass, field
from heapq import heappop, heappush

queue_to_future = asyncio.Queue()

@dataclass(order=True)
class ScheduledEvent(asyncio.Event):
    name: str = field(compare=False)
    time: float

    def __post_init__(self):
        super().__init__()

@dataclass(order=True)
class CompletionEvent(asyncio.Event):
    name: str = field(compare=False)
    time: float

    def __post_init__(self):
        super().__init__()


class FutureEventList:
    def __init__(self):
        self.events = []
        
    def __iter__(self):
        return self
    
    def __next__(self) -> ScheduledEvent:
        if self.events:
            return heappop(self.events)
        raise StopIteration

    def __repr__(self) -> str:
        from pprint import pformat
        return pformat(self.events)

    def get_next(self):
        return heappop(self.events)


async def activity(name: str, start: ScheduledEvent, end: ScheduledEvent):#, future: FutureEventList):

    await start.wait()
    print(f"EVENT:  {start.name}")
    print(f"  Begin ACTIVITY:  {name}")

    queue_to_future.put_nowait(end)


async def sim_engine(future):

    for event in future:
        # await asyncio.sleep(0.2)
        # update the time
        # set_time(event.time)
        # print(f"The time is {now()}")
        
        # trigger the event
        event.set()
        
        # await sim_continue.wait()
        new_event = await queue_to_future.get()

        if isinstance(new_event, ScheduledEvent):
            heappush(future.events, new_event)

    print("~~~ END SIMULATION ~~~")

async def fly_mission():

    future = FutureEventList()

    # liftoff = asyncio.Event()
    INIT = ScheduledEvent("countdown", 0)
    liftoff   = ScheduledEvent("liftoff", 10)
    stage     = ScheduledEvent("stage", 25)
    meco      = ScheduledEvent("meco", 50)
    TERM      = CompletionEvent("END", 51)

    heappush(future.events, INIT)

    tasks = [
        asyncio.create_task(activity("Pre-launch", INIT, liftoff)),
        asyncio.create_task(activity("Ascent S1", liftoff, stage)),
        asyncio.create_task(activity("Ascent S2", stage, meco)),
        asyncio.create_task(activity("Insertion", meco, TERM)),
        asyncio.create_task(sim_engine(future))
    ]

    await asyncio.gather(*tasks)


asyncio.run(fly_mission())

print("DONE.")