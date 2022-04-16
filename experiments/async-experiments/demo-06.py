
import asyncio
import pandas as pd
from dataclasses import dataclass, field
from heapq import heappop, heappush


#######################################################################################################################
# Event Template

@dataclass
class Event:
    """Object used to template events in a mission ConOps"""
    name: str

@dataclass
class Completor(Event):
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
    trace: pd.DataFrame = pd.DataFrame(columns=['Time', 'CurrentEvent', 'NextEvent', 'Prop', 'Activity'])

    def __repr__(self):
        return (f'{self.__class__.__name__} - {self.name}')

    def update_trace(self, sim_time):
        self.trace = pd.concat([
            self.trace,
            pd.DataFrame({
                "Time": sim_time,
                "CurrentEvent": self.activity.start, 
                "NextEvent": self.activity.end, 
                "Prop": self.propload, 
                "Activity": self.activity}, index = [len(self.trace) + 1])
        ])

#######################################################################################################################

@dataclass(order=True)
class ScheduledEvent(asyncio.Event):
    name: str = field(compare=False)
    template: str = field(compare=False)
    time: float

    def __post_init__(self):
        super().__init__()  # Make sure we inherit all of the attributes of the asyncio.Event class

@dataclass(order=True)
class CompletionEvent(asyncio.Event):
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


@dataclass
class Simulator:
    entities: dict = field(default_factory = lambda: {})  
    # no default, we cannot start a sim without entities ? 
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
                print(f"TERMINAL EVENT @ time {new_event.time}")

        print("> No more future.")


    def schedule(self, event: ScheduledEvent):
        heappush(self.future.events, event)

    def add_task(self, coroutine):
        self.tasks.append(
            asyncio.create_task(coroutine)
        )

    def add_activity(self, name: str, start: ScheduledEvent, vehicle: Vehicle):
        self.tasks.append(
            asyncio.create_task(
                activity_handler(name, start, self, vehicle)
            )
        )

    def add_vehicle(self, vehicle: Vehicle, start_time: float):
        # Add the vehicle to the entities list
        self.entities.update({vehicle.name: vehicle})
        # Get the first activity in the vehicles's conops and schedule it
        activity = vehicle.conops.first()
        # Schedule the intial event
        INIT = ScheduledEvent(activity.start.name, activity.start, start_time)
        self.schedule(INIT)                     # This INIT event will be .set() at time zero
        self.add_activity(activity.name, INIT, vehicle)  # This activity will comments when the INIT event is .set()

    async def run(self, initial_vehicles):

        for vehicle, start_time in initial_vehicles:
            self.add_vehicle(vehicle, start_time)

        self.add_task(self.process_events())
        await asyncio.gather(*self.tasks)

# async def activity_handler(name: str, start: ScheduledEvent, end: ScheduledEvent, sim):
async def activity_handler(name: str, start: ScheduledEvent, sim: Simulator, vehicle: Vehicle):

    await start.wait()
    print(f"\nEVENT:  {start.name}  @ time {sim.clock}")

    current_activity = vehicle.conops.after(start)  # <- this gets the activity which comes after

    print(f"  VEHICLE {vehicle.name} > Begin ACTIVITY:  {current_activity.name}")

    # Update the Vehicle
    vehicle.activity = current_activity
    vehicle.propload -= 1
    vehicle.update_trace(sim.clock)

    # In our approach, activity.start has already occurred.
    # So we must schedule the ending event, along with the the activity which will wait on that event

    if isinstance(current_activity.end, Completor):
        current_end = CompletionEvent(
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
        next_activity = vehicle.conops.after(current_end)
        next_start    = current_end

        sim.tasks.append(
            asyncio.create_task(
                activity_handler(next_activity.name, next_start, sim, vehicle)
            )
        )

    sim.queue_future.put_nowait(next_start)


async def fly_mission(sim: Simulator):

    # -----------------------------------------------------------------------------------------------------------------
    # Mission Definition
    # - Events
    INIT    = Event("INIT")
    liftoff = Event("Liftoff")
    stage   = Event("Stage")
    burnout = Event("Burnout")
    DONE    = Completor("TERM")

    # - ConOps
    conops = ConOps({
        INIT.name:    Activity("Countdown", INIT, liftoff, 3),
        liftoff.name: Activity("Ascent S1", liftoff, stage, 10),
        stage.name:   Activity("Ascent S2", stage, burnout, 10),
        burnout.name: Activity("Insertion", burnout, DONE, 2)
    })

    v1 = Vehicle("Booster-01", conops, 100)
    v2 = Vehicle("Booster-02", conops, 100)

    # Execute the simulation based on the initilized vehicles
    await sim.run([
        (v1, 0.0),
        (v2, 25.0),
    ])


#######################################################################################################################
# Demo
#######################################################################################################################

if __name__ == "__main__":

    sim = Simulator()

    print("\n***********\n***BEGIN***\n")

    asyncio.run(fly_mission(sim))

    print("\n***DONE****\n***********")