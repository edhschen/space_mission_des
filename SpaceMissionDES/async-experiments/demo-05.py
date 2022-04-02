
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
class TerminalEvent(asyncio.Event):
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


async def activity(name: str, start: ScheduledEvent, end: ScheduledEvent, sim):#, future: FutureEventList):

    await start.wait()
    print(f"EVENT:  {start.name}  @ time {sim.clock}")
    print(f"  Begin ACTIVITY:  {name}")

    sim.future_queue.put_nowait(end)


@dataclass
class Simulator:
    future: FutureEventList = FutureEventList()
    tasks: list = field(default_factory = lambda: [])
    predicates: list = field(default_factory = lambda: [])
    clock: float = 0.0
    future_queue: asyncio.Queue = asyncio.Queue()

    async def process_events(self):
        for event in self.future:
            # update the time
            # await asyncio.sleep(0.2)
            self.clock = event.time
            
            # trigger the event
            event.set()
            
            # await sim_continue.wait()
            new_event = await self.future_queue.get()

            if isinstance(new_event, ScheduledEvent):
                self.schedule(new_event)
            else:
                print("TERMINAL EVENT")

        print("> No more future.")


    def schedule(self, event: ScheduledEvent):
        heappush(self.future.events, event)

    def add_task(self, coroutine):
        self.tasks.append(
            asyncio.create_task(coroutine)
        )

    def add_activity(self, name: str, start: ScheduledEvent, end: ScheduledEvent):
        self.tasks.append(
            asyncio.create_task(
                activity(name, start, end, sim)
            )
        )

    async def run(self):
        self.add_task(self.process_events())
        await asyncio.gather(*self.tasks)


async def fly_mission(sim: Simulator):

    # liftoff = asyncio.Event()
    INIT = ScheduledEvent("countdown", 0)
    liftoff   = ScheduledEvent("liftoff", 10)
    stage     = ScheduledEvent("stage", 25)
    meco      = ScheduledEvent("meco", 50)
    TERM      = TerminalEvent("END", 51)

    sim.schedule(INIT)

    sim.add_activity("Pre-launch", INIT, liftoff)
    sim.add_activity("Ascent S1", liftoff, TERM)
    # sim.add_activity("Ascent S2", stage, meco)
    # sim.add_activity("Insertion", meco, TERM)

    # sim.tasks.extend([
    #     asyncio.create_task(activity("Pre-launch", INIT, liftoff)),
    # ])

    await sim.run()
    

# =============================================================================
# =============================================================================

sim = Simulator()

# INIT = ScheduledEvent("countdown", 0)
# liftoff   = ScheduledEvent("liftoff", 10)
# stage     = ScheduledEvent("stage", 25)
# meco      = ScheduledEvent("meco", 50)
# TERM      = TerminalEvent("END", 51)


# activity("Ascent", liftoff, stage, sim)'


# conops = {
#     liftoff.name: activity("Ascent S1", liftoff, stage, sim),
#     stage.name:   activity("Ascent S2", stage, meco, sim)
# }


print("\n***********\n***BEGIN***\n")

asyncio.run(fly_mission(sim))

print("\n***DONE****\n***********")