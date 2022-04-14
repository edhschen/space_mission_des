
import asyncio
from dataclasses import dataclass, field
from heapq import heappop, heappush


#######################################################################################################################
# Event Template

@dataclass
class Event:
    """Object used to template events in a mission ConOps"""
    name: str

@dataclass
class Terminator(Event):
    """Object used to indicate end of mission"""
    name: str

    def __post_init__(self):
        super().__init__(self.name)
#######################################################################################################################
# Activities

@dataclass
class Activity:
    name: str
    start: Event
    end: Event
    duration: float


#######################################################################################################################
# ConOps

@dataclass
class ConOps:
    sequence: dict

    def first(self):
        return self.sequence["INIT"]

    def after(self, current_event):
        # Get the activity which starts with a particular event
        return self.sequence[current_event.name]


#######################################################################################################################
# Vehicle

@dataclass
class Vehicle:
    name: str
    conops: ConOps
    propload: float
    activity: Activity = None
    # trace: pd.DataFrame = pd.DataFrame(columns=['CurrentEvent', 'NextEvent', 'Prop', 'Activity'])

    def __repr__(self):
        return (f'{self.__class__.__name__} - {self.name}')

#######################################################################################################################

@dataclass(order=True)
class ScheduledEvent(asyncio.Event):
    name: str = field(compare=False)
    template: str = field(compare=False)
    time: float

    def __post_init__(self):
        super().__init__()

@dataclass(order=True)
class TerminalEvent(asyncio.Event):
    name: str = field(compare=False)
    template: str = field(compare=False)
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


# async def activity_handler(name: str, start: ScheduledEvent, end: ScheduledEvent, sim):
async def activity_handler(name: str, start: ScheduledEvent, sim):

    await start.wait()
    print(f"EVENT:  {start.name}  @ time {sim.clock}")


    current_activity = sim.conops.after(start)  # <- this gets the activity which comes after

    # In our approach, activity.start has already occurred.
    # So we must schedule the ending event, along with the the activity which will wait on that event

    if isinstance(current_activity.end, Terminator):
        current_end = TerminalEvent(
            current_activity.end.name,
            current_activity.end,
            sim.clock + current_activity.duration
        )
        next_start    = current_end
    else:
        current_end = ScheduledEvent(
            current_activity.end.name,
            current_activity.end,
            sim.clock + current_activity.duration
        )

        # Schedule the next activity, which will be waiting and started by the current end event
        next_activity = sim.conops.after(current_end)
        next_start    = current_end

        sim.tasks.append(
            asyncio.create_task(
                activity_handler(next_activity.name, next_start, sim)
            )
        )

    print(f"  Begin ACTIVITY:  {current_activity.name}")

    sim.queue_future.put_nowait(next_start)
    # sim.queue_future.put_nowait(new_end_event)


@dataclass
class Simulator:
    entities: list  # no default, we cannot start a sim without entities
    future: FutureEventList = FutureEventList()
    tasks: list = field(default_factory = lambda: [])
    predicates: list = field(default_factory = lambda: [])
    clock: float = 0.0
    queue_future: asyncio.Queue = asyncio.Queue()

    async def process_events(self):
        for event in self.future:
            # update the time
            # await asyncio.sleep(0.2)
            self.clock = event.time
            
            # trigger the event
            event.set()
            
            # await sim_continue.wait()
            new_event = await self.queue_future.get()

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

    def add_activity(self, name: str, start: ScheduledEvent):
        self.tasks.append(
            asyncio.create_task(
                activity_handler(name, start, sim)
            )
        )

    async def run(self):
        self.add_task(self.process_events())
        await asyncio.gather(*self.tasks)


async def fly_mission(sim: Simulator):

    # Initialize the mission
    activity = sim.conops.first()

    # Schedule the intial event
    INIT = ScheduledEvent(activity.start.name, activity.start, 0)
    
    sim.schedule(INIT)                     # This INIT event will be .set() at time zero
    sim.add_activity(activity.name, INIT)  # This activity will comments when the INIT event is .set()

    await sim.run()


#######################################################################################################################
# Demo
#######################################################################################################################

if __name__ == "__main__":

    # -----------------------------------------------------------------------------------------------------------------
    # Mission Definition
    # - Events
    INIT    = Event("INIT")
    liftoff = Event("Liftoff")
    stage   = Event("Stage")
    burnout = Event("Burnout")
    DONE    = Terminator("TERM")

    # - ConOps
    conops = ConOps({
        INIT.name:    Activity("Countdown", INIT, liftoff, 3),
        liftoff.name: Activity("Ascent S1", liftoff, stage, 10),
        stage.name:   Activity("Ascent S2", stage, burnout, 10),
        burnout.name: Activity("Insertion", burnout, DONE, 2)
    })

    v1 = Vehicle("V1", conops, 100)
    v2 = Vehicle("V2", conops, 100)

    sim = Simulator([])

    print("\n***********\n***BEGIN***\n")

    asyncio.run(fly_mission(sim))

    print("\n***DONE****\n***********")