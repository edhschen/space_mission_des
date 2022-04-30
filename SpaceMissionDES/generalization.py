# %%
from dataclasses import dataclass, field
from heapq import heappush, heappop
from pprint import pprint # pretty-printing basic data structures

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

# print("The current simulation time is", now(), "o'clock.")

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
    children: dict
    trace: pd.DataFrame = pd.DataFrame(columns=['CurrentEvent', 'NextEvent', 'Resource', 'Activity'])

    def __repr__(self):
        return (f'{self.__class__.__name__} - {self.name}')

    @staticmethod
    def initialize(name, conops, resource):
        v = Object(name, conops.first(), resource)
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
# ### Process Example 01

# %% [markdown]
# First define the ConOps as a sequence of processes

# %%
# Events
INIT = Event("INIT")
liftoff = Event("Liftoff")
stage = Event("Stage")
orbit = Event("Orbit")

# Activities
activities = {
    INIT.name: Activity("waiting", INIT, liftoff, 0),
    liftoff.name: Activity("s1_ascent", liftoff, stage, 10),
    stage.name: Activity("s2_ascent", stage, orbit, 10)
}

conops = ConOps(activities)

# %% [markdown]
# Initialize the Simulation

# %%
# Reset the clock
set_time(0)

# Create and empty events list
future = FutureEventList()

# Start a vehicle
current_vehicle = Object.initialize("LV1", conops)

# Vehicle starts in some activity, which will end when that activities event is processed
current_vehicle.schedule_next_event(future)

# %% [markdown]
# Walk the events

# %%
# Trigger the ending event
current_event = future.get_next()

# Process the event
# - Update the system state
# - Update the vehicle state
# v.propload -= 60  # some fancy code to handle this

# Get the next activity
next_activity = conops.after(current_event)

print(f"The current activity is {current_vehicle.activity}")
print(f"The current event is {current_event}")
print(f"The next activity is {next_activity}")

# - Change the activity
current_vehicle.activity = next_activity

# Schedule the next event
current_vehicle.schedule_next_event(future)

assert current_event.template == next_activity.start

# - Update the vehicle trace
current_vehicle.update_trace()

current_vehicle.trace

# %% [markdown]
# ### Process Example 02

# %% [markdown]
# First define the ConOps as a sequence of processes

# %%
# Events
INIT = Event("INIT")
liftoff = Event("Liftoff")
stage = Event("Stage")
orbit = Event("Orbit")

DONE = Event("Done")

# Activities
activities = {
    INIT.name: Activity("waiting", INIT, liftoff, 0),
    liftoff.name: Activity("s1_ascent", liftoff, stage, 10),
    stage.name: Activity("s2_ascent", stage, orbit, 10),
    orbit.name: Activity("insertion", orbit, DONE, 5)
}

conops = ConOps(activities)

system_state = {
    activity.name: [] for activity in conops.sequence.values()
}

# %% [markdown]
# Initialize the Simulation

# %%
# Reset the clock
set_time(0)

# Create and empty events list
future = FutureEventList()

# Start a vehicle
current_vehicle = Object.initialize("LV1", conops)

# Vehicle starts in some activity, which will end when that activities event is processed
current_vehicle.schedule_next_event(future)

system_state[current_vehicle.activity.name].append(current_vehicle)

system_state  # update the system state trace here

# %% [markdown]
# Loop over events

# %%
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

# %%
vehicle.trace

# %%
system_state

# %%
