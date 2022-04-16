# simulator.py

from dataclasses import dataclass, field
import asyncio
import random
import logging
import pandas as pd

from objects.events import *
from objects.vehicles import Vehicle


def new_future_queue():
    new_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(new_loop)
    return asyncio.Queue()

@dataclass
class Simulator:
    entities: dict = field(default_factory = lambda: {})  
    # no default, we cannot start a sim without entities ?
    failures: pd.DataFrame = pd.DataFrame(columns=["Time", "Vehicle", "Activity"])
    future: FutureEventList = FutureEventList()
    tasks: list = field(default_factory = lambda: [])
    predicates: list = field(default_factory = lambda: [])
    clock: float = 0.0
    success: bool = False
    queue_future: asyncio.Queue = field(default_factory = new_future_queue)

    # def __post_init__(self):
    #     new_loop = asyncio.new_event_loop()
    #     asyncio.set_event_loop(new_loop)
        

    def __repr__(self) -> str:

        sim_text  = f"{self.__class__.__name__}\n"
        sim_text += f"\ttime = {self.clock}\n"
        sim_text += f"\tVehicles\n"
        for vehicle in self.entities.values():
            sim_text += "\t - " + str(vehicle.name) + "\n"

        return (sim_text)

    async def process_events(self):
        for event in self.future:
            # update the time
            # await asyncio.sleep(0.2)
            self.clock = event.time
            
            # trigger the event
            event.set()
            
            # await sim_continue.wait()
            new_event = await self.queue_future.get()

            if isinstance(new_event, FailureEvent):
                logging.info(f"\tFAILURE @ time {new_event.time}")
                self.cancel_tasks()
                return
            
            elif isinstance(new_event, CompletionEvent):
                logging.info(f"\tTERMINAL EVENT @ time {new_event.time}")
            
            else:
                self.schedule(new_event)

        logging.info("\nCOMPLETE\n")
        self.success = True


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

    def log_failure(self, time, vehicle, activity):
        self.failures = pd.concat([
            self.failures,
            pd.DataFrame({"Time":time, "Vehicle": vehicle, "Activity": activity}, index = [len(self.failures) + 1])
        ])

    def cancel_tasks(self):
        for task in self.tasks:
            logging.debug(task)
            logging.debug('cancelling task')
            task.cancel()

# async def activity_handler(name: str, start: ScheduledEvent, end: ScheduledEvent, sim):
async def activity_handler(name: str, start: ScheduledEvent, sim: Simulator, vehicle: Vehicle):

    await start.wait()
    logging.info(f"\n\tEVENT:  {start.name}  @ time {sim.clock}")

    current_activity = vehicle.conops.after(start)  # <- this gets the activity which comes after

    logging.info(f"\t  VEHICLE {vehicle.name} > Begin ACTIVITY:  {current_activity.name}")

    # ---------------------------------------------------------------------------------------------
    # Test Activity Success

    # Look up activity probabililty
    p_fail_activity = current_activity.p_fail
    # p_fail_activity = 1/5  # = 0.8

    # Perform a bernoulli trial
    trial = random.random()
    if trial > (1 - p_fail_activity):
        logging.warning(f"  FAIL -- VEHICLE {vehicle.name} failed ACTIVITY:  {current_activity.name}")
        
        # Log failure to sim -- Vehicle X failed on activity Y at time Z
        sim.log_failure(sim.clock, vehicle.name, current_activity.name)
        # Handle the failure, update failure states
        vehicle.handle_failure()
        
        current_end = current_activity.failure
    else:
        current_end = current_activity.end

    # Get the event which successfuly ends the activity
    # current_end = current_activity.end

    # ---------------------------------------------------------------------------------------------
    # Update the Vehicle -- ONLY if the event activity is succesful
    vehicle.activity = current_activity
    vehicle.propload -= 1
    

    # In our approach, activity.start has already occurred.
    # So we must schedule the ending event, along with the the activity which will wait on that event
    
    if isinstance(current_end, Failure):
        next_event = FailureEvent(
            current_activity.failure.name,
            current_activity.failure,
            sim.clock
        )
        # Upd
    
    elif isinstance(current_end, Completor):
        next_event = CompletionEvent(
            current_activity.end.name,
            current_activity.end,
            sim.clock + current_activity.duration
        )
        # Update the vehicle to indicate the ConOps has compelted
        vehicle.completed_conops = True
    
    else:
        next_activity = vehicle.conops.after(current_end)
        
        next_event = ScheduledEvent(
            next_activity.start.name,
            next_activity.start,
            sim.clock + current_activity.duration
        )

        # Schedule the next activity, which will be waiting and started by the current end event

        sim.tasks.append(
            asyncio.create_task(
                activity_handler(next_activity.name, next_event, sim, vehicle)
            )
        )

    # ---------------------------------------------------------------------------------------------
    # Return control to the simulation driver by placing an event on the future queue
    vehicle.update_trace(sim.clock)
    sim.queue_future.put_nowait(next_event)