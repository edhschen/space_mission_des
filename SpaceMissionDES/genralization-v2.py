# %%
from dataclasses import dataclass, field
from heapq import heappush, heappop
from pprint import pprint # pretty-printing basic data structures
import random

import pandas as pd

# %% [markdown]
# Clock

# %%
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

print("The current simulation time is", now(), "o'clock.")

# %% [markdown]
# Events

# %%
@dataclass
class Event:
    name: str

# %% [markdown]
# Activities

# %%
@dataclass
class Activity:
    name: str
    start: Event
    end: Event
    duration: float
    dependency: dict = field(default_factory=dict)
    resource_change: dict = field(default_factory=dict)
    success_rate: float = 1.0

# waiting = Activity("waiting", INIT, liftoff, 0)
# s1_ascent = Activity("s1_ascent", liftoff, separation, 5)
# s2_ascent = Activity("s2_ascent", separation, orbit, 5)

# %% [markdown]
# Vehicles

# %%
@dataclass
class Object:
    name: str
    activity: Activity
    resource: dict
    children: list
    trace: pd.DataFrame = pd.DataFrame(columns=['CurrentEvent', 'NextEvent', 'Resource', 'Activity'])

    def __repr__(self):
        return (f'{self.__class__.__name__} - {self.name}')

    @staticmethod
    def initialize(name, activity, resource = {}, children = []):
        v = Object(name, activity, resource, children)
        for child in children:
            for resource_type, amnt in child.resource.items():
                if resource_type in v.resource:
                    v.resource[resource_type] += amnt
                else:
                    v.resource[resource_type] = amnt
        v.update_trace()
        return v

    def process_event(self, global_trace):
        dependencies = self.activity.dependency
        resource_change = self.activity.resource_change
        # dependency is a dict of events that need to be completed before this event
        # for instance, dependency = {"tank_1": {"tank_ejection": ["strict"]}, "tank_2: {"tank_ejection": ["strict"]}, {"vehicle": {"positioning": ["moderate", {"propellant": -10}]}}
        # ideas for other severities are "modifiable", ie positioning unsuccessful, event can proceed but will take more resource

        # resource_consumption is a dict of resources that will be changed during an event, can be positive or negative
        # for instance, resource_change = {"propellant": -50}

        for dependency, severity in dependencies.items():
            if dependency not in [a.name for a in global_trace.loc[:,"Activity"]]:
                if severity[0] == "strict":
                    raise Exception(f"Strict dependency {dependency} not satisfied, something failed")
                    break
                # temporary, need to find a standardizable syntax
                elif severity[0] == "moderate":
                    for resource, value in severity[1].items():
                        try:
                            resource_change[resource] += value
                        except:
                            resource_change[resource] = value


        for resource, value in resource_change.items():
            try:
                self.resource[resource] += value
                if self.resource[resource] <= 0:
                    raise Exception(f"Ran out of {resource} during {self.activity.name}")
                    break
            except:
                raise Exception(f"Tried to modify a resource which does not exist, {resource}")
                break

        if random.random() > self.activity.success_rate:
            print(f"Oops, {self.activity.name} did not go according to plan")
            # does not raise an exception since not all events are process-ending
            return "Failed"
        else:
            return "Success"


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
                "Resource": self.resource,
                "Activity": self.activity}, index = [len(self.trace) + 1])
        ])

# %% [markdown]
# Future Events

# %%
@dataclass(order=True)
class ScheduledEvent:
    name: str=field(compare=False)
    template: Event=field(compare=False)
    object: Object=field(compare=False)
    time: float

# %%
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

# %% [markdown]
# ConOps

# %%
@dataclass
class ConOps:
    sequence: dict

    def first(self):
        return self.sequence["INIT"]

    def after(self, current_event):
        # Get the activity which starts with a particular event
        return self.sequence[current_event.name]

# %% [markdown]
# ### Process Example 02

# %% [markdown]
# First define the ConOps as a sequence of processes

