# simulator.py

import asyncio
from dataclasses import dataclass, field

from objects.events import *
from objects.vehicles import Vehicle


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

        for start_time, vehicle in initial_vehicles:
            self.add_vehicle(vehicle, start_time)
        
        self.tasks.append(
            asyncio.create_task(self.process_events())
        )
        
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
        next_activity = vehicle.conops.after(current_end)
        next_start    = current_end

        sim.tasks.append(
            asyncio.create_task(
                activity_handler(next_activity.name, next_start, sim, vehicle)
            )
        )

    sim.queue_future.put_nowait(next_start)