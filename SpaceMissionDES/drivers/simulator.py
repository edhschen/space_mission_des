# simulator.py

from dataclasses import dataclass, field
import asyncio
import random
import logging
import pandas as pd
from collections import Counter

from objects.events import *
from objects.vehicles import Vehicle
from objects.activities import *


def new_future_queue():
    """Create a new event loop and Queue for each simulator instance, needed for Monte Carlo"""
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

    async def process_events(self):
        for event in self.future:
            
            # Update the Clock and do any vehicle state updates
            self.clock = event.time
            event.state_update()  # fuction called which was defined in the activity_handler
            
            # trigger the event
            event.set()
            
            # Get the next event -- we use await here to pass control back and forth between the main scheduler and the activity handlers
            new_event = await self.queue_future.get()

            # Handle each type of event
            if isinstance(new_event, FailureEvent):                             # Failure events lead to canceling the sim outright
                logging.info(f"\tFAILURE @ time {new_event.time}")
                self.cancel_tasks()
                # Cleanup
                for excess_event in self.future:
                    excess_event.set()

                return # Exit the process_events loop immediately
            
            elif isinstance(new_event, CompletionEvent):                        # Completion events conclude a ConOps and DO NOT schedule new events
                logging.info(f"\tTERMINAL EVENT named {new_event.name} @ time {new_event.time}")

            elif new_event.predicate != None:                                   # Predicate events are added to predicates, not scheduled until satisfied
                self.predicates.append(new_event)
            
            else:
                self.schedule(new_event)

            # ----------------------------------------------
            # Sim state has been updated -- CHECK PREDICATES
            for p in self.predicates:
                try:
                    if p.predicate.check(p, self):  # calls unqiue functions to check predicate -> bool
                        # Shedule the event to occur immediately
                        p.time = self.clock
                        self.schedule(p)
                        # Remove the predicate so it wont be activated twice
                        self.predicates.remove(p)
                except AttributeError:
                    continue

            # testing alternative approach
            # for vehicle, predicate in self.predicates.items():
            #     if predicate.activity in [a.name for a in vehicle.trace.loc[:, "Activity"]]:
            #         predicate.time = self.clock
            #         self.schedule(predicate)
            #         self.predicates.remove(predicate)
                    

        # Only log success if all predicates have been satisfied
        if len(self.predicates) == 0:
            logging.info("\nCOMPLETE\n")
            self.success = True
        else:
            logging.warn(f"\nINcomplete predicates: {[p.predicate.name for p in self.predicates]}\n")

    def schedule(self, event: ScheduledEvent):
        heappush(self.future.events, event)

    def add_activity(self, name: str, start: ScheduledEvent, vehicle: Vehicle):
        self.tasks.append(
            asyncio.create_task(
                activity_handler(name, start, self, vehicle),
                name = f"Vehicle: {vehicle.name} | INIT"
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
            asyncio.create_task(self.process_events(), name="process_event")
        )
        
        await asyncio.gather(*self.tasks)

    def log_failure(self, time, vehicle, activity):
        self.failures = pd.concat([
            self.failures,
            pd.DataFrame({"Time":time, "Vehicle": vehicle, "Activity": activity}, index = [len(self.failures) + 1])
        ])

    def cancel_tasks(self):
        for task in self.tasks:
            if task.get_name() != 'process_event' and not task.done():
                logging.debug(f'CANCEL -> {task}')
                task.cancel()

    def __repr__(self) -> str:

        sim_text  = f"{self.__class__.__name__}\n"
        sim_text += f"\ttime = {self.clock}\n"
        sim_text += f"\tVehicles\n"
        for vehicle in self.entities.values():
            sim_text += "\t - " + str(vehicle.name) + "\n"

        return (sim_text)


async def activity_handler(name: str, start: ScheduledEvent, sim: Simulator, vehicle: Vehicle):

    # An activity begins when the start event has been scheduled AND picked off the future event list
    await start.wait()
    logging.info(f"\n\tEVENT:  {start.name}  @ time {sim.clock:.2f}")

    # Activty is handling is used at the beginning of an event
    current_activity = vehicle.conops.after(start)  # <- this gets the activity which comes after
    logging.info(f"\t  VEHICLE {vehicle.name} > Begin ACTIVITY:  {current_activity.name}")

    # ---------------------------------------------------------------------------------------------
    # Test Activity Success
    current_end = check_activity_failure(current_activity, vehicle, sim)

    # Change the end if there is a branching function
    if isinstance(current_end, Branch):
        current_end = current_end.logic(sim, vehicle)

    # ---------------------------------------------------------------------------------------------
    # Update the Vehicle
    vehicle.activity = current_activity
    # print(vehicle.resource)
    vehicle.resource = Counter(vehicle.resource) - Counter(current_activity.resource_change)
    if any(value == 0 for value in vehicle.resource.values()):
        raise Exception(f"Vehicle {vehicle.name} ran out of a tracked resource or is trying to deplete a resource that does not exist")
    # Define State variable updator which is only called when the event succeeds and the end event is triggered
    state_update = lambda: vehicle.update_state(current_activity.update)

    # In our approach, activity.start has already occurred.
    # So we must schedule the ending event, along with the the activity which will wait on that event

    # print(f"Hellooo {current_end}  on {current_activity.name}")
    if not isinstance(current_end, Failure):
        if current_activity.agg_type == "join":
            # print(f"WHAT {current_activity.agg_params['vehicles']}")
            logging.info(f"\t  VEHICLES {current_activity.agg_params['vehicles']} > Begin ACTIVITY:  {current_activity.name}")
            logging.info(f"\t  VEHICLES {current_activity.agg_params['vehicles']} > JOINED TO:  {current_activity.agg_params['name']}")
            # print(current_activity.agg_params['vehicles'])
            if len(current_activity.agg_params['vehicles']) < 2:
                raise Exception("Not enough arguments provided for object collation")
            resources_agg = Counter({})
            for vc in current_activity.agg_params['vehicles']:
                # print(sim.entities)
                # print(sim.entities[vc].name)
                resources_agg += Counter(sim.entities[vc].resource)

            # if not name:
            #     name = ""
            #     for vc in current_activity.agg_params['vehicles']:
            #         name += sim.entities[vc].name + "/"
            
            # print(current_activity.agg_params['conops'])
            parent_vc = Vehicle(current_activity.agg_params['name'], current_activity.agg_params['conops'], dict(resources_agg), children = current_activity.agg_params['vehicles'][:])

            for vc in current_activity.agg_params['vehicles']:
                # print(f"Currently checking {vc}")
                # print(sim.entities[vc].parent)
                sim.entities[vc].parent = current_activity.agg_params['name']
            
            sim.add_vehicle(parent_vc, sim.clock + current_activity.duration)

        if current_activity.agg_type == "dejoin":
            logging.info(f"\t  VEHICLES {vehicle.name} > decoupled CHILDREN:  {vehicle.children}")
            for child in vehicle.children:
                sim.entities[child].parent = None
            vehicle.children = []

        if current_activity.agg_type == "dropchild":
            for vc in current_activity.agg_params['vehicles']:
                try:
                    sim.entities[vc].parent = None
                    vehicle.children.remove(vc)
                except:
                    raise Exception(f"Child entity {vc} does not exist")

        if current_activity.agg_type == "addchild":
            vehicle.children.append(current_activity.agg_params['vehicles'][:])
            for vc in current_activity.agg_params['vehicles']:
                sim.entities[vc].parent = vehicle.name
    
    if isinstance(current_end, Failure):
        next_event = FailureEvent(
            current_activity.failure.name,
            current_activity.failure,
            sim.clock
        )
    
    elif isinstance(current_end, Completor):
        next_event = CompletionEvent(
            current_end.name,
            current_end,
            sim.clock + current_activity.duration + sample(current_activity.delay),
            state_update=state_update
        )
        # Update the vehicle to indicate the ConOps has compelted
        vehicle.completed_conops = True

    else:
        next_activity = vehicle.conops.after(current_end)
        
        if isinstance(current_activity, PredicatedActivity):
            # Create the event, but don't schedule it
            next_event = ScheduledEvent(
                next_activity.start.name,
                next_activity.start,
                predicate = current_activity.predicate,
                state_update=state_update
            )
        else:
            next_event = ScheduledEvent(
                next_activity.start.name,
                next_activity.start,
                sim.clock + current_activity.duration + sample(current_activity.delay),
                state_update=state_update
            )

        # Schedule the next activity, which will be waiting and started by the current end event
        sim.tasks.append(
            asyncio.create_task(
                activity_handler(next_activity.name, next_event, sim, vehicle),
                name = f"Vehicle: {vehicle.name} | Activity: {vehicle.activity.name}"
            )
        )

    # ---------------------------------------------------------------------------------------------
    # Return control to the simulation driver by placing an event on the future queue
    vehicle.update_trace(sim.clock)
    sim.queue_future.put_nowait(next_event)


def check_activity_failure(activity, vehicle, sim):
    multievent = type(vehicle) == list
    # Perform a bernoulli trial
    trial = random.random()
    if trial > (1 - activity.p_fail):
        if multievent:
            name = ""
            for v in vehicle:
                name += v.name + "/"
        logging.warning(f"  FAIL -- VEHICLE {vehicle.name} failed ACTIVITY:  {activity.name}")
        
        if not multievent:
            # Log failure to sim -- Vehicle X failed on activity Y at time Z
            sim.log_failure(sim.clock, vehicle.name, activity.name)
            # Handle the failure, update failure states
            vehicle.handle_failure()
        else:
            for v in vehicle:
                sim.log_failure(sim.clock, v.name, activity.name)
                v.handle_failure()
        
        outcome = activity.failure
    else:
        outcome = activity.end

    return outcome