# %%
# Events
INIT = Event("INIT")
liftoff = Event("Liftoff")
tank_usage = Event("Tank Usage")
stage = Event("Stage")
tank_dropped = Event("Tank Dropped")
orbit = Event("Orbit")
DONE = Event("Done")

# Activities
# setting the probabilities really low to test things
vehicle_activities = {
    INIT.name: Activity("waiting", INIT, liftoff, duration=0),
    liftoff.name: Activity("s1_ascent", liftoff, stage, duration=10, dependency = {"tank1": {"tank_usage": "strict"}}, resource_change = {"propellant": "40"}, success_rate=0.8),
    stage.name: Activity("s2_ascent", stage, orbit, duration=10, dependency = {"tank2": {"tank_usage": "strict"}}, resource_change = {"propellant": "20"}, success_rate=0.8),
    orbit.name: Activity("insertion", orbit, DONE, duration=5, dependency = {"tank1": {"tank_dropped": "strict"}, "tank2": {"tank_dropped": "strict"}},resource_change = {"propellant": "10"}, success_rate=0.8)
}
# need to think of some failure event handlers, ie "insertion" can probably be retried, whereas "s2_ascent" cannot
# for sake of simplicity a retry should probably just have the same resource change
# sorta think it would be better if we had one master activity list, separating the conops may get a bit messy

# can we make this so it is easily duplicated across multiple objects
tank_activities = {
    INIT.name: Activity("waiting", INIT, liftoff, duration=0),
    tank_usage.name: Activity("tank_usage", tank_usage, tank_dropped, duration = 8, resource_change={"propellant": "35"}, success_rate=0.8),
    tank_dropped.name: Activity("tank_dropped", tank_dropped, DONE, duration = 8, resource_change={}, success_rate=0.8)
}

conops_vehicle = ConOps(vehicle_activities)
conops_tank1 = ConOps(tank_activities)
conops_tank2 = ConOps(tank_activities)

system_state = {
    activity.name: [] for activity in conops_vehicle.sequence.values()
}

# %% [markdown]
# Initialize the Simulation

# %%
# Reset the clock
set_time(0)

# Create and empty events list
future = FutureEventList()

# Start a vehicle
# children and resource have default empty values, have just declared them here to reduce confusion
tank_1 = Object.initialize("tank1", conops_tank1.first(), resource={"propellant": 50}, children=[])
tank_2 = Object.initialize("tank2", conops_tank2.first(), resource={"propellant": 50}, children=[])
current_vehicle = Object.initialize("LV1", conops_vehicle.first(), resource={"propellant": 100}, children=[tank_1, tank_2])

# Vehicle starts in some activity, which will end when that activities event is processed
current_vehicle.schedule_next_event(future)

system_state[current_vehicle.activity.name].append(current_vehicle)

system_state  # update the system state trace here

# %% [markdown]
# Loop over events

# %%
# not currently accounting for child object processing, in progress
print("\n\n********************\n* BEGIN SIMULATION *\n********************\n")

for event in future:

    # Update the simulation clock
    set_time(event.time)

    if event.template is DONE:
        # system_state[event.object.activity.name].remove(vehicle)
        print(f"Time is {now()}")
        print("\n******************\n* END SIMULATION *\n******************")
        break

    # Transfer control to the vehicle process
    vehicle = event.object

    # Get the next activity & update the vehicle
    previous_activity = vehicle.activity
    vehicle.activity = conops_vehicle.after(event)

    # - Update the vehicle trace
    vehicle.update_trace()

    print(f"Time is {now()}")
    print(f"\tThe previous activity was {previous_activity.name}")
    print(f"\tThe current event is {event.name}")
    print(f"\tThe next activity is {vehicle.activity.name}\n")

    # Update the system state
    # print(system_state[previous_activity.name])
    system_state[previous_activity.name].remove(vehicle)
    system_state[vehicle.activity.name].append(vehicle)

    # Schedule the next event
    vehicle.schedule_next_event(future)

    # Return control to the scheduler

# %%
vehicle.trace

# %%
system_state

# %%
[a.name for a in vehicle.trace.loc[:,"Activity"]]
