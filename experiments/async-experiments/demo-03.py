
import asyncio
import time
from dataclasses import dataclass, field
from heapq import heappop, heappush

#######################################################################################################################
# Simulation clock -- taken from Prof. Vuduc's example code

# https://stackoverflow.com/questions/279561/what-is-the-python-equivalent-of-static-variables-inside-a-function
def static_vars(**kwargs):
    def decorate(func):
        for k in kwargs:
            setattr(func, k, kwargs[k])
        return func
    return decorate

@static_vars(t=0)
def now():
    return now.t

def set_time(t_new=0):
    now.t = t_new
    return now()

#######################################################################################################################
# Future Events

@dataclass(order=True)
class ScheduledEvent(asyncio.Event):
    name: str = field(compare=False)
    time: float

    def __post_init__(self):
        super().__init__()


# delay   = ScheduledEvent("delay", 0)
# liftoff = ScheduledEvent("liftoff", 10)

# Implement the FutureEventList from Prof. Vuduc's example
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

#######################################################################################################################
# Mission Definition

async def start(countdown, liftoff, future):

    await countdown.wait()

    for i in [3, 2, 1]:
        time.sleep(0.2)
        print("T-", i)

    # liftoff.set()
    # heappush(future.events, liftoff)
    # sim_continue.set()
    queue_to_future.put_nowait(liftoff)

async def ascent_1(liftoff, stage, duration = 1):

    await liftoff.wait()
    print("We have liftoff!")

    # AdvanceTime(now() + duration)
    await asyncio.sleep(duration)

    stage.set()

async def ascent_2(stage, meco, duration = 1):

    await stage.wait()
    print("Staging complete")

    # AdvanceTime(now() + duration)
    await asyncio.sleep(1)

    meco.set()

async def in_orbit(meco):

    await meco.wait()
    print("System nominal --> We're in Orbit")

    queue_to_future.put_nowait("END")


#######################################################################################################################
# Mission Execution

queue_to_future = asyncio.Queue()

async def sim_engine(future):

    for event in future:
        # await asyncio.sleep(0.2)
        # update the time
        set_time(event.time)
        print(f"The time is {now()}")
        # trigger the event
        event.set()
        # await sim_continue.wait()
        new_event = await queue_to_future.get()

        if new_event != "END":
            heappush(future.events, new_event)

    print("~~~ END SIMULATION ~~~")

async def fly_mission():

    future = FutureEventList()

    # liftoff = asyncio.Event()
    countdown = ScheduledEvent("countdown", 0)
    liftoff   = ScheduledEvent("liftoff", 10)
    stage     = ScheduledEvent("separation", 25)
    meco      = ScheduledEvent("meco", 50)

    heappush(future.events, countdown)

    tasks = [
        asyncio.create_task(start(countdown, liftoff, future)),
        asyncio.create_task(ascent_1(liftoff, stage)),
        asyncio.create_task(ascent_2(stage, meco)),
        asyncio.create_task(in_orbit(meco)),
        asyncio.create_task(sim_engine(future))
    ]

    await asyncio.gather(*tasks)


asyncio.run(fly_mission())

print("DONE.")
