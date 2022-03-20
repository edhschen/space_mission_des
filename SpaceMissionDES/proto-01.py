
# Standard Library
from dataclasses import dataclass, field
from heapq import heappush, heappop
from pprint import pprint # pretty-printing basic data structures

# Dependencies
import pandas as pd

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
# Event Template

@dataclass
class Event:
    """Object used to template events in a mission ConOps"""
    name: str

#######################################################################################################################
# Activities

@dataclass
class Activity:
    name: str
    start: Event
    end: Event
    duration: float

#######################################################################################################################
# Vehicles

@dataclass
class Vehicle:
    name: str
    activity: Activity
    propload: float
    trace: pd.DataFrame = pd.DataFrame(columns=['CurrentEvent', 'NextEvent', 'Prop', 'Activity'])

    def __repr__(self):
        return (f'{self.__class__.__name__} - {self.name}')

    @staticmethod
    def initialize(name, conops, propload = 100):
        v = Vehicle(name, conops.first(), propload)
        v.update_trace()
        return v

    def schedule_next_event(self, future_event_list):
        template = self.activity.end
        name = self.activity.end.name
        heappush(
            future_event_list.events,
            ScheduledEvent(name, template, self, now() + self.activity.duration)
        )

    def update_trace(self):
        self.trace = pd.concat([
            self.trace,
            pd.DataFrame({
                "CurrentEvent": self.activity.start, 
                "NextEvent": self.activity.end, 
                "Prop": self.propload, 
                "Activity": self.activity}, index = [len(self.trace) + 1])
        ])

#######################################################################################################################
# Future Events

@dataclass(order=True)
class ScheduledEvent:
    name: str=field(compare=False)
    template: Event=field(compare=False)
    vehicle: Vehicle=field(compare=False)
    time: float

# Implement the FutureEventList from Prof. Vuduc's example
class FutureEventList:
    def __init__(self):
        self.events = []
        
    def __iter__(self):
        return self
    
    def __next__(self) -> Event:
        from heapq import heappop
        if self.events:
            return heappop(self.events)
        raise StopIteration

    def __repr__(self) -> str:
        from pprint import pformat
        return pformat(self.events)

    def get_next(self):
        return heappop(self.events)

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
# Demo
#######################################################################################################################

if __name__ == "__main__":

    # -----------------------------------------------------------------------------------------------------------------
    # Mission Definition
    # - Events
    INIT = Event("INIT")
    liftoff = Event("Liftoff")
    stage = Event("Stage")
    orbit = Event("Orbit")

    DONE = Event("Done")

    # - Activities
    activities = {
        INIT.name: Activity("waiting", INIT, liftoff, 0),
        liftoff.name: Activity("s1_ascent", liftoff, stage, 10),
        stage.name: Activity("s2_ascent", stage, orbit, 10),
        orbit.name: Activity("insertion", orbit, DONE, 5)
    }

    conops = ConOps(activities)

    # -----------------------------------------------------------------------------------------------------------------
    # Initialization
    # - Set up the system state
    system_state = {
        activity.name: [] for activity in conops.sequence.values()
    }

    # - Reset the clock
    set_time(0)

    # - Create and empty events list
    future = FutureEventList()

    # - Start a vehicle
    current_vehicle = Vehicle.initialize("LV1", conops)

    # - Schedule the first event expected for the vehicle
    current_vehicle.schedule_next_event(future)

    # Add the vehicle to the empty system state
    system_state[current_vehicle.activity.name].append(current_vehicle)
    # system_state  # update the system state trace here

    # -----------------------------------------------------------------------------------------------------------------
    # Simulation Loop
    print("\n\n********************\n* BEGIN SIMULATION *\n********************\n")

    for event in future:

        # Update the simulation clock
        set_time(event.time)

        if event.template is DONE:
            system_state[event.vehicle.activity.name].remove(vehicle)
            print(f"Time is {now()}")
            print("\n******************\n* END SIMULATION *\n******************")
            break

        # Transfer control to the vehicle process
        vehicle = event.vehicle

        # Process the event

        # - Update the vehicle state
        vehicle.propload -= 60  #TODO: Add proper logic for propellant updates

        # Get the next activity & update the vehilce
        previous_activity = vehicle.activity
        vehicle.activity = conops.after(event)

        # - Update the vehicle trace
        vehicle.update_trace()

        print(f"Time is {now()}")
        print(f"\tThe previous activity was {previous_activity.name}")
        print(f"\tThe current event is {event.name}")
        print(f"\tThe next activity is {vehicle.activity.name}\n")

        # Update the system state
        system_state[previous_activity.name].remove(vehicle)
        system_state[vehicle.activity.name].append(vehicle)

        # Schedule the next event
        vehicle.schedule_next_event(future)

        # Return control to the scheduler

    # -----------------------------------------------------------------------------------------------------------------
    # Post-sim Report
    print("\nVehicle Trace:")
    print(vehicle.trace)

    print("\nSystem State:")
    print(system_state)